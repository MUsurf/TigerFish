#include <opencv2/opencv.hpp>
#include "process_images/gate_detection.hpp"
#include <iostream>
#include <algorithm>
#include <random>
#include <cmath>

// --- Human HSV (H:0-360 deg, S/V:0-100%) -> OpenCV HSV (H:0-179, S/V:0-255) ---
// Put this near the top of your file (needs <algorithm> for std::clamp)

// This is a helper that I am using to abstract away openCV's weird HSV scaling. which goes from 0-179 for H, 0-255 for S and V
// pluging it in like this allows us to visualize the color space with commonly available color pickers.
cv::Scalar Gate_detection::hsvToOpenCV(float h_deg, float s_pct, float v_pct)
{
    // Convert
  int h = static_cast<int>(h_deg / 2.0f);     // 0-360 -> 0-180 (OpenCV uses 0-179)
  int s = static_cast<int>(s_pct * 2.55f);    // 0-100 -> 0-255
  int v = static_cast<int>(v_pct * 2.55f);    // 0-100 -> 0-255

    // Clamp to OpenCV valid ranges
  h = std::clamp(h, 0, 179);
  s = std::clamp(s, 0, 255);
  v = std::clamp(v, 0, 255);

  return cv::Scalar(h, s, v);
}

// ===== RANSAC LINE FIT  =====
// Fits a single dominant line to a set of 2D points using RANSAC, then refines with cv::fitLine on inliers.
// Returns true if a line was found. Output is (vx, vy, x0, y0) in the same format as cv::fitLine.
// helper function to fit line
// Detect up to maxLines line models from a point cloud using iterative RANSAC,
// removing inliers after each detection (multi-line extraction).
std::vector<cv::Vec4f> Gate_detection::ransacDetectLines(
  std::vector<cv::Point2f> points,     // pass by value on purpose (we mutate / shrink it)
  int maxLines,
  int iterations,
  float inlierThresholdPx,
  float minInlierRatio,
  int minInliersFloor
)
{
  std::vector<cv::Vec4f> linesOut;
  if (points.size() < 2) {return linesOut;}

        // Deterministic RNG (same as your original). Change seed if you want randomness.
  static std::mt19937 rng(12345);

  for (int k = 0; k < maxLines; ++k) {
    if (points.size() < 2) {break;}

    const int minInliers = std::max(minInliersFloor,
    static_cast<int>(points.size() * minInlierRatio));

            // --- Single-line RANSAC fit (inlined) ---
    std::vector<int> bestInliers;
    bestInliers.reserve(points.size());

    int bestInlierCount = 0;
    cv::Vec4f bestModel(0, 0, 0, 0);

    std::uniform_int_distribution<int> dist(0, static_cast<int>(points.size() - 1));

    for (int it = 0; it < iterations; ++it) {
      const int i1 = dist(rng);
      const int i2 = dist(rng);
      if (i1 == i2) {continue;}

      const cv::Point2f & p1 = points[i1];
      const cv::Point2f & p2 = points[i2];

                // direction = normalized (p2 - p1)
      cv::Point2f d = p2 - p1;
      const float len = std::sqrt(d.x * d.x + d.y * d.y);
      if (len < 1e-6f) {continue;}
      d.x /= len; d.y /= len;

                // collect inliers by point-to-line distance using 2D cross product magnitude
      std::vector<int> inliers;
      inliers.reserve(points.size());

      for (int i = 0; i < (int)points.size(); ++i) {
        const cv::Point2f a = points[i] - p1;
        const float cross = d.x * a.y - d.y * a.x;               // |d x a|
        const float distPx = std::fabs(cross);                   // d is unit-length

        if (distPx <= inlierThresholdPx) {
          inliers.push_back(i);
        }
      }

      if ((int)inliers.size() > bestInlierCount) {
        bestInlierCount = (int)inliers.size();
        bestInliers = std::move(inliers);
        bestModel = cv::Vec4f(d.x, d.y, p1.x, p1.y);             // (vx, vy, x0, y0)
      }
    }

            // If we can't get enough inliers, stop extracting more lines.
    if (bestInlierCount < minInliers) {break;}

            // Refine best model with least-squares fit on inliers
    std::vector<cv::Point2f> inlierPts;
    inlierPts.reserve(bestInliers.size());
    for (int idx : bestInliers) {
      inlierPts.push_back(points[idx]);
    }

    cv::Vec4f refined;
    cv::fitLine(inlierPts, refined, cv::DIST_L2, 0, 0.01, 0.01);

    linesOut.push_back(refined);

            // --- Remove inliers from the working set for multi-line detection ---
    std::vector<char> isInlier(points.size(), 0);
    for (int idx : bestInliers) {
      isInlier[idx] = 1;
    }

    std::vector<cv::Point2f> remaining;
    remaining.reserve(points.size() - bestInliers.size());
    for (size_t i = 0; i < points.size(); ++i) {
      if (!isInlier[i]) {remaining.push_back(points[i]);}}

    points.swap(remaining);

            // Optional early stop if too few points remain to form another strong line
    if (points.size() < (size_t)minInliersFloor) {break;}
  }

  return linesOut;
}

