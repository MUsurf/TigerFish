#include "process_images/marker_detector.hpp"


MarkerDetector::MarkerDetector(double focal_length, double actual_width)
: focal_length_(focal_length), actual_width_(actual_width) {}

MarkerResult MarkerDetector::find_markers(const cv::Mat & frame)
{
  MarkerResult result;
  result.found = false;   //has the marker been found


    //mask for the color - get the orange stuff
  cv::Mat hsv, mask;
  cv::cvtColor(frame, hsv, cv::COLOR_BGR2HSV);   //convert to HSV color scheme
  cv::inRange(hsv, cv::Scalar(hue_low, saturation_low, value_low),
    cv::Scalar(hue_high, saturation_high, value_high), mask);                                                                  //create the mask

    //perform dilation
  cv::Mat dilated;
  cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(11, 11));
  cv::dilate(mask, dilated, kernel);

    //get the contours from the image
    // RETR_EXTERNAL: only retrieve extreme outer contours (ignore contours of holes IN the object)
    // CHAIN_APPROX_SIMPLE: remove redundant points in the contour
  std::vector<std::vector<cv::Point>> contours;
  cv::findContours(dilated, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

  for(const auto & contour: contours) {
    double area = cv::contourArea(contour);

    if(area > 600) {     //noise detection
      cv::RotatedRect rect = cv::minAreaRect(contour);

            // calculate some general values: width, height, aspect ration, rectangle area, extent, etc
      float w = rect.size.width;
      float h = rect.size.height;
      float aspect_ratio = std::max(w, h) / std::min(w, h);
      float rect_area = w * h;
      float extent = area / rect_area;     // how much space a specific object occupies compared to the surrounding bounding box
            // float pixel_length = std::max(rect.size.width, rect.size.height);
      bool is_close = (area > (frame.rows * frame.cols * 0.1));
      float K = 200.0;       //adjust this based on camer (K = realDistance * sqrt(areaInPixels))


            //position matters a lil bit, the lane markers "should be" on the floor and not in the upper frame
      if(rect.center.y < (frame.rows * 0.35)) {continue;}

            //check to make sure its not the gate (gates are verticle + skinny)
      if (h > (w * 1.5) && aspect_ratio > 2.0) {continue;}

            //check if the aspect ratio is correct - note that we can be close to the markers which means they aren't always that perfect shape
      if (!is_close && aspect_ratio < 1.5) {continue;}     // aspect ratio is wrong and we aren't close
      if (aspect_ratio > 10.0) {continue;}     // too thin


            //solidarity filter: analyze local pixel neighborhoods to preserve only the correct edges (ignore narrow/false edges)
      if(extent < 0.3) {continue;}


      result.contour = contour;
      result.center = rect.center;
      result.found = true;
      result.depth = K / std::sqrt(area);
      result.norm_position.x = (rect.center.x - (frame.cols / 2.0)) / (frame.cols / 2.0);
      result.norm_position.y = (rect.center.y - (frame.rows / 2.0)) / (frame.rows / 2.0);
      result.angle = rect.angle;
      break;

    }
  }

  return result;
}


void MarkerDetector::visualize_markers(cv::Mat & display_frame, const MarkerResult & result)
{
  if(result.found == true) {
    cv::drawContours(display_frame, std::vector<std::vector<cv::Point>>{result.contour}, -1,
      cv::Scalar(0, 255, 0), 2);                                                                                            //raw contour in green

    std::vector<cv::Point> hull;
    cv::convexHull(result.contour, hull);
    cv::drawContours(display_frame, std::vector<std::vector<cv::Point>>{hull}, -1,
      cv::Scalar(0, 0, 255), 2);                                                                                  // mark the hull in red

    cv::drawMarker(display_frame, result.center, cv::Scalar(255, 0, 0), cv::MARKER_CROSS, 20, 2);     //mark center in blue crosshair


    std::string depthTxt = "DEPTH: " + std::to_string(result.depth).substr(0, 4) + "m";
    cv::putText(display_frame, depthTxt, cv::Point(50, 50), cv::FONT_HERSHEY_SIMPLEX, 1,
      cv::Scalar(255, 255, 255), 2);

    std::string angleTxt = "Angle: " + std::to_string(result.angle).substr(0, 4) + "m";
    cv::putText(display_frame, angleTxt, cv::Point(50, 90), cv::FONT_HERSHEY_SIMPLEX, 1,
      cv::Scalar(255, 255, 255), 2);
  }
}
