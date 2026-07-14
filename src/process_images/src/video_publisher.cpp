#include <chrono>
#include <memory>
#include <opencv2/opencv.hpp>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.h>

using namespace std::chrono_literals;


class VideoPublisher : public rclcpp::Node
{
public:
  VideoPublisher()
  : Node("video_publisher")
  {
    this->declare_parameter("video_path", "");

    path_ = this->get_parameter("video_path").as_string();
    if (path_.empty()) {
      RCLCPP_ERROR(this->get_logger(),
        "video_path parameter is required. Pass --ros-args -p video_path:=/path/to/file.mp4");
      return;
    }

    publisher_ = this->create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);

    cap_.open(path_);
    if (!cap_.isOpened()) {
      RCLCPP_ERROR(this->get_logger(), "Could not open video: %s", path_.c_str());
      return;
    }

    RCLCPP_INFO(this->get_logger(), "Opened video: %s", path_.c_str());
    timer_ = this->create_wall_timer(33ms, std::bind(&VideoPublisher::timer_callback, this));
  }

private:
  void timer_callback()
  {
    cv::Mat frame;

    if (cap_.read(frame)) {
      auto msg = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", frame).toImageMsg();
      publisher_->publish(*msg);
    } else {
      cap_.release();
      cap_.open(path_);
      RCLCPP_INFO(this->get_logger(), "Video looped.");
    }

  }

  cv::VideoCapture cap_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::string path_;

};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<VideoPublisher>());
  rclcpp::shutdown();
  return 0;
}
