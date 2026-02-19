#include <opencv2/opencv.hpp>
#include <iostream>
#include <algorithm>
#include <random> 

// NOTES: CURRENT IMPLEMENTATION APPLIES BOTH HOUGH LINE TRANSFORM AND RANSAC LINE FITTING. 
// THIS IS ONLY FOR THE PURPOSE OF TESTING SINCE HOUGH LINE DETECTION HAS YIELDED BETTER RESULTS UP TILL NOW
// THE OBJECTIVE IS TO GET RANSAC DETECTION TO WORK 

// TODO: Mask color range needs to be fine tuned, currently even my skin is getting detected as red, which is not ideal.
// TODO: The ransac implementation still needs to be worked on, this can be an issue with either the ransac implementation itself or the tuning. must ask DIP people about this
// TODO: Another source of error is the Canny edge detection, which is currently set to 100/200, but may need to be tuned for better results.
// TODO: Cleanup of gausean blur operations. There may be some extra gausean operations being applied which are bluring the image.
// TODO: A big portion of tuning this image recognition software will involve letting the testing team play with the parameters and find good values for them, 
// so we should make sure to expose all the relevant parameters in an easy to change way. We should make a UI with trackbars for this at some point.

static void drawHoughLines(const std::vector<cv::Vec4i>& lines, cv::Mat& image) {
    for (const auto& l : lines) {
        cv::line(
            image,
            cv::Point(l[0], l[1]),
            cv::Point(l[2], l[3]),
            cv::Scalar(0, 255, 0),
            2
        );
    }
}

// --- Human HSV (H:0-360 deg, S/V:0-100%) -> OpenCV HSV (H:0-179, S/V:0-255) ---
// Put this near the top of your file (needs <algorithm> for std::clamp)

// This is a helper that I am using to abstract away openCV's weird HSV scaling. which goes from 0-179 for H, 0-255 for S and V
// pluging it in like this allows us to visualize the color space with commonly available color pickers.
static cv::Scalar hsvToOpenCV(float h_deg, float s_pct, float v_pct)
{
    // Convert
    int h = static_cast<int>(h_deg / 2.0f);   // 0-360 -> 0-180 (OpenCV uses 0-179)
    int s = static_cast<int>(s_pct * 2.55f);  // 0-100 -> 0-255
    int v = static_cast<int>(v_pct * 2.55f);  // 0-100 -> 0-255

    // Clamp to OpenCV valid ranges
    h = std::clamp(h, 0, 179);
    s = std::clamp(s, 0, 255);
    v = std::clamp(v, 0, 255);

    return cv::Scalar(h, s, v);
}

// ===== RANSAC LINE FIT  =====
// Fits a single dominant line to a set of 2D points using RANSAC, then refines with cv::fitLine on inliers.
// Returns true if a line was found. Output is (vx, vy, x0, y0) in the same format as cv::fitLine.
static bool ransacFitLine(
    const std::vector<cv::Point2f>& points,
    cv::Vec4f& outLine,
    std::vector<int>& outInlierIdx,
    int iterations = 200,
    float inlierThresholdPx = 2.0f,
    int minInliers = 50
)
{
    outInlierIdx.clear();

    if (points.size() < 2) return false;

    // Random sampler
    //std::mt19937 rng(static_cast<unsigned>(cv::getTickCount()));
    static std::mt19937 rng(12345);
    std::uniform_int_distribution<int> dist(0, static_cast<int>(points.size() - 1));

    int bestInlierCount = 0;
    cv::Vec4f bestModel(0, 0, 0, 0);
    std::vector<int> bestInliers;

    for (int it = 0; it < iterations; ++it) {
        int i1 = dist(rng);
        int i2 = dist(rng);
        if (i1 == i2) continue;

        const cv::Point2f& p1 = points[i1];
        const cv::Point2f& p2 = points[i2];

        // Build a line model from two points:
        // direction = p2 - p1, point on line = p1
        cv::Point2f d = p2 - p1;
        float len = std::sqrt(d.x * d.x + d.y * d.y);
        if (len < 1e-6f) continue;
        d.x /= len; d.y /= len;

        // For point-to-line distance, we can use:
        // distance = |(p - p1) x d| where d is a unit direction vector
        // In 2D, cross product magnitude = |(dx,dy) x (ax,ay)| = |dx*ay - dy*ax|
        std::vector<int> inliers;
        inliers.reserve(points.size());

        for (int i = 0; i < (int)points.size(); ++i) {
            cv::Point2f a = points[i] - p1;
            float cross = d.x * a.y - d.y * a.x;
            float distPx = std::fabs(cross); // because d is unit-length

            if (distPx <= inlierThresholdPx) {
                inliers.push_back(i);
            }
        }

        if ((int)inliers.size() > bestInlierCount) {
            bestInlierCount = (int)inliers.size();
            bestInliers = std::move(inliers);
            bestModel = cv::Vec4f(d.x, d.y, p1.x, p1.y);
        }
    }

    if (bestInlierCount < minInliers) {
        return false;
    }

    // Refine: fit a line to inlier points using OpenCV's fitLine (least squares)
    std::vector<cv::Point2f> inlierPts;
    inlierPts.reserve(bestInliers.size());
    for (int idx : bestInliers) {
        inlierPts.push_back(points[idx]);
    }

    cv::Vec4f refined;
    // fitLine returns (vx, vy, x0, y0)
    cv::fitLine(inlierPts, refined, cv::DIST_L2, 0, 0.01, 0.01);

    outLine = refined;
    outInlierIdx = std::move(bestInliers);
    return true;
}

