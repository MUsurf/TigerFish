#include "rclcpp/rclcpp.hpp"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <algorithm>
#include <random>

//for inliers
struct RansacLine
{
  cv::Vec4f model; //{vx, vy, x0, y0}
  std::vector<cv::Point2f> inliers; //points belonging to this line

};

struct GateResult
{
  std::vector<RansacLine> lines;   // (vx,vy,x0,y0) format for each line
};

//For prequal
struct LinesResult
{
  RansacLine horizontalBar; //Gate bar
  RansacLine verticalMarker; //Pole bar
  bool gateFound = false;
  bool markerFound = false;
  float lateralError = 0.0f; // distance from image center (px)
  float verticalError = 0.0f; // for gate depth control (px)
  float distance = 0.0f; //distance to the gate (likely inaccurate)

};

class Gate_detection
{
public:
  Gate_detection() = default;

  static GateResult find_gate(const cv::Mat & frame);
// returns ransac lines in (vx,vy,x0,y0) format, where (vx,vy) is the normalized direction vector and (x0,y0) is a point on the line

  static void visualize_lines(cv::Mat & display_frame, const GateResult & result);
  static void visualize_center_gate(cv::Mat & display_frame, const LinesResult & res);


// draws the ransac lines on the provided frame, for visualization purposes
  enum class TargetType { GATE, MARKER };
  static LinesResult prequal(
    const std::vector<RansacLine> & lines, int imgWidth, int imgHeight,
    TargetType currentTask);

  // Draw an infinite line (vx,vy,x0,y0) clipped to image bounds
// (color and thickness parameters are optional for flexibility in visualization)
  static void drawFitLines(
    const std::vector<RansacLine> & lines,
    cv::Mat & image,
    const cv::Scalar & color = cv::Scalar(255, 0, 0), // Red by default
    int thickness = 2
  );

private:
  static cv::Scalar hsvToOpenCV(float h_deg, float s_pct, float v_pct);

// ===== RANSAC LINE FIT  =====
// Fits a single dominant line to a set of 2D points using RANSAC, then refines with cv::fitLine on inliers.
// Returns true if a line was found. Output is (vx, vy, x0, y0) in the same format as cv::fitLine.
  static std::vector<RansacLine> ransacDetectLines(
    std::vector<cv::Point2f> points,   // pass by value on purpose (we mutate / shrink it)
    int maxLines = 4,
    int iterations = 300,
    float inlierThresholdPx = 1.0f,
    float minInlierRatio = 0.02f,
    int minInliersFloor = 200
  );


};
