#ifndef MARKER_DETECTOR_HPP
#define MARKER_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <vector>


//the goal of this code is to detect orange markers in the pool and determine positioning information
struct MarkerResult
{
  cv::Point2f center;
  cv::Point2f norm_position;   // [-1, 1] in both axes
  std::vector<cv::Point> contour;
  float depth = 0.0f;
  // Heading-error angle in degrees: 0 = path aligned with sub forward (vertical in image),
  // 90 = path perpendicular to forward. Range [0, 90]. Sign ambiguity is inherent for a
  // symmetric marker — left vs right lean cannot be distinguished from shape alone.
  float angle = 0.0f;
  double area = 0.0;   // contour area in pixels, used to pick the best camera's detection
  bool found = false;
};


class MarkerDetector
{
public:
  //takes the focal length of the camera; actual width of the markers
  MarkerDetector(double focal_length, double actual_width);

  MarkerResult find_markers(const cv::Mat & frame);

  void visualize_markers(cv::Mat & display_frame, const MarkerResult & result);

  void setHSVBounds(int h_low, int h_high, int s_low, int s_high, int v_low, int v_high);
  void setMinArea(double min_area);

private:
  double focal_length_;
  double actual_width_;

  int hue_low = 8;
  int saturation_low = 110;
  int value_low = 80;

  int hue_high = 22;
  int saturation_high = 255;
  int value_high = 255;

  double min_area_ = 600.0;
};


#endif
