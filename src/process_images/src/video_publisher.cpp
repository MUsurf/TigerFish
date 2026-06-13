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

    std::string path = this->get_parameter("video_path").as_string();
    if (path.empty()) {
      RCLCPP_ERROR(this->get_logger(),
        "video_path parameter is required. Pass --ros-args -p video_path:=/path/to/file.mp4");
      return;
    }

    publisher_ = this->create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);

    cap_.open(path);
    if (!cap_.isOpened()) {
      RCLCPP_ERROR(this->get_logger(), "Could not open video: %s", path.c_str());
      return;
    }

    RCLCPP_INFO(this->get_logger(), "Opened video: %s", path.c_str());
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
      //reset video
      cap_.set(cv::CAP_PROP_POS_FRAMES, 0);
      RCLCPP_INFO(this->get_logger(), "Video looped.");
    }
  }

  cv::VideoCapture cap_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;

};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<VideoPublisher>());
  rclcpp::shutdown();
  return 0;
}
