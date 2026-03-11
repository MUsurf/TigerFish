#ifndef MARKER_DETECTOR_HPP
#define MARKER_DETECTOR_HPP

#include <opencv2/opencv.hpp>
#include <vector>


//the goal of this code is to detect orange markers in the pool and determine positioning information
struct MarkerResult
{
  cv::Point2f center;   //pixel location
  cv::Point2f norm_position;   //pixel location sconverted to -1.0 and 1.0 (ie normalized)
  std::vector<cv::Point> contour;   //contour point
  float depth;
  float angle;
  bool found;
};


class MarkerDetector{
public:
        //takes the focal length of the camera; actual width of the markers
  MarkerDetector(double focal_length, double actual_width);

  MarkerResult find_markers(const cv::Mat & frame);

  void visualize_markers(cv::Mat & display_frame, const MarkerResult & result);

private:
  double focal_length_;
  double actual_width_;

  int hue_low = 8;
  int saturation_low = 110;
  int value_low = 80;

  int hue_high = 22;
  int saturation_high = 255;
  int value_high = 255;
};


#endif
