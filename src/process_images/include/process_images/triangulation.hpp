#ifndef TRIANGULATION_HPP
#define TRIANGULATION_HPP

#include <opencv2/opencv.hpp>

// Converts a pixel coordinate to bearing angles (radians) from the camera's
// optical axis, using the camera's intrinsic matrix (fx, fy, cx, cy from
// mono_calibration.yaml). Returned x = horizontal (azimuth) angle,
// y = vertical (elevation) angle. Positive azimuth = pixel right of center,
// positive elevation = pixel below center.
cv::Point2d pixel_to_angle(const cv::Point2d & pixel, const cv::Mat & camera_matrix);

// Same as above, but uses the camera matrix loaded from
// config/mono_calibration.yaml (loaded once on first call).
cv::Point2d pixel_to_angle(const cv::Point2d & pixel);

#endif // TRIANGULATION_HPP
