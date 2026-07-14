// Mono camera calibration node.
// Usage: ros2 run process_images mono_calibration_node --ros-args
//          -p video_path:=/path/to/video.mp4 -p square_size:=0.025
//
// Single camera only — there is no stereo extrinsic solve here, so the
// calibration itself is just one linear calibrateCamera() pass, unlike
// stereo_calibration_node which chains a stereoCalibrate() on top for
// R/T between two cameras.
//
// Controls (click the OpenCV window first):
//   SPACE  — capture the current frame (must detect checkerboard corners)
//   C      — run calibration and save (requires min_captures valid frames)
//   Q/ESC  — quit without saving

#include "rclcpp/rclcpp.hpp"
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

class MonocalNode : public rclcpp::Node
{
public:
  MonocalNode()
  : Node("mono_calibration_node")
  {
    this->declare_parameter("video_path", "");
    this->declare_parameter("board_width",  6);
    this->declare_parameter("board_height", 8);
    this->declare_parameter("square_size",  0.08);   // meters — measure before use!
    this->declare_parameter("min_captures", 20);
    this->declare_parameter("output_file",  "src/src/process_images/config/mono_calibration.yaml");

    video_path_   = this->get_parameter("video_path").as_string();
    board_size_   = cv::Size(
      this->get_parameter("board_width").as_int(),
      this->get_parameter("board_height").as_int());
    square_size_  = this->get_parameter("square_size").as_double();
    min_captures_ = this->get_parameter("min_captures").as_int();
    output_file_  = this->get_parameter("output_file").as_string();

    if (video_path_.empty()) {
      RCLCPP_ERROR(this->get_logger(),
        "video_path parameter is required. Pass --ros-args -p video_path:=/path/to/file.mp4");
      return;
    }

    cap_.open(video_path_);
    if (!cap_.isOpened()) {
      RCLCPP_ERROR(this->get_logger(), "Could not open video: %s", video_path_.c_str());
      return;
    }

    RCLCPP_INFO(this->get_logger(),
      "Mono calibration ready | Video: %s | Board: %dx%d | Square: %.4f m | Min captures: %d",
      video_path_.c_str(), board_size_.width, board_size_.height, square_size_, min_captures_);
    RCLCPP_INFO(this->get_logger(),
      "Controls: SPACE=capture  C=calibrate+save  Q/ESC=quit");
  }

  // Called from main loop each tick. Returns true when the node should exit.
  bool update()
  {
    read_frame();
    draw_display();
    int key = cv::waitKey(30) & 0xFF;

    if (key == ' ') {
      capture_frame();
    } else if (key == 'c' || key == 'C') {
      if (static_cast<int>(img_points_.size()) >= min_captures_) {
        run_calibration();
        return true;
      } else {
        RCLCPP_WARN(this->get_logger(),
          "Need %d captures, have %zu — keep going", min_captures_, img_points_.size());
      }
    } else if (key == 'q' || key == 'Q' || key == 27) {
      RCLCPP_INFO(this->get_logger(), "Quitting without saving.");
      return true;
    }
    return false;
  }

private:
  void read_frame()
  {
    if (!cap_.isOpened()) {return;}
    cv::Mat f;
    if (cap_.read(f)) {
      frame_ = f;
    } else {
      cap_.set(cv::CAP_PROP_POS_FRAMES, 0);
    }
  }

  void draw_display()
  {
    if (frame_.empty()) {
      cv::Mat placeholder = cv::Mat::zeros(240, 320, CV_8UC3);
      cv::putText(placeholder, "Waiting for video...", {10, 120},
        cv::FONT_HERSHEY_SIMPLEX, 0.7, {255, 255, 255}, 2);
      cv::imshow("Mono Calibration", placeholder);
      return;
    }

    cv::Mat disp = frame_.clone();

    std::vector<cv::Point2f> corners;
    bool found = cv::findChessboardCorners(disp, board_size_, corners, cv::CALIB_CB_FAST_CHECK);
    cv::drawChessboardCorners(disp, board_size_, corners, found);

    std::string count_str = "Captures: " + std::to_string(img_points_.size()) +
      " / " + std::to_string(min_captures_);
    cv::putText(disp, count_str, {10, 30},
      cv::FONT_HERSHEY_SIMPLEX, 0.7, {0, 255, 255}, 2);
    cv::putText(disp, found ? "DETECTED" : "--", {10, 60},
      cv::FONT_HERSHEY_SIMPLEX, 0.7,
      found ? cv::Scalar(0, 255, 0) : cv::Scalar(0, 0, 255), 2);

    cv::imshow("Mono Calibration", disp);
  }

  void capture_frame()
  {
    if (frame_.empty()) {
      RCLCPP_WARN(this->get_logger(), "No frame available yet.");
      return;
    }

    cv::Mat gray;
    cv::cvtColor(frame_, gray, cv::COLOR_BGR2GRAY);
    img_size_ = gray.size();

    std::vector<cv::Point2f> corners;
    bool found = cv::findChessboardCorners(gray, board_size_, corners);
    if (!found) {
      RCLCPP_WARN(this->get_logger(), "Corners not found — skipped");
      return;
    }

    cv::TermCriteria crit(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.001);
    cv::cornerSubPix(gray, corners, {11, 11}, {-1, -1}, crit);

    img_points_.push_back(corners);
    RCLCPP_INFO(this->get_logger(),
      "Captured checkerboard frame %zu / %d", img_points_.size(), min_captures_);
  }

  void run_calibration()
  {
    RCLCPP_INFO(this->get_logger(),
      "Running checkerboard calibration with %zu frames...", img_points_.size());

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
    std::vector<std::vector<cv::Point3f>> obj_points(img_points_.size(), obj_pts);

    cv::Mat K = cv::Mat::eye(3, 3, CV_64F);
    cv::Mat D;
    std::vector<cv::Mat> rvecs, tvecs;
    double rms = cv::calibrateCamera(obj_points, img_points_, img_size_, K, D, rvecs, tvecs);

    RCLCPP_INFO(this->get_logger(), "Calibration RMS: %.4f", rms);

    cv::FileStorage fs(output_file_, cv::FileStorage::WRITE);
    if (!fs.isOpened()) {
      RCLCPP_ERROR(this->get_logger(), "Cannot write to %s", output_file_.c_str());
      return;
    }

    fs << "camera" << "{";
    fs << "image_width"  << img_size_.width;
    fs << "image_height" << img_size_.height;
    fs << "camera_matrix" << K;
    fs << "distortion_coefficients" << D;
    fs << "reprojection_error" << rms;
    fs << "}";

    fs.release();
    RCLCPP_INFO(this->get_logger(), "Calibration saved to %s", output_file_.c_str());
  }

  cv::VideoCapture cap_;
  std::string video_path_;
  cv::Mat frame_;
  cv::Size board_size_;
  cv::Size img_size_;
  double square_size_;
  int min_captures_;
  std::string output_file_;

  std::vector<std::vector<cv::Point2f>> img_points_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<MonocalNode>();

  // Run spin_some + display update in the same thread so cv::waitKey works
  while (rclcpp::ok()) {
    rclcpp::spin_some(node);
    if (node->update()) {break;}
  }

  cv::destroyAllWindows();
  rclcpp::shutdown();
  return 0;
}
