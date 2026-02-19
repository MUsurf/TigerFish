#pragma once
#include <opencv2/opencv.hpp>
#include <cmath>
#include <iostream>
#include <utility>
#include <vector>

class RedLineTracker 
{
public:
    RedLineTracker(double smoothing = 0.85, double angleGateDeg = 10, bool debug = false);

    std::pair<cv::Mat, cv::Mat> processFrame(const cv::Mat& frame);

private:
    cv::Scalar lowRed1 = cv::Scalar(0, 150, 80);        // Sets the lower threshold used to find the red line
    cv::Scalar highRed1 = cv::Scalar(10, 255, 255);     // Sets the higher threshold used to find the red line
    cv::Scalar lowRed2 = cv::Scalar(174, 150, 80);      // second set of scalars are used to 
    cv::Scalar highRed2 = cv::Scalar(180, 255, 255);

    double smoothing{ 0.85 };
    double angleGateRad{ 10.0 * CV_PI / 180.0 };
    bool debug{ false };

    // Previous frame's smoothed polar coordinates
    double prevRho = { -1.0 };
    double prevTheta = { -1.0 };

    // Returns a black and white mask outlining the objects that we want to detect
    cv::Mat detectRedMask(const cv::Mat& frame);

    //uses principal component analysis to draw a line 
    std::vector<int> detectLine(const cv::Mat& mask);

    // keeps track of the line's previous state, making it so that the line doesn't jump
    std::vector<int> trackLine(const std::vector<int>& line, const cv::Size& frameSize);

    // helper functions for trackLine
    std::pair<double, double> lineToPolar(const std::vector<int>& line);

    // helper functions for trackLine
    std::vector<int> polarToLine(double rho, double theta, const cv::Size& size);

    // helper for 
    double angleDiff(double a, double b);

    void drawLine(cv::Mat& frame, const std::vector<int>& line);

};