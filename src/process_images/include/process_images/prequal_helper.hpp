#ifndef PREQUAL_HELPER_HPP
#define PREQUAL_HELPER_HPP

#include <opencv2/opencv.hpp>
#include <optional>


cv::Mat applyColorHSVMask(const cv::Mat& inputImage, cv::Mat& outputMask, std::array<float, 3> lower1HSV, std::array<float, 3> higher1HSV, std::optional<std::array<float, 3>> lower2HSV = std::nullopt, std::optional<std::array<float, 3>> higher2HSV = std::nullopt);


#endif // PREQUAL_HELPER_HPP