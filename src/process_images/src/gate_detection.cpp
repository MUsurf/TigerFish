// #include <opencv2/opencv.hpp>
// #include "process_images/gate_detection.hpp"
// #include <iostream>
// #include <algorithm>
// #include <random>
// #include <cmath>

// // --- Human HSV (H:0-360 deg, S/V:0-100%) -> OpenCV HSV (H:0-179, S/V:0-255) ---
// // Put this near the top of your file (needs <algorithm> for std::clamp)

// // for prequalification we are going to be working with gates and poles

// // This is a helper that I am using to abstract away openCV's weird HSV scaling. which goes from 0-179 for H, 0-255 for S and V
// // pluging it in like this allows us to visualize the color space with commonly available color pickers.
// cv::Scalar Gate_detection::hsvToOpenCV(float h_deg, float s_pct, float v_pct)
// {
//   // Convert
//   int h = static_cast<int>(h_deg / 2.0f);     // 0-360 -> 0-180 (OpenCV uses 0-179)
//   int s = static_cast<int>(s_pct * 2.55f);    // 0-100 -> 0-255
//   int v = static_cast<int>(v_pct * 2.55f);    // 0-100 -> 0-255

//   // Clamp to OpenCV valid ranges
//   h = std::clamp(h, 0, 179);
//   s = std::clamp(s, 0, 255);
//   v = std::clamp(v, 0, 255);

//   return cv::Scalar(h, s, v);
// }

// // ===== RANSAC LINE FIT  =====
// // Fits a single dominant line to a set of 2D points using RANSAC, then refines with cv::fitLine on inliers.
// // Returns true if a line was found. Output is (vx, vy, x0, y0) in the same format as cv::fitLine.
// // helper function to fit line
// // Detect up to maxLines line models from a point cloud using iterative RANSAC,
// // removing inliers after each detection (multi-line extraction).
// std::vector<RansacLine> Gate_detection::ransacDetectLines(
//   std::vector<cv::Point2f> points,     // pass by value on purpose (we mutate / shrink it)
//   int maxLines,
//   int iterations,
//   float inlierThresholdPx,
//   float minInlierRatio,
//   int minInliersFloor
// )
// {
//   std::vector<RansacLine> linesOut;
//   if (points.size() < 2) {return linesOut;}

//   // Deterministic RNG (same as your original). Change seed if you want randomness.
//   static std::mt19937 rng(12345);

//   for (int k = 0; k < maxLines; ++k) {
//     if (points.size() < 2) {break;}

//     const int minInliers = std::max(
//       minInliersFloor,
//       static_cast<int>(points.size() * minInlierRatio));

//     // --- Single-line RANSAC fit (inlined) ---
//     std::vector<int> bestInliers;
//     bestInliers.reserve(points.size());

//     int bestInlierCount = 0;
//     cv::Vec4f bestModel(0, 0, 0, 0);

//     std::uniform_int_distribution<int> dist(0, static_cast<int>(points.size() - 1));

//     // ransac iteration loop
//     for (int it = 0; it < iterations; ++it) {
//       const int i1 = dist(rng);
//       const int i2 = dist(rng);
//       if (i1 == i2) {continue;}

//       const cv::Point2f & p1 = points[i1];
//       const cv::Point2f & p2 = points[i2];

//       // direction = normalized (p2 - p1)
//       cv::Point2f d = p2 - p1;
//       const float len = std::sqrt(d.x * d.x + d.y * d.y);
//       if (len < 1e-6f) {continue;}
//       d.x /= len; d.y /= len;

//       // collect inliers by point-to-line distance using 2D cross product magnitude
//       std::vector<int> inliers;
//       inliers.reserve(points.size());

//       for (int i = 0; i < (int)points.size(); ++i) {
//         const cv::Point2f a = points[i] - p1;
//         const float cross = d.x * a.y - d.y * a.x;               // |d x a|
//         const float distPx = std::fabs(cross);                   // d is unit-length

//         if (distPx <= inlierThresholdPx) {
//           inliers.push_back(i);
//         }
//       }

//       if ((int)inliers.size() > bestInlierCount) {
//         bestInlierCount = (int)inliers.size();
//         bestInliers = std::move(inliers);
//         bestModel = cv::Vec4f(d.x, d.y, p1.x, p1.y);             // (vx, vy, x0, y0)
//       }

//     }


//     // If we can't get enough inliers, stop extracting more lines.
//     if (bestInlierCount < minInliers) {break;}

//     RansacLine rl;
//     for (int idx : bestInliers) {
//       rl.inliers.push_back(points[idx]);
//     }


//     cv::fitLine(rl.inliers, rl.model, cv::DIST_L2, 0, 0.01, 0.01);

//     linesOut.push_back(rl);

//     // --- Remove inliers from the working set for multi-line detection ---
//     std::vector<char> isInlier(points.size(), 0);
//     for (int idx : bestInliers) {
//       isInlier[idx] = 1;
//     }

//     std::vector<cv::Point2f> remaining;
//     remaining.reserve(points.size() - bestInliers.size());
//     for (size_t i = 0; i < points.size(); ++i) {
//       if (!isInlier[i]) {remaining.push_back(points[i]);}}

