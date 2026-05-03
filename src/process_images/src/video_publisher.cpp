#include <chrono>
#include <memory>
#include <opencv2/opencv.hpp>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.h>

//NOTE: this currently is meant for testing with mp4s
// to modify this for the actual sub, we may want to look into intra-process communication to avoid making copies of video
// currently it makes full copies!

using namespace std::chrono_literals;


class VideoPublisher : public rclcpp::Node
{
public:
  VideoPublisher()
  : Node("video_publisher")
  {
    //setup
    publisher_ = this->create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);

    //mp4 setup - update path to follow what is on your PC
    cap_.open("/home/ros2_ws/src/src/TestImages/RoboSub2022CourseWalkThrough.mp4");

    // check that we opened the mp4 correctly
    if (!cap_.isOpened()) {
      RCLCPP_ERROR(
        this->get_logger(),
        "MP4 video in video publisher not able to be opened. -_(-_-)_-");
      return;
    }

    //timer setup for how often the video is published
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
