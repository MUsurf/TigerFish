#include "process_images/prequal_helper.hpp"


// A) Get Masks
// Setting color ranges
// setting shape

// B) get the lines 




/**
 * @brief Mask image from given HSV ranges. HSV in red has to be split into two ranges since red wraps around the color disk
 
    @details lowerHSV and upperHSV are to handle a case where the color wraps around the color space. 
 
 * @param inputImage 
 * @param outputMask 
 * @param lower1HSV First lower HSV range (e.g., for red: [0, 100, 100])
 * @param higher1HSV First upper HSV range (e.g., for red: [10, 255, 255])
 * @param lower2HSV Second lower HSV range in case HSV wraps around
 * @param higher2HSV Second upper HSV range in case HSV wraps around
 * @return cv::Mat Masked image based on the provided HSV ranges
 */
cv::Mat applyColorHSVMask(const cv::Mat& inputImage, 
                          cv::Mat& outputMask, 
                          std::array<float, 3> lower1HSV, 
                          std::array<float, 3> higher1HSV, 
                          std::optional<std::array<float, 3>> lower2HSV, 
                          std::optional<std::array<float, 3>> higher2HSV)
{
    // Convert the image to HSV color space
    cv::Mat hsvImage;
    cv::cvtColor(inputImage, hsvImage, cv::COLOR_BGR2HSV);
    cv::Scalar low1(lower1HSV[0], lower1HSV[1], lower1HSV[2]);
    cv::Scalar high1(higher1HSV[0], higher1HSV[1], higher1HSV[2]);
    // If the second range is not provided, use only the first range
    if (!lower2HSV.has_value() || !higher2HSV.has_value()) {
        cv::inRange(hsvImage, low1, high1, outputMask);
        return outputMask;
    }
    
    // Create masks for the two red ranges
    // Needs two sets of values because red wraps around
    cv::Mat mask1, mask2;

    cv::Scalar low2(lower2HSV.value()[0], lower2HSV.value()[1], lower2HSV.value()[2]);
    cv::Scalar high2(higher2HSV.value()[0], higher2HSV.value()[1], higher2HSV.value()[2]);

    cv::inRange(hsvImage, low1, high1, mask1);
    cv::inRange(hsvImage, low2, high2, mask2);

    // Combine the two masks
    outputMask = mask1 | mask2;
    return outputMask;
}

