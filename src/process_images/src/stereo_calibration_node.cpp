// Stereo camera calibration node.
// Usage: ros2 run process_images stereo_calibration_node --ros-args
//          -p square_size:=0.025 -p output_file:=/path/to/stereo_calibration.yaml
//
// Controls (click the OpenCV window first):
//   SPACE  — capture the current frame pair (must detect corners in both cameras)
//   C      — run calibration and save (requires min_captures valid pairs)
//   Q/ESC  — quit without saving

#include "rclcpp/rclcpp.hpp"
#include <opencv2/opencv.hpp>
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.h"
#include <cmath>
#include <string>
#include <vector>

class StereocalNode : public rclcpp::Node
{
public:
  StereocalNode()
  : Node("stereo_calibration_node")
  {
    this->declare_parameter("left_camera_topic",  "camera/left/image_raw");
    this->declare_parameter("right_camera_topic", "camera/right/image_raw");
    this->declare_parameter("board_width",  9);
    this->declare_parameter("board_height", 6);
    this->declare_parameter("square_size",  0.025);   // meters — measure before use!
    this->declare_parameter("min_captures", 20);
    this->declare_parameter("output_file",  "config/stereo_calibration.yaml");

    std::string left_topic  = this->get_parameter("left_camera_topic").as_string();
    std::string right_topic = this->get_parameter("right_camera_topic").as_string();
    board_size_  = cv::Size(
      this->get_parameter("board_width").as_int(),
      this->get_parameter("board_height").as_int());
    square_size_ = this->get_parameter("square_size").as_double();
    min_captures_ = this->get_parameter("min_captures").as_int();
    output_file_  = this->get_parameter("output_file").as_string();

    sub_left_ = this->create_subscription<sensor_msgs::msg::Image>(
      left_topic, 10,
      [this](const sensor_msgs::msg::Image::SharedPtr msg) {
        try {left_frame_ = cv_bridge::toCvCopy(msg, "bgr8")->image;} catch (...) {}
      });

    sub_right_ = this->create_subscription<sensor_msgs::msg::Image>(
      right_topic, 10,
      [this](const sensor_msgs::msg::Image::SharedPtr msg) {
        try {right_frame_ = cv_bridge::toCvCopy(msg, "bgr8")->image;} catch (...) {}
      });

    RCLCPP_INFO(this->get_logger(),
      "Stereo calibration ready | Board: %dx%d | Square: %.4f m | Min captures: %d",
      board_size_.width, board_size_.height, square_size_, min_captures_);
    RCLCPP_INFO(this->get_logger(),
      "Controls: SPACE=capture  C=calibrate+save  Q/ESC=quit");
  }

  // Called from main loop each tick. Returns true when the node should exit.
  bool update()
  {
    draw_display();
    int key = cv::waitKey(30) & 0xFF;

    if (key == ' ') {
      capture_pair();
    } else if (key == 'c' || key == 'C') {
      if (static_cast<int>(img_points_left_.size()) >= min_captures_) {
        run_calibration();
        return true;
      } else {
        RCLCPP_WARN(this->get_logger(),
          "Need %d captures, have %zu — keep going",
          min_captures_, img_points_left_.size());
      }
    } else if (key == 'q' || key == 'Q' || key == 27) {
      RCLCPP_INFO(this->get_logger(), "Quitting without saving.");
      return true;
    }
    return false;
  }

private:
  void draw_display()
  {
    if (left_frame_.empty() || right_frame_.empty()) {
      cv::Mat placeholder = cv::Mat::zeros(240, 640, CV_8UC3);
      cv::putText(placeholder, "Waiting for camera topics...", {10, 120},
        cv::FONT_HERSHEY_SIMPLEX, 0.7, {255, 255, 255}, 2);
      cv::imshow("Stereo Calibration", placeholder);
      return;
    }

    cv::Mat disp_l = left_frame_.clone();
    cv::Mat disp_r = right_frame_.clone();

    // Live corner preview
    std::vector<cv::Point2f> corners_l, corners_r;
    bool found_l = cv::findChessboardCorners(
      disp_l, board_size_, corners_l, cv::CALIB_CB_FAST_CHECK);
    bool found_r = cv::findChessboardCorners(
      disp_r, board_size_, corners_r, cv::CALIB_CB_FAST_CHECK);
    cv::drawChessboardCorners(disp_l, board_size_, corners_l, found_l);
    cv::drawChessboardCorners(disp_r, board_size_, corners_r, found_r);

    // Status text
    std::string count_str = "Captures: " +
      std::to_string(img_points_left_.size()) + " / " +
      std::to_string(min_captures_);
    cv::putText(disp_l, count_str, {10, 30},
      cv::FONT_HERSHEY_SIMPLEX, 0.7, {0, 255, 255}, 2);
    cv::putText(disp_l, found_l ? "L: OK" : "L: --", {10, 60},
      cv::FONT_HERSHEY_SIMPLEX, 0.7,
      found_l ? cv::Scalar(0, 255, 0) : cv::Scalar(0, 0, 255), 2);
    cv::putText(disp_r, found_r ? "R: OK" : "R: --", {10, 60},
      cv::FONT_HERSHEY_SIMPLEX, 0.7,
      found_r ? cv::Scalar(0, 255, 0) : cv::Scalar(0, 0, 255), 2);

    // Resize right frame to match left if needed before concatenating
    if (disp_l.rows != disp_r.rows) {
      cv::resize(disp_r, disp_r, disp_l.size());
    }

    cv::Mat combined;
    cv::hconcat(disp_l, disp_r, combined);
    cv::imshow("Stereo Calibration", combined);
  }

  void capture_pair()
  {
    if (left_frame_.empty() || right_frame_.empty()) {
      RCLCPP_WARN(this->get_logger(), "No frames available yet.");
      return;
    }

    cv::Mat gray_l, gray_r;
    cv::cvtColor(left_frame_,  gray_l, cv::COLOR_BGR2GRAY);
    cv::cvtColor(right_frame_, gray_r, cv::COLOR_BGR2GRAY);

    std::vector<cv::Point2f> corners_l, corners_r;
    bool found_l = cv::findChessboardCorners(gray_l, board_size_, corners_l);
    bool found_r = cv::findChessboardCorners(gray_r, board_size_, corners_r);

    if (!found_l || !found_r) {
      RCLCPP_WARN(this->get_logger(),
        "Corners not found in both frames (L:%d R:%d) — skipped", found_l, found_r);
      return;
    }

    cv::TermCriteria crit(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.001);
    cv::cornerSubPix(gray_l, corners_l, {11, 11}, {-1, -1}, crit);
    cv::cornerSubPix(gray_r, corners_r, {11, 11}, {-1, -1}, crit);

    img_points_left_.push_back(corners_l);
    img_points_right_.push_back(corners_r);
    img_size_ = gray_l.size();

    RCLCPP_INFO(this->get_logger(),
      "Captured pair %zu / %d",
      img_points_left_.size(), min_captures_);
  }

  void run_calibration()
  {
    RCLCPP_INFO(this->get_logger(),
      "Running calibration with %zu pairs...", img_points_left_.size());

    // 3-D corner positions in the checkerboard's own frame (z=0 plane)
    std::vector<cv::Point3f> obj_pts;
    for (int r = 0; r < board_size_.height; ++r) {
      for (int c = 0; c < board_size_.width; ++c) {
        obj_pts.push_back({
          static_cast<float>(c * square_size_),
          static_cast<float>(r * square_size_),
          0.0f});
      }
    }
    std::vector<std::vector<cv::Point3f>> obj_points(img_points_left_.size(), obj_pts);

    // Per-camera intrinsic calibration
    cv::Mat K_l = cv::Mat::eye(3, 3, CV_64F);
    cv::Mat K_r = cv::Mat::eye(3, 3, CV_64F);
    cv::Mat D_l, D_r;
    std::vector<cv::Mat> rvecs_l, tvecs_l, rvecs_r, tvecs_r;

    double rms_l = cv::calibrateCamera(
      obj_points, img_points_left_,  img_size_, K_l, D_l, rvecs_l, tvecs_l);
    double rms_r = cv::calibrateCamera(
      obj_points, img_points_right_, img_size_, K_r, D_r, rvecs_r, tvecs_r);

    RCLCPP_INFO(this->get_logger(),
      "Individual RMS — left: %.4f  right: %.4f", rms_l, rms_r);

    // Stereo extrinsic calibration (R, T between cameras)
    cv::Mat R, T, E, F;
    double rms_stereo = cv::stereoCalibrate(
      obj_points, img_points_left_, img_points_right_,
      K_l, D_l, K_r, D_r,
      img_size_, R, T, E, F,
      cv::CALIB_FIX_INTRINSIC);

    double baseline = cv::norm(T);
    RCLCPP_INFO(this->get_logger(),
      "Stereo RMS: %.4f  Baseline: %.4f m", rms_stereo, baseline);

    // Save results
    cv::FileStorage fs(output_file_, cv::FileStorage::WRITE);
    if (!fs.isOpened()) {
      RCLCPP_ERROR(this->get_logger(), "Cannot write to %s", output_file_.c_str());
      return;
    }

    fs << "left_camera" << "{";
    fs << "image_width"  << img_size_.width;
    fs << "image_height" << img_size_.height;
    fs << "camera_matrix" << K_l;
    fs << "distortion_coefficients" << D_l;
    fs << "}";

    fs << "right_camera" << "{";
    fs << "image_width"  << img_size_.width;
    fs << "image_height" << img_size_.height;
    fs << "camera_matrix" << K_r;
    fs << "distortion_coefficients" << D_r;
    fs << "}";

    fs << "stereo" << "{";
    fs << "rotation_matrix"    << R;
    fs << "translation_vector" << T;
    fs << "baseline_m"         << baseline;
    fs << "}";

    fs.release();
    RCLCPP_INFO(this->get_logger(), "Calibration saved to %s", output_file_.c_str());
  }

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_left_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_right_;

  cv::Mat left_frame_;
  cv::Mat right_frame_;
  cv::Size board_size_;
  cv::Size img_size_;
  double square_size_;
  int min_captures_;
  std::string output_file_;

  std::vector<std::vector<cv::Point2f>> img_points_left_;
  std::vector<std::vector<cv::Point2f>> img_points_right_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<StereocalNode>();

  // Run spin_some + display update in the same thread so cv::waitKey works
  while (rclcpp::ok()) {
    rclcpp::spin_some(node);
    if (node->update()) {break;}
  }

  cv::destroyAllWindows();
  rclcpp::shutdown();
  return 0;
}