//     points.swap(remaining);

//     // Optional early stop if too few points remain to form another strong line
//     if (points.size() < (size_t)minInliersFloor) {break;}
//   }

//   return linesOut;
// }

// GateResult Gate_detection::find_gate(
//   const cv::Mat & frame) // I don't think we need the lines input
// {
//   GateResult result;
//   cv::Mat frameProc = frame.clone();

//   // ===== RED MASK (HSV) =====
//   cv::Mat hsv;
//   cv::cvtColor(frameProc, hsv, cv::COLOR_BGR2HSV);

//   cv::Mat maskRed1;
//   cv::Mat maskRed2;
//   cv::Mat colorMask;

//   cv::inRange(
//     hsv,
//     Gate_detection::hsvToOpenCV(0.0f, 30.0f, 30.0f),
//     Gate_detection::hsvToOpenCV(40.0f, 100.0f, 100.0f),
//     maskRed1
//   );

//   // maskRed2: 315°..360°
//   cv::inRange(
//     hsv,
//     Gate_detection::hsvToOpenCV(315.0f, 30.0f, 30.0f),
//     Gate_detection::hsvToOpenCV(360.0f, 100.0f, 100.0f),
//     maskRed2
//   );
//   cv::bitwise_or(maskRed1, maskRed2, colorMask);


//   // morphological opening followed by closing to reduce noise and fill gaps in the mask
//   // if it is removed, the mask will be much noisier, and the edges will be more fragmented, which will lead to worse line detection results.
//   // the size of the kernel is 3x3, which is a common choice for morphological operations, as it is small enough to preserve details while still being effective at removing noise and filling gaps.
//   cv::Mat kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3});
//   cv::morphologyEx(colorMask, colorMask, cv::MORPH_OPEN, kernel);
//   cv::morphologyEx(colorMask, colorMask, cv::MORPH_CLOSE, kernel);

//   // ===, maskEdge, maskedEdges);   // keep only boundary-aligned edges

//   // Non-zero points implementation
//   // Collect non-zero pixels using OpenCV (much faster than manual scanning)
//   std::vector<cv::Point> nonZeroPts;
//   cv::findNonZero(maskedEdges) //== EDGES FROM RED CHANNEL (MONO) + MASK =====
//   std::vector<cv::Mat> bgr;
//   cv::split(frameProc, bgr);
//   cv::Mat redMono = bgr[2];   // only the red channel (0..255)

//   // Keep only red-region pixels in the red channel image
//   cv::Mat redMaskedMono;
//   cv::bitwise_and(redMono, redMono, redMaskedMono, colorMask);

//   cv::Mat maskedEdges;
//   cv::Canny(redMaskedMono, maskedEdges, 50, 150);

//   cv::Mat maskEdge;
//   cv::Mat k = cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3});
//   cv::morphologyEx(colorMask, maskEdge, cv::MORPH_GRADIENT, k);

//   cv::bitwise_and(maskedEdges, nonZeroPts);

//   // Convert to Point2f for the RANSAC function
//   std::vector<cv::Point2f> edgePoints;
//   edgePoints.reserve(nonZeroPts.size());

//   for (const auto & p : nonZeroPts) {
//     edgePoints.emplace_back((float)p.x, (float)p.y);
//   }

//   cv::Mat visualizationCanvas = frameProc.clone();

//   // Guard to ensure we have enough points for RANSAC. If not, just show the intermediate results and continue.
//   if (edgePoints.size() < 2) {
//     return result; // Not enough points to fit a line
//   }

//   std::vector<RansacLine> ransacLines = Gate_detection::ransacDetectLines(edgePoints);
//   result.lines = ransacLines;

//   return result;
// }

// // Draw an infinite line (vx,vy,x0,y0) clipped to image bounds
// void Gate_detection::drawFitLines(
//   const std::vector<RansacLine> & lines,
//   cv::Mat & image,
//   const cv::Scalar & color,
//   int thickness
// )
// {
//   for (const auto & line : lines) {
//     float vx = line.model[0], vy = line.model[1], x0 = line.model[2], y0 = line.model[3];

//     // Choose two far points along the line and clip by using a large scale
//     float scale = 10000.0f;
//     cv::Point2f p1(x0 - vx * scale, y0 - vy * scale);
//     cv::Point2f p2(x0 + vx * scale, y0 + vy * scale);

//     cv::line(image, p1, p2, color, thickness);
//   }
// }

// void Gate_detection::visualize_lines(
//   cv::Mat & display_frame,
//   const GateResult & result)
// {
//   const auto & lines = result.lines;
//   Gate_detection::drawFitLines(lines, display_frame, cv::Scalar(255, 0, 0), 3);
// }

// void Gate_detection::visualize_center_gate(
//   cv::Mat & display_frame,
//   const LinesResult & res
// )
// {
//   //res has the following fields
//   // RansacLine horizontalBar; //Gate bar
//   // RansacLine verticalMarker; //Pole bar
//   // bool gateFound = false;
//   // bool markerFound = false;
//   // float lateralError = 0.0f; // distance from image center (px)
//   // float verticalError = 0.0f; // for gate depth control (px)
//   // float distance = 0.0f; //distance to the gate (likely inaccurate)