static std::vector<cv::Vec4f> ransacFitMultipleLines(
    std::vector<cv::Point2f> points,
    int maxLines = 2,
    int iterations = 250,
    float inlierThresholdPx = 4.0f,
    float minInlierRatio = 0.02f,   // 2% of current points
    int minInliersFloor = 150       // but never accept less than this
) {
    std::vector<cv::Vec4f> linesOut;

    for (int k = 0; k < maxLines; ++k) {
        if (points.size() < 2) break;

        int minInliers = std::max(minInliersFloor, (int)(points.size() * minInlierRatio));

        cv::Vec4f line;
        std::vector<int> inliers;
        bool found = ransacFitLine(points, line, inliers, iterations, inlierThresholdPx, minInliers);
        if (!found) break;

        linesOut.push_back(line);

        // Remove inliers from the working point set
        std::vector<char> isInlier(points.size(), 0);
        for (int idx : inliers) isInlier[idx] = 1;

        std::vector<cv::Point2f> remaining;
        remaining.reserve(points.size() - inliers.size());
        for (size_t i = 0; i < points.size(); ++i) {
            if (!isInlier[i]) remaining.push_back(points[i]);
        }
        points.swap(remaining);

        // Optional: early stop if too few points remain
        if (points.size() < (size_t)minInliersFloor) break;
    }

    return linesOut;
}


// Draw an infinite line (vx,vy,x0,y0) clipped to image bounds
static void drawFitLine(const cv::Vec4f& line, cv::Mat& image, const cv::Scalar& color, int thickness = 2)
{
    float vx = line[0], vy = line[1], x0 = line[2], y0 = line[3];

    // Choose two far points along the line and clip by using a large scale
    float scale = 10000.0f;
    cv::Point2f p1(x0 - vx * scale, y0 - vy * scale);
    cv::Point2f p2(x0 + vx * scale, y0 + vy * scale);

    cv::line(image, p1, p2, color, thickness);
}

