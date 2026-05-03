#ifndef PREQUAL_LINE_HPP
#define PREQUAL_LINE_HPP

#include <opencv2/opencv.hpp>
#include <vector>
#include <cmath>


struct PoleShapeData{
    bool detected = false;
    bool outOfFrame = false;
    // cv::Mat mask;
    cv::Point topLeft;
    cv::Point topRight;
    cv::Point bottomRight;
    cv::Point bottomLeft;
    cv::Point center;
    cv::Point centerTop;
    cv::Point centerBottom;
    int width;
    int height;

};

struct MarkerAngles{
    double yaw; // Left (-) to Right (+)
    double pitch; // down(-) to up(+)
};
PoleShapeData getPoleShape(const cv::Mat& frame);

// PoleShapeData getPoleCoords(const cv::Mat& frame);

MarkerAngles getAnglesToTop(const PoleShapeData& data, const cv::Mat& cameraMatrix);


#endif // PREQUAL_LINE_HPPx