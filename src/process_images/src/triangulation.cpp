#include "process_images/triangulation.hpp"
#include <cmath>

cv::Point2d pixel_to_angle(const cv::Point2d & pixel, const cv::Mat & camera_matrix)
{
  if (pixel.x < 0 || pixel.y < 0 || pixel.x >= camera_matrix.at<double>(0, 2) * 2 || pixel.y >= camera_matrix.at<double>(1, 2) * 2) {
    throw std::invalid_argument("Pixel coordinates are out of bounds.");
  }
  double fx = camera_matrix.at<double>(0, 0);
  double fy = camera_matrix.at<double>(1, 1);
  double cx = camera_matrix.at<double>(0, 2);
  double cy = camera_matrix.at<double>(1, 2);

  double azimuth   = std::atan2(pixel.x - cx, fx);
  double elevation = std::atan2(pixel.y - cy, fy);

  return cv::Point2d(azimuth, elevation);
}

namespace
{
cv::Mat load_default_camera_matrix()
{
  cv::FileStorage fs("config/mono_calibration.yaml", cv::FileStorage::READ);
  cv::Mat camera_matrix;
  if (fs.isOpened()) {
    fs["camera"]["camera_matrix"] >> camera_matrix;
  }
  return camera_matrix;
}
}  // namespace

cv::Point2d pixel_to_angle(const cv::Point2d & pixel)
{
  static const cv::Mat camera_matrix = load_default_camera_matrix();
  return pixel_to_angle(pixel, camera_matrix);
}