int main() {

    cv::VideoCapture inputCapture(0);
    if (!inputCapture.isOpened()) {
        std::cerr << "Failed to open webcam\n";
        return -1;
    }

    while (true) {

        cv::Mat frameBGR;
        inputCapture >> frameBGR;
        if (frameBGR.empty()) break;

        cv::Mat frameProc = frameBGR.clone();

        //apply low sigma gaussian blur to reduce noise .5
        //filter size should be 6x the .5 sigma = 3x3
        // apply low sigma gaussian blur to reduce noise (sigma=0.5, kernel 3x3)
        cv::GaussianBlur(frameProc, frameProc, cv::Size(3, 3), 0.5, 0.5);

        // ===== RED MASK (HSV) =====
        cv::Mat hsv;
        cv::cvtColor(frameProc, hsv, cv::COLOR_BGR2HSV);

        cv::Mat maskRed1;
        cv::Mat maskRed2;
        cv::Mat colorMask;

        // here we determine two masks for red color, and that is just because of HSV values work
        // HSV has a 360 degree color wheel, red ends up being on both sides of the color, so we are just declaring
        // 2 different ranges and then combining them to create the full mask
        // why are we doing it this way instead of just using the raw RGB values?
        //
        // "because HSV is more robust to lighting changes,
        // and it allows us to specify a range of hues that we consider "red" instead of trying to find an exact match in RGB space,
        // which can be very sensitive to lighting and shadows."
        //
        // that is to say, HSV allows us to declare a much more flexible color range for real world conditions.
        // Lower-red region on hue wheel: 0°..20°
        cv::inRange(
            hsv,
            hsvToOpenCV(0.0f, 30.0f, 30.0f),
            hsvToOpenCV(40.0f, 100.0f, 100.0f),
            maskRed1
        );

        // maskRed2: 315°..360°
        cv::inRange(
            hsv,
            hsvToOpenCV(315.0f, 30.0f, 30.0f),
            hsvToOpenCV(360.0f, 100.0f, 100.0f),
            maskRed2
        );
        cv::bitwise_or(maskRed1, maskRed2, colorMask);


        // morphological opening followed by closing to reduce noise and fill gaps in the mask
        // if it is removed, the mask will be much noisier, and the edges will be more fragmented, which will lead to worse line detection results.
        // the size of the kernel is 3x3, which is a common choice for morphological operations, as it is small enough to preserve details while still being effective at removing noise and filling gaps.
        cv::Mat kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, { 3,3 });
        cv::morphologyEx(colorMask, colorMask, cv::MORPH_OPEN, kernel);
        cv::morphologyEx(colorMask, colorMask, cv::MORPH_CLOSE, kernel);

        // ===== EDGES FROM RED CHANNEL (MONO) + MASK =====
        std::vector<cv::Mat> bgr;
        cv::split(frameProc, bgr);
        cv::Mat redMono = bgr[2];             // only the red channel (0..255)

        // Keep only red-region pixels in the red channel image
        cv::Mat redMaskedMono;
        cv::bitwise_and(redMono, colorMask, redMaskedMono);

        // Optional: small blur helps stabilize Canny on sensor noise
        cv::GaussianBlur(redMaskedMono, redMaskedMono, cv::Size(3, 3), 0.5, 0.5);

        cv::Mat maskedEdges;
        cv::Canny(redMaskedMono, maskedEdges, 50, 150);

        cv::Mat maskEdge;
        cv::Mat k = cv::getStructuringElement(cv::MORPH_ELLIPSE, { 3,3 });
        cv::morphologyEx(colorMask, maskEdge, cv::MORPH_GRADIENT, k);

        cv::bitwise_and(maskedEdges, maskEdge, maskedEdges); // keep only boundary-aligned edges



        // ===== HOUGH LINES =====
        // the Houghlines function detects lines in the masked edge image, and it returns a vector of lines, where each line is represented by a 4-element vector (x1, y1, x2, y2) that defines the endpoints of the line segment.
        std::vector<cv::Vec4i> lines;
        cv::HoughLinesP(maskedEdges, lines, 1, CV_PI / 180, 50, 50, 10);

        // ===== RANSAC LINE FIT =====
        // below are two implementations.
        // manual scan and zero point implementation
        // manual scan is more straightforward to work with, but its much slower
        // zero point is faster, but I still don't really understand it. leaving both here to see which one works best

        //// Convert masked edge pixels into a point set for RANSAC.
        //std::vector<cv::Point2f> edgePoints;
        //edgePoints.reserve(5000);

        //// Collect non-zero pixels. This loops over the image and grabs points where maskedEdges is "on".
        //for (int y = 0; y < maskedEdges.rows; ++y) {
        //    const uchar* row = maskedEdges.ptr<uchar>(y);
        //    for (int x = 0; x < maskedEdges.cols; ++x) {
        //        if (row[x]) {
        //            edgePoints.emplace_back((float)x, (float)y);
        //        }
        //    }
        //}

        // Non-zero points implementation
        // Collect non-zero pixels using OpenCV (much faster than manual scanning)
        std::vector<cv::Point> nonZeroPts;
        cv::findNonZero(maskedEdges, nonZeroPts);

        // Convert to Point2f for the RANSAC function
        std::vector<cv::Point2f> edgePoints;
        edgePoints.reserve(nonZeroPts.size());

        for (const auto& p : nonZeroPts) {
            edgePoints.emplace_back((float)p.x, (float)p.y);
        }


        cv::Mat visualizationCanvas = frameProc.clone();

        // Draw Hough segments (optional: keep this if you want to compare)
        drawHoughLines(lines, visualizationCanvas);

        // Guard to ensure we have enough points for RANSAC. If not, just show the intermediate results and continue.
        if (edgePoints.size() < 2) {
            cv::imshow("Color Mask (HSV Red)", colorMask);
            cv::imshow("Masked Edges", maskedEdges);
            cv::imshow("Lines", visualizationCanvas);
            if (cv::waitKey(1) == 27) break;
            continue;
        }

        // Guard
        if (edgePoints.size() >= 2) {
            // Iterative multi-line RANSAC

            // NOTES: Ransac model tuning can be done below
            auto ransacLines = ransacFitMultipleLines(
                edgePoints,
                /*maxLines=*/3,
                /*iterations=*/500,
                /*inlierThresholdPx=*/2.0f,
                /*minInlierRatio=*/0.02f,
                /*minInliersFloor=*/200
            );

            for (const auto& L : ransacLines) {
                drawFitLine(L, visualizationCanvas, cv::Scalar(255, 0, 0), 3);
            }
        }

        cv::imshow("Color Mask (HSV Red)", colorMask);
        cv::imshow("Masked Edges", maskedEdges);
        cv::imshow("Lines", visualizationCanvas);

        if (cv::waitKey(1) == 27) break;
    }

    return 0;
}
