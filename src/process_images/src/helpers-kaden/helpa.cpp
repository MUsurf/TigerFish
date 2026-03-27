#include <opencv2/opencv.hpp>

using namespace cv;

void drawThatRect(Mat image, Point topLeft, Point topRight, Point bottomRight, Point bottomLeft, Point center, Point centerBottom, Point centerTop)
{
    circle(image, topLeft, 3, Scalar(32, 100, 100), -1);
    circle(image, topRight, 3, Scalar(32, 100, 100), -1);
    circle(image, bottomLeft, 3, Scalar(32, 100, 100), -1);
    circle(image, bottomRight, 3, Scalar(32, 100, 100), -1);
    circle(image, center, 3, Scalar(32, 100, 100), -1);
    circle(image, centerTop, 3, Scalar(32, 100, 100), -1);
    circle(image, centerBottom, 3, Scalar(32, 100, 100), -1);
    line(image, centerTop, centerBottom, Scalar(32, 100, 100), 3, LINE_AA);
    rectangle(image, topLeft, bottomRight, Scalar(32, 100, 100), 3, LINE_AA);
}