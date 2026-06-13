#include "rclcpp/rclcpp.hpp"
#include <memory>
#include <string>
#include <opencv2/opencv.hpp>
#include "sensor_msgs/msg/image.hpp"
#include "geometry_msgs/msg/pose2_d.hpp"
#include "cv_bridge/cv_bridge.h"
#include "process_images/img_preprocessing.hpp"
#include "process_images/marker_detector.hpp"
#include "process_images/gate_detection.hpp"

class processImgNode : public rclcpp::Node
{
public:
  processImgNode()
  : Node("process_img_node")
  {
    // Parameters
    this->declare_parameter("stereo_calibration_file", "");
    this->declare_parameter("marker_actual_width", 1.2);
    this->declare_parameter("left_camera_topic", "camera/left/image_raw");
    this->declare_parameter("right_camera_topic", "camera/right/image_raw");
    this->declare_parameter("hsv_h_low", 8);
    this->declare_parameter("hsv_h_high", 22);
    this->declare_parameter("hsv_s_low", 110);
    this->declare_parameter("hsv_s_high", 255);
    this->declare_parameter("hsv_v_low", 80);
    this->declare_parameter("hsv_v_high", 255);
    this->declare_parameter("marker_min_area", 600.0);
    this->declare_parameter("output_video_path", "");

    std::string cal_file =
      this->get_parameter("stereo_calibration_file").as_string();
    double marker_width =
      this->get_parameter("marker_actual_width").as_double();
    std::string left_topic =
      this->get_parameter("left_camera_topic").as_string();
    std::string right_topic =
      this->get_parameter("right_camera_topic").as_string();
    int h_low  = this->get_parameter("hsv_h_low").as_int();
    int h_high = this->get_parameter("hsv_h_high").as_int();
    int s_low  = this->get_parameter("hsv_s_low").as_int();
    int s_high = this->get_parameter("hsv_s_high").as_int();
    int v_low  = this->get_parameter("hsv_v_low").as_int();
    int v_high = this->get_parameter("hsv_v_high").as_int();
    double min_area =
      this->get_parameter("marker_min_area").as_double();
    output_video_path_ =
      this->get_parameter("output_video_path").as_string();

    // Load focal lengths from stereo calibration file if provided
    double focal_left = 600.0;
    double focal_right = 600.0;
    if (!cal_file.empty()) {
      cv::FileStorage fs(cal_file, cv::FileStorage::READ);
      if (fs.isOpened()) {
        cv::Mat K_l, K_r;
        fs["left_camera"]["camera_matrix"] >> K_l;
        fs["right_camera"]["camera_matrix"] >> K_r;
        if (!K_l.empty()) {focal_left  = K_l.at<double>(0, 0);}
        if (!K_r.empty()) {focal_right = K_r.at<double>(0, 0);}
        RCLCPP_INFO(
          this->get_logger(), "Loaded calibration: fx_l=%.1f fx_r=%.1f",
          focal_left, focal_right);
      } else {
        RCLCPP_WARN(
          this->get_logger(), "Cannot open calibration file: %s — using defaults",
          cal_file.c_str());
      }
    }

    // Preprocessing (stateless, shared between both cameras)
    preprocesser_ = std::make_unique<process_images::img_preprocesser>(2.0, cv::Size(16, 16));

    // One detector per camera so each can have its own focal length
    left_detector_  = std::make_unique<MarkerDetector>(focal_left,  marker_width);
    right_detector_ = std::make_unique<MarkerDetector>(focal_right, marker_width);
    left_detector_->setHSVBounds(h_low, h_high, s_low, s_high, v_low, v_high);
    right_detector_->setHSVBounds(h_low, h_high, s_low, s_high, v_low, v_high);
    left_detector_->setMinArea(min_area);
    right_detector_->setMinArea(min_area);

    // Publishers
    //   primary: best (largest) detection across both cameras
    //   left / right: per-camera results (published only when found)
    //   debug_image: both processed frames side by side
    pub_primary_ = this->create_publisher<geometry_msgs::msg::Pose2D>(
      "markers/path_marker", 10);
    pub_left_ = this->create_publisher<geometry_msgs::msg::Pose2D>(
      "markers/left/path_marker", 10);
    pub_right_ = this->create_publisher<geometry_msgs::msg::Pose2D>(
      "markers/right/path_marker", 10);
    pub_debug_ = this->create_publisher<sensor_msgs::msg::Image>(
      "markers/debug_image", 10);

    // Subscriptions
    sub_left_ = this->create_subscription<sensor_msgs::msg::Image>(
      left_topic, 10,
      std::bind(&processImgNode::left_callback, this, std::placeholders::_1));
    sub_right_ = this->create_subscription<sensor_msgs::msg::Image>(
      right_topic, 10,
      std::bind(&processImgNode::right_callback, this, std::placeholders::_1));

    RCLCPP_INFO(
      this->get_logger(),
      "processImgNode ready — left: %s  right: %s",
      left_topic.c_str(), right_topic.c_str());
  }

  ~processImgNode()
  {
    if (video_writer_.isOpened()) {
      video_writer_.release();
      RCLCPP_INFO(this->get_logger(), "Video writer released.");
    }
  }

private:
  // Processes one camera frame: preprocess → detect → visualize → cache → publish per-camera
  void process_camera(
    const sensor_msgs::msg::Image::SharedPtr & msg,
    MarkerDetector & detector,
    cv::Mat & cached_frame,
    MarkerResult & cached_result,
    rclcpp::Publisher<geometry_msgs::msg::Pose2D>::SharedPtr & per_cam_pub)
  {
    try {
      cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, "bgr8");
      cv::Mat raw_frame = cv_ptr->image;
      cv::Mat processed_frame;
      preprocesser_->all_preprocessing(raw_frame, processed_frame);

      MarkerResult result = detector.find_markers(processed_frame);
      detector.visualize_markers(processed_frame, result);

      cached_frame  = processed_frame;
      cached_result = result;

      if (result.found) {
        geometry_msgs::msg::Pose2D pose;
        pose.x     = result.center.x;
        pose.y     = result.center.y;
        pose.theta = result.angle;
        per_cam_pub->publish(pose);
      }
    } catch (const cv_bridge::Exception & e) {
      RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
    }
  }

  void left_callback(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    process_camera(msg, *left_detector_, left_frame_, left_result_, pub_left_);
    publish_best();
    publish_debug(msg->header);
  }

  void right_callback(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    process_camera(msg, *right_detector_, right_frame_, right_result_, pub_right_);
    publish_best();
    publish_debug(msg->header);
  }

  // Publish the detection with the larger contour area as the primary result
  void publish_best()
  {
    const MarkerResult * best = nullptr;
    if (left_result_.found && right_result_.found) {
      best = (left_result_.area >= right_result_.area) ? &left_result_ : &right_result_;
    } else if (left_result_.found) {
      best = &left_result_;
    } else if (right_result_.found) {
      best = &right_result_;
    }

    if (best) {
      geometry_msgs::msg::Pose2D pose;
      pose.x     = best->center.x;
      pose.y     = best->center.y;
      pose.theta = best->angle;
      pub_primary_->publish(pose);
    }
  }

  // Publish side-by-side debug visualization and optionally write to video file
  void publish_debug(const std_msgs::msg::Header & header)
  {
    if (left_frame_.empty() && right_frame_.empty()) {return;}

    cv::Mat debug_frame;
    if (!left_frame_.empty() && !right_frame_.empty() &&
      left_frame_.rows == right_frame_.rows)
    {
      cv::hconcat(left_frame_, right_frame_, debug_frame);
    } else if (!left_frame_.empty()) {
      debug_frame = left_frame_;
    } else {
      debug_frame = right_frame_;
    }

    if (!output_video_path_.empty()) {
      if (!video_writer_.isOpened()) {
        int fourcc = cv::VideoWriter::fourcc('m', 'p', '4', 'v');
        video_writer_.open(output_video_path_, fourcc, 30.0, debug_frame.size());
      }
      video_writer_.write(debug_frame);
    }

    cv_bridge::CvImage img_bridge(header, "bgr8", debug_frame);
    pub_debug_->publish(*img_bridge.toImageMsg());
  }

  // Components
  std::unique_ptr<process_images::img_preprocesser> preprocesser_;
  std::unique_ptr<MarkerDetector> left_detector_;
  std::unique_ptr<MarkerDetector> right_detector_;

  // Subscriptions
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_left_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_right_;

  // Publishers
  rclcpp::Publisher<geometry_msgs::msg::Pose2D>::SharedPtr pub_primary_;
  rclcpp::Publisher<geometry_msgs::msg::Pose2D>::SharedPtr pub_left_;
  rclcpp::Publisher<geometry_msgs::msg::Pose2D>::SharedPtr pub_right_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_debug_;

  // Latest processed frames and results from each camera
  cv::Mat left_frame_;
  cv::Mat right_frame_;
  MarkerResult left_result_;
  MarkerResult right_result_;

  cv::VideoWriter video_writer_;
  std::string output_video_path_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<processImgNode>());
  rclcpp::shutdown();
  return 0;
}
