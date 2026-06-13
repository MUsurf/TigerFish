#include "process_images/marker_detector.hpp"
#include <cmath>

MarkerDetector::MarkerDetector(double focal_length, double actual_width)
: focal_length_(focal_length), actual_width_(actual_width) {}

void MarkerDetector::setHSVBounds(
  int h_low, int h_high, int s_low, int s_high, int v_low, int v_high)
{
  hue_low = h_low; hue_high = h_high;
  saturation_low = s_low; saturation_high = s_high;
  value_low = v_low; value_high = v_high;
}

void MarkerDetector::setMinArea(double min_area)
{
  min_area_ = min_area;
}

MarkerResult MarkerDetector::find_markers(const cv::Mat & frame)
{
  MarkerResult result;

  cv::Mat hsv, mask;
  cv::cvtColor(frame, hsv, cv::COLOR_BGR2HSV);
  cv::inRange(
    hsv,
    cv::Scalar(hue_low, saturation_low, value_low),
    cv::Scalar(hue_high, saturation_high, value_high),
    mask);

  cv::Mat dilated;
  cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(11, 11));
  cv::dilate(mask, dilated, kernel);

  std::vector<std::vector<cv::Point>> contours;
  cv::findContours(dilated, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

  // Track the largest valid contour across the whole frame
  double best_area = 0.0;
  cv::RotatedRect best_rect;
  std::vector<cv::Point> best_contour;

  for (const auto & contour : contours) {
    double area = cv::contourArea(contour);
    if (area <= min_area_) {continue;}

    cv::RotatedRect rect = cv::minAreaRect(contour);
    float w = rect.size.width;
    float h = rect.size.height;
    float aspect_ratio = std::max(w, h) / std::min(w, h);
    float rect_area = w * h;
    float extent = area / rect_area;
    bool is_close = (area > (frame.rows * frame.cols * 0.1));

    // Gate check: gates are tall and skinny (vertical poles)
    if (h > (w * 1.5) && aspect_ratio > 2.0) {continue;}

    // Marker should appear in the lower portion of the frame (floor)
    if (rect.center.y < (frame.rows * 0.35)) {continue;}

    // Aspect ratio filters
    if (!is_close && aspect_ratio < 1.5) {continue;}
    if (aspect_ratio > 10.0) {continue;}

    // Extent (fill ratio) filter
    if (extent < 0.3) {continue;}

    if (area > best_area) {
      best_area = area;
      best_rect = rect;
      best_contour = contour;
    }
  }

  if (best_area > 0.0) {
    result.found = true;
    result.contour = best_contour;
    result.area = best_area;
    result.center = best_rect.center;

    const float K = 200.0f;
    result.depth = K / std::sqrt(static_cast<float>(best_area));

    result.norm_position.x =
      (best_rect.center.x - frame.cols / 2.0f) / (frame.cols / 2.0f);
    result.norm_position.y =
      (best_rect.center.y - frame.rows / 2.0f) / (frame.rows / 2.0f);

    // Heading-error angle: 0 = path aligned with sub forward (long axis vertical in image).
    // OpenCV minAreaRect returns angle in [-90, 0) where 0 means the width axis is horizontal.
    // Adding 90 maps [-90, 0) → [0, 90): 0 when vertical (aligned), 90 when horizontal (perpendicular).
    // Note: a symmetric marker cannot distinguish left-lean from right-lean; the result is
    // always in [0, 90]. Use norm_position.x for lateral offset if direction context is needed.
    result.angle = best_rect.angle + 90.0f;
  }

  return result;
}

void MarkerDetector::visualize_markers(cv::Mat & display_frame, const MarkerResult & result)
{
  if (!result.found) {return;}

  cv::drawContours(
    display_frame,
    std::vector<std::vector<cv::Point>>{result.contour}, -1,
    cv::Scalar(0, 255, 0), 2);

  std::vector<cv::Point> hull;
  cv::convexHull(result.contour, hull);
  cv::drawContours(
    display_frame,
    std::vector<std::vector<cv::Point>>{hull}, -1,
    cv::Scalar(0, 0, 255), 2);

  cv::drawMarker(
    display_frame, result.center, cv::Scalar(255, 0, 0),
    cv::MARKER_CROSS, 20, 2);

  std::string depth_txt = "Depth: " + std::to_string(result.depth).substr(0, 4) + "m";
  cv::putText(
    display_frame, depth_txt, cv::Point(10, 30),
    cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(255, 255, 255), 2);

  std::string angle_txt = "Heading err: " + std::to_string(result.angle).substr(0, 4) + "deg";
  cv::putText(
    display_frame, angle_txt, cv::Point(10, 65),
    cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(255, 255, 255), 2);
}
