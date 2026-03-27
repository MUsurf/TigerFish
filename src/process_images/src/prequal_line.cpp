#include "process_images/prequal_line.hpp"



/**
 * @brief Cleans up the frame and returns a mask of the pole shape
 * 
 * @param frame 
 * @return poleShapeData a bitmask of the pole shape, where the pole is white and the rest is black
 */
PoleShapeData getPoleShape(const cv::Mat& frame){

    PoleShapeData res;
    double maxArea = 0;
    res.detected = false;
    //create a blank image for visualizatsion
    cv::Mat cleanMask = cv::Mat::zeros(frame.size(), CV_8UC1);


    // Deep copy the input frame
    cv::Mat processed_im;
    // Clean up the noise in the mask, removing speckles and weakly connected things
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(3, 3));
    cv::morphologyEx(frame, processed_im, cv::MORPH_OPEN, kernel);
    cv::morphologyEx(processed_im, processed_im, cv::MORPH_CLOSE, kernel);


    // We find the contours 
    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(processed_im, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

    for (const auto& cnt: contours){
        double area = cv::contourArea(cnt);

        // filter out stuff 
        double frameArea = frame.cols * frame.rows;
        double minArea = frameArea*0.002;
        if (area < minArea){
            continue; // Object to skip it
        }
        
        // now that we have filtered a bit more, we can prform the actual shape detection
        cv::Rect bbox = cv::boundingRect(cnt);
        float aspectRatioOfObject = (float)bbox.height / bbox.width;


        // calculate Solidity - describe convex area and how different it is from the rectangle
        std::vector<cv::Point> hull;
        cv::convexHull(cnt, hull);
        double hullArea = cv::contourArea(hull);
        float solidity = 0;
        if(hullArea > 0){
            solidity = (float) area/hullArea;
        }

        // look for pole shape ie
        // vertical (height> width)
        if(aspectRatioOfObject>2.0f && solidity > 0.7f){
            // cv::drawContours(cleanMask, std::vector<std::vector<cv::Point>>{cnt}, -1, cv::Scalar(255), cv::FILLED);
            if (area > maxArea){
                maxArea = area;
                res.detected = true;

                // define a 2-pixel margin to check if the pole is in frame, otherwise mark as out of frame!
                int margin = 2;
                if(bbox.x <= margin ||
                    bbox.y <= margin ||
                    (bbox.x+bbox.width)>=(frame.cols - margin) ||
                    (bbox.y+bbox.height)>=(frame.rows - margin)){
                        res.outOfFrame = true;
                }

                res.topLeft = bbox.tl();
                res.topRight= cv::Point(bbox.x+bbox.width, bbox.y);
                res.bottomRight = bbox.br();
                res.bottomLeft = cv::Point(bbox.x, bbox.y+bbox.height);
                res.center = cv::Point(bbox.x + bbox.width/2, bbox.y+bbox.height/2);
                res.centerTop = cv::Point(bbox.x + bbox.width/2, bbox.y);
                res.centerBottom = cv::Point(bbox.x + bbox.width/2, bbox.y + bbox.height);

            }



            std::cout<< "Pole found at: " << bbox.x + (bbox.width/2) <<std::endl;
        }
    }

    return res;

}

MarkerAngles getAnglesToTop(const PoleShapeData& data, const cv::Mat& cameraMatrix){
    //calibration matrix for camera
    // this is important for the real life info about the camera, which the angle is heavily dependent on 
    double fx = cameraMatrix.at<double>(0, 0);
    double fy = cameraMatrix.at<double>(1, 1);
    double cx = cameraMatrix.at<double>(0, 2);
    double cy = cameraMatrix.at<double>(1, 2);

    // get the midpoints of the pole from the PoleShapeData
    // struct PoleShapeData{
    // bool detected = false;
    // bool outOfFrame = false;
    // // cv::Mat mask;
    // cv::Point topLeft;
    // cv::Point topRight;
    // cv::Point bottomRight;
    // cv::Point bottomLeft;
    // cv::Point center;
    // cv::Point centerTop;
    // cv::Point centerBottom;
    // };

    cv::Point2f centerTop = (cv::Point2f)data.centerTop; // get center top

    // calculate angle in radians
    //yaw: x relative to optical center
    double angleYawRad = std::atan2(centerTop.x - cx, fx);

    //Pitch: y relative to optical center
    // cy -y since Y increases downwards
    double anglePitchRad = std::atan2(cy - centerTop.y, fy);

    //convert to degrees
    const double rad2deg = 180.0 / M_PI;

    return {angleYawRad * rad2deg, anglePitchRad* rad2deg};

}