GateResult Gate_detection::find_gate(
  const cv::Mat & frame) // I don't think we need the lines input
{
  GateResult result;
  cv::Mat frameProc = frame.clone();

  // ===== RED MASK (HSV) =====
  cv::Mat hsv;
  cv::cvtColor(frameProc, hsv, cv::COLOR_BGR2HSV);

  cv::Mat maskRed1;
  cv::Mat maskRed2;
  cv::Mat colorMask;

  cv::inRange(
        hsv,
        Gate_detection::hsvToOpenCV(0.0f, 30.0f, 30.0f),
        Gate_detection::hsvToOpenCV(40.0f, 100.0f, 100.0f),
        maskRed1
  );

    // maskRed2: 315°..360°
  cv::inRange(
        hsv,
        Gate_detection::hsvToOpenCV(315.0f, 30.0f, 30.0f),
        Gate_detection::hsvToOpenCV(360.0f, 100.0f, 100.0f),
        maskRed2
  );
  cv::bitwise_or(maskRed1, maskRed2, colorMask);


  // morphological opening followed by closing to reduce noise and fill gaps in the mask
  // if it is removed, the mask will be much noisier, and the edges will be more fragmented, which will lead to worse line detection results.
  // the size of the kernel is 3x3, which is a common choice for morphological operations, as it is small enough to preserve details while still being effective at removing noise and filling gaps.
  cv::Mat kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3});
  cv::morphologyEx(colorMask, colorMask, cv::MORPH_OPEN, kernel);
  cv::morphologyEx(colorMask, colorMask, cv::MORPH_CLOSE, kernel);

  // ===== EDGES FROM RED CHANNEL (MONO) + MASK =====
  std::vector<cv::Mat> bgr;
  cv::split(frameProc, bgr);
  cv::Mat redMono = bgr[2];   // only the red channel (0..255)

  // Keep only red-region pixels in the red channel image
  cv::Mat redMaskedMono;
  cv::bitwise_and(redMono, redMono, redMaskedMono, colorMask);

  cv::Mat maskedEdges;
  cv::Canny(redMaskedMono, maskedEdges, 50, 150);

  cv::Mat maskEdge;
  cv::Mat k = cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3});
  cv::morphologyEx(colorMask, maskEdge, cv::MORPH_GRADIENT, k);

  cv::bitwise_and(maskedEdges, maskEdge, maskedEdges);   // keep only boundary-aligned edges

  // Non-zero points implementation
  // Collect non-zero pixels using OpenCV (much faster than manual scanning)
  std::vector<cv::Point> nonZeroPts;
  cv::findNonZero(maskedEdges, nonZeroPts);

  // Convert to Point2f for the RANSAC function
  std::vector<cv::Point2f> edgePoints;
  edgePoints.reserve(nonZeroPts.size());

  for (const auto & p : nonZeroPts) {
    edgePoints.emplace_back((float)p.x, (float)p.y);
  }

  cv::Mat visualizationCanvas = frameProc.clone();

  // Guard to ensure we have enough points for RANSAC. If not, just show the intermediate results and continue.
  if (edgePoints.size() < 2) {
    result.found = false;
    return result; // Not enough points to fit a line
  }

  std::vector<cv::Vec4f> ransacLines = Gate_detection::ransacDetectLines(edgePoints);
  result.lines = ransacLines;
  result.found = true;

  return result;
}

// Draw an infinite line (vx,vy,x0,y0) clipped to image bounds
void Gate_detection::drawFitLines(
  const std::vector<cv::Vec4f> & lines,
  cv::Mat & image,
  const cv::Scalar & color,
  int thickness
)
{
  for (const auto & line : lines) {
    float vx = line[0], vy = line[1], x0 = line[2], y0 = line[3];

    // Choose two far points along the line and clip by using a large scale
    float scale = 10000.0f;
    cv::Point2f p1(x0 - vx * scale, y0 - vy * scale);
    cv::Point2f p2(x0 + vx * scale, y0 + vy * scale);

    cv::line(image, p1, p2, color, thickness);
  }
}

void Gate_detection::visualize_lines(
  cv::Mat & display_frame,
  const GateResult & result)
{
  const auto & lines = result.lines;
  Gate_detection::drawFitLines(lines, display_frame, cv::Scalar(255, 0, 0), 3);
}
