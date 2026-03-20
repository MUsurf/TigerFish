#include "rclcpp/rclcpp.hpp"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <algorithm>
#include <random>

struct GoalResult
{
  std::vector<cv::Vec4f> lines;   // (vx,vy,x0,y0) format for each line
  bool found = false; // whether any lines were found
};

class Goal_detection
{
public:
  Goal_detection() = default;

  static GoalResult find_gate(const cv::Mat & frame);
// returns ransac lines in (vx,vy,x0,y0) format, where (vx,vy) is the normalized direction vector and (x0,y0) is a point on the line

  static void visualize_lines(cv::Mat & display_frame, const GoalResult & result);
// draws the ransac lines on the provided frame, for visualization purposes

private:
  static cv::Scalar hsvToOpenCV(float h_deg, float s_pct, float v_pct);

// ===== RANSAC LINE FIT  =====
// Fits a single dominant line to a set of 2D points using RANSAC, then refines with cv::fitLine on inliers.
// Returns true if a line was found. Output is (vx, vy, x0, y0) in the same format as cv::fitLine.
  static std::vector<cv::Vec4f> ransacDetectLines(
    std::vector<cv::Point2f> points,   // pass by value on purpose (we mutate / shrink it)
    int maxLines = 4,
    int iterations = 300,
    float inlierThresholdPx = 1.0f,
    float minInlierRatio = 0.02f,
    int minInliersFloor = 200
  );
// Draw an infinite line (vx,vy,x0,y0) clipped to image bounds
// (color and thickness parameters are optional for flexibility in visualization)
  static void drawFitLines(
    const std::vector<cv::Vec4f> & lines,
    cv::Mat & image,
    const cv::Scalar & color = cv::Scalar(255, 0, 0), // Red by default
    int thickness = 2
  );

};
