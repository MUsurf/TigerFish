#include <opencv2/opencv.hpp>
#include <cmath>
#include <algorithm>
#include <iostream>
#include "img_detection.h"

RedLineTracker::RedLineTracker(double smoothing, double angleGateDeg, bool debug) :
    smoothing(smoothing), debug(debug) { angleGateRad = angleGateDeg * CV_PI / 180.0;}
 
std::pair<cv::Mat, cv::Mat> RedLineTracker::processFrame(const cv::Mat& frame) {
    cv::Mat mask = detectRedMask(frame);
    cv::Mat frameCopy = frame.clone();
    std::vector<int> line = detectLine(mask);
    if (!line.empty()) {
        std::vector<int> trackedLine = trackLine(line, frame.size());
        drawLine(frameCopy, trackedLine);
    }
    return { frameCopy, mask };
}

cv::Mat RedLineTracker::detectRedMask(const cv::Mat& frame) {
    cv::Mat hsv, mask1, mask2, mask;
    cv::cvtColor(frame, hsv, cv::COLOR_BGR2HSV);
    cv::inRange(hsv, lowRed1, highRed1, mask1);
    cv::inRange(hsv, lowRed2, highRed2, mask2);
    cv::bitwise_or(mask1, mask2, mask);
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(5, 5));
    cv::morphologyEx(mask, mask, cv::MORPH_OPEN, kernel);
    cv::morphologyEx(mask, mask, cv::MORPH_DILATE, kernel);
    return mask;
}

std::vector<int> RedLineTracker::detectLine(const cv::Mat& mask) {
    
    std::vector<cv::Point> points;
    cv::findNonZero(mask, points);

    if (points.size() < 500) {
        return {};
    }

    // PCA to get line direction
    cv::Mat data(points.size(), 2, CV_32F);
    
    for (size_t i = 0; i < points.size(); ++i) {
        data.at<float>(i, 0) = points[i].x;
        data.at<float>(i, 1) = points[i].y;
    }
    
    cv::PCA pca(data, cv::Mat(), cv::PCA::DATA_AS_ROW);
    cv::Point2f center = cv::Point2f(pca.mean.at<float>(0), pca.mean.at<float>(1));
    cv::Point2f dir = cv::Point2f(pca.eigenvectors.at<float>(0, 0),
        pca.eigenvectors.at<float>(0, 1));
    
    double thetaDir = std::atan2(dir.y, dir.x);
    double theta = std::fmod(thetaDir + CV_PI / 2.0, CV_PI);
    
    // Fix angle flip
    if (prevTheta >= 0) {
        if (std::abs(angleDiff(theta, prevTheta)) > CV_PI / 4) {
            theta = std::fmod(theta + CV_PI / 2.0, CV_PI);
        }
    }
   
    double rho = center.x * std::cos(theta) + center.y * std::sin(theta);
    return polarToLine(rho, theta, mask.size());
}

std::vector<int> RedLineTracker::trackLine(const std::vector<int>& line, const cv::Size& frameSize) {
    auto [rho, theta] = lineToPolar(line);
    
    if (prevRho < 0 || prevTheta < 0) {
        prevRho = rho;
        prevTheta = theta;
        return polarToLine(rho, theta, frameSize);
    }
    
    double dtheta = angleDiff(theta, prevTheta);
    double alpha = std::clamp(smoothing + std::abs(dtheta), 0.7, 0.95);
    theta = prevTheta + (1.0 - alpha) * dtheta;
    rho = alpha * prevRho + (1.0 - alpha) * rho;
    prevTheta = theta;
    prevRho = rho;
    return polarToLine(rho, theta, frameSize);
}

std::pair<double, double> RedLineTracker::lineToPolar(const std::vector<int>& line) {
    int x1 = line[0], y1 = line[1], x2 = line[2], y2 = line[3];
    double dx = x2 - x1;
    double dy = y2 - y1;
    double thetaDir = std::atan2(dy, dx);
    double theta = std::fmod(thetaDir + CV_PI / 2.0, CV_PI);
    double rho = x1 * std::cos(theta) + y1 * std::sin(theta);
    return { rho, theta };
}

std::vector<int> RedLineTracker::polarToLine(double rho, double theta, const cv::Size& size) {
    double a = std::cos(theta);
    double b = std::sin(theta);
    double x0 = a * rho;
    double y0 = b * rho;
    int scale = std::max(size.width, size.height);
    int x1 = static_cast<int>(x0 + scale * (-b));
    int y1 = static_cast<int>(y0 + scale * a);
    int x2 = static_cast<int>(x0 - scale * (-b));
    int y2 = static_cast<int>(y0 - scale * a);
    return { x1, y1, x2, y2 };
}

double RedLineTracker::angleDiff(double a, double b) {
    double diff = a - b;
    return std::fmod(diff + CV_PI / 2, CV_PI) - CV_PI / 2;
}

void RedLineTracker::drawLine(cv::Mat& frame, const std::vector<int>& line) {
    cv::line(frame, cv::Point(line[0], line[1]), cv::Point(line[2], line[3]), cv::Scalar(0, 255, 0), 3);
    if (debug && prevTheta >= 0) {
        double angleDeg = prevTheta * 180.0 / CV_PI;
        cv::putText(frame, "Theta: " + std::to_string(angleDeg).substr(0, 5) + " deg",
            cv::Point(20, 30), cv::FONT_HERSHEY_SIMPLEX, 0.7,
            cv::Scalar(0, 255, 0), 2);
    }
}


// ===========================
// Main
// ===========================
int main() {
    cv::VideoCapture cap(0);
    if (!cap.isOpened()) {
        std::cerr << "Error opening video stream." << std::endl;
        return -1;
    }

    RedLineTracker tracker(0.6,10, true);

    while (true) {
        cv::Mat frame;
        cap >> frame;
        if (frame.empty()) break;

        auto [output, mask] = tracker.processFrame(frame);

        cv::imshow("Red Line Tracking", output);
        cv::imshow("Red Mask", mask);

        if (cv::waitKey(1) == 27) break;  // ESC to exit
    }

    cap.release();
    cv::destroyAllWindows();
    return 0;
}