//   if (res.gateFound == true) {
//     //visualize the lines, both

//     std::vector<RansacLine> linesToDraw;
//     if (res.horizontalBar.model[0] != 0 || res.horizontalBar.model[1] != 0) {
//       linesToDraw.push_back(res.horizontalBar);
//     }
//     if (res.verticalMarker.model[0] != 0 || res.verticalMarker.model[1] != 0) {
//       linesToDraw.push_back(res.verticalMarker);
//     }

//     drawFitLines(linesToDraw, display_frame, cv::Scalar(0, 0, 255), 2);


//     //draw center
//     int targetX = static_cast<int>((display_frame.cols / 2.0f) + res.lateralError);
//     int targetY = static_cast<int>((display_frame.rows / 2.0f) + res.verticalError);
//     cv::Point targetPt(targetX, targetY);

//     cv::circle(display_frame, targetPt, 10, cv::Scalar(0, 255, 0), -1);

//     // put distance text
//     std::string text = "Dist: " + std::to_string(res.distance).substr(0, 4) + "m";

//     cv::putText(
//       display_frame, text, cv::Point(30, 30), cv::FONT_HERSHEY_SIMPLEX, 0.8,
//       cv::Scalar(0, 0, 255), 2);

//   }

// }


// /**
//  * @brief Get the X at Y Postion on a particular line
//  * 
//  * @param line line that x position lies on
//  * @param y the y coordinate
//  * @return float 
//  */
// float getXatY(const RansacLine & line, float y){
//   float vx = line.model[0], vy = line.model[1], x0 = line.model[2], y0 = line.model[3];
//   if (std::abs(vy) < 1e-6)
//   {
//     return x0;
//   }

//   return x0 + (vx / vy) * (y - y0);


// }


// /**
//  * @brief gets top of gate, midpoint of gate, 4 corners of gate. distance to gate (optional)
//  * 
//  */
// void findGateFeatures(){




// }


// void findPoleFeatures(){

// }

// void 


// LinesResult Gate_detection::prequal(
//   const std::vector<RansacLine> & lines, int imgWidth,
//   int imgHeight, TargetType currentTask)
// {

//   LinesResult res;
//   float screenCenterX = imgWidth / 2.0f;
//   float screenCenterY = imgHeight / 2.0f;

//   // if (currentTask == Gate_detection::TargetType::GATE) {
//   //   std::vector<RansacLine> verticalPoles;
//   //   RansacLine topBar;
//   //   bool foundTopBar = false;

//   //   for (const auto & line : lines) {
//   //     float vx = std::abs(line.model[0]);
//   //     float vy = std::abs(line.model[1]);


//   //     // horizontal line = gate
//   //     if (std::abs(vx) > 0.9f && !res.gateFound) {
//   //       topBar = line;
//   //       foundTopBar = true; //horizontal bar is top bar of the gate! :)
//   //     } else if (vy > 0.9f) {
//   //       verticalPoles.push_back(line);
//   //     }
//   //   }

//   //   //get center of gate
//   //   //IDEA: prequal gate may have 3 vert lines. find center point of each line if that point is on another vertical line it is a gate 
//   //   if (verticalPoles.size() >= 2) { //2 vertical poles
//   //     res.gateFound = true;
//   //     res.verticalMarker = verticalPoles[0];

//   //     float x1 = getXatY(verticalPoles[0], screenCenterY);
//   //     float x2 = getXatY(verticalPoles[1], screenCenterY);

//   //     float targetCenterX = (x1 + x2) / 2.0f; //x is between the two poles
//   //     float pixelWidth = std::abs(x1 - x2); //width in pixels

//   //     res.lateralError = targetCenterX - screenCenterX;

//   //     // float knownGateWidthMeters = 2f; // the gate width (meters)
//   //     // float focalLengthPx = 800.0f; // focal length in pixels
//   //     // res.distance = (knownGateWidthMeters * focalLengthPx) / pixelWidth;
//   //     res.distance = 0.0f; //temporary set to this so it doesn't yell at me for display purposes... todo

//   //     if (!foundTopBar) { //estimation of vertical error
//   //       res.verticalError = (screenCenterY + (pixelWidth / 2.0f)) - screenCenterY; // best guess of vertical error... this will always be positive so we will only head one way which is no good TODO
//   //     }

//   //   }
//   //   if (foundTopBar) { //found top bar
//   //     res.gateFound = true;
//   //     res.horizontalBar = topBar;


//   //     float verticalOffset = 100.0f; // static number of PIXELS to guesstimate position. we don't want to be on top bar. this value is dubious, should be proportional bc distance from gate changes
//   //     res.verticalError = (topBar.model[3] + verticalOffset) - screenCenterY; 
//   //   }

//   }
//   else{ //pole detection 
//     // THINGS WE WANT  //
//     // Top of pole 
//     // angle to top
//     // we want middle of pole
//     /////////////////////


//   }

//   return res;
// }
