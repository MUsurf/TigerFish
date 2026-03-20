#include "rclcpp/rclcpp.hpp"
#include <memory>
#include <opencv2/opencv.hpp>
#include "process_images/img_preprocessing.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.hpp"
#include "process_images/marker_detector.hpp"
#include "process_images/goal_detection.hpp"

class processImgNode : public rclcpp::Node
{
public:
  processImgNode()
      : Node("process_img_node")
  {
    // preprocessing setup
    cv::Size kernel = cv::Size(16, 16);
    float clipLimit = 2.0;

    preprocesser_ = std::make_unique<process_images::img_preprocesser>(clipLimit, kernel);
    marker_detector_ = std::make_unique<MarkerDetector>(600.0, 1.2);
    goal_detector_ = std::make_unique<Goal_detection>();

    // create a publisher for the video feed
    publisher_ = this->create_publisher<sensor_msgs::msg::Image>(
        "camera/image_processed", 10);
    // subscriber
    subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
        "camera/image_raw", 10,
        std::bind(&processImgNode::image_callback, this, std::placeholders::_1));

    // logging
    RCLCPP_INFO(this->get_logger(), "processImgNode ready for images...");
  }

  // destructor
  ~processImgNode()
  {
    if (is_writer_initialized_)
    {
      video_writer_.release();
      RCLCPP_INFO(this->get_logger(), "Video file finalized and saved.");
    }
  }

private:
  void WriteVideo(const cv::Mat &processed_frame)
  {
    // Visualization ////////////////////////////////
    // So there are a couple ways to do this:
    // a) install x11 forwarding and use imshow (this is annoying)
    // b) write every ith frame to a folder
    // c) write the new video
    // It should be noted that these should not be active on the real sub :)

    // a) x11 forwarding option ////////////////////////////////
    // cv::imshow("Raw Feed", raw_frame);
    // cv::imshow("Processed Feed (CLAHE)", processed_frame);
    // cv::waitKey(1);
    ///////////////////////////////////////////////////////////

    // b) write every ith frame /////////////////////////////////////////////
    // static int frame_count = 0;
    // captures every "ith" frame (ie 30th frame)
    // const int ith_frame = 30;
    // if (frame_count % ith_frame == 0){
    //     std::string filename = "/home/ros2_ws/src/output_images/processed/frame_"+ std::to_string(frame_count)+ ".jpg";
    //     cv::imwrite(filename, processed_frame);

    //     std::string filename2 = "/home/ros2_ws/src/output_images/input/frame_"+ std::to_string(frame_count)+ ".jpg";
    //     cv::imwrite(filename, raw_frame);

    // }
    // frame_count++;
    ///////////////////////////////////////////////////////////////////////

    // c) write vid //////////////////////////////////////////////////////
    if (!is_writer_initialized_)
    {
      int fourcc = cv::VideoWriter::fourcc('m', 'p', '4', 'v');
      video_writer_.open("/home/ros2_ws/src/output_images/processed_vid/processed_output.mp4",
                         fourcc, 30.0, processed_frame.size());
      is_writer_initialized_ = true;
    }
    video_writer_.write(processed_frame);
  }

  cv::Mat StitchImg(cv::Mat &raw_frame, cv::Mat &processed_frame)
  {
    // stitch together original feed + raw feed
    cv::Mat combined_frame;
    if (raw_frame.rows == processed_frame.rows && raw_frame.cols == processed_frame.cols)
    {
      std::vector<cv::Mat> images = {raw_frame, processed_frame};
      cv::hconcat(images, combined_frame);
    }
    else
    {
      combined_frame = processed_frame;
    }

    return combined_frame;
  }
  // image callback
  void image_callback(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    try
    {
      // convert ros to opencv
      cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, "bgr8");
      cv::Mat raw_frame = cv_ptr->image;
      cv::Mat processed_frame;

      // improvements
      preprocesser_->all_preprocessing(raw_frame, processed_frame);


      // Test code stuff, comment out marker detection and uncomment goal detection to test, if both are up at the same time stuff will be overwritten

      // detect markers
      // MarkerResult marker_detector_result = marker_detector_->find_markers(processed_frame);
      // marker_detector_->visualize_markers(processed_frame, marker_detector_result);

      // add the line detection stuff here, pull in result
      GoalResult goal_result = goal_detector_->find_gate(processed_frame);
      goal_detector_->visualize_lines(processed_frame, goal_result);

      // stitch images
      cv::Mat combined_frame = StitchImg(raw_frame, processed_frame);

      // TODO: change this to be the version of the image that will be written + broadcast
      cv::Mat ImgToWrite = combined_frame;

      WriteVideo(combined_frame);

      // in addition to writing the vid it will be published (to view in realtime)
      std_msgs::msg::Header header = msg->header; // timestamp
      cv_bridge::CvImage img_bridge = cv_bridge::CvImage(header, "bgr8", processed_frame);
      publisher_->publish(*img_bridge.toImageMsg());
    }
    catch (cv_bridge::Exception &e)
    {
      RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
    }
  }

  // variables  ///////////////////////////////////////////////
  std::unique_ptr<process_images::img_preprocesser> preprocesser_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr subscription_;
  std::unique_ptr<MarkerDetector> marker_detector_;
  std::unique_ptr<Goal_detection> goal_detector_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;

  cv::VideoWriter video_writer_;
  bool is_writer_initialized_ = false;
};

int main(int argc, char *argv[])
{
  // init ros
  rclcpp::init(argc, argv);

  // spin - keep the node active
  rclcpp::spin(std::make_shared<processImgNode>());

  // shutdown
  rclcpp::shutdown();
  return 0;
}
