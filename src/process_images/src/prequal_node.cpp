#include "rclcpp/rclcpp.hpp"
#include <memory>
#include <opencv2/opencv.hpp>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

#include "process_images/img_preprocessing.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.h"
#include "process_images/prequal_line.hpp"
#include "process_images/prequal_helper.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "geometry_msgs/msg/vector3.hpp"


class prequal_node : public rclcpp::Node
{
public:
  prequal_node()
  : Node("prequal_node")
  {
    // preprocessing setup
    cv::Size kernel = cv::Size(16, 16);
    float clipLimit = 2.0;


    preprocesser_ = std::make_unique<process_images::img_preprocesser>(clipLimit, kernel);

    // create a publisher for the video feed
    publisher_ = this->create_publisher<sensor_msgs::msg::Image>(
      "camera/image_processed", 10);
    // subscriber
    subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
      "topic_camera_image", 10,
      std::bind(&prequal_node::image_callback, this, std::placeholders::_1));
    info_sub_ = this->create_subscription<sensor_msgs::msg::CameraInfo>(
        "camera/camera_info", 10,
        std::bind(&prequal_node::info_callback, this, std::placeholders::_1));
    coords_pub_ = this->create_publisher<geometry_msgs::msg::Vector3>("path/pole_coords", 10);
    

    // logging
    RCLCPP_INFO(this->get_logger(), "Prequal img Node ready for images...");
  }

  // destructor
  ~prequal_node()
  {
    if (is_writer_initialized_) {
      video_writer_.release();
      RCLCPP_INFO(this->get_logger(), "Video file finalized and saved.");
    }
  }

private:
  void info_callback(const sensor_msgs::msg::CameraInfo::SharedPtr info){
        camera_matrix_ = (cv::Mat_<double>(3, 3) <<
            info->k[0], info->k[1], info->k[2],
            info->k[3], info->k[4], info->k[5],
            info->k[6], info->k[7], info->k[8]);
        is_calibrated_ = true;

  }


  void WriteVideo(const cv::Mat & processed_frame)
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
    if (!is_writer_initialized_) {
      //get current time:
      auto now = std::chrono::system_clock::now();
      auto in_time_t = std::chrono::system_clock::to_time_t(now);

      // format the time
      std::stringstream ss;
      ss << "/home/ros2_ws/src/output_images/processed_vid/prequal_"
        << std::put_time(std::localtime(&in_time_t), "%Y%m%d_%H%M%S")
        << ".mp4";

      std::string filename =ss.str();

      int fourcc = cv::VideoWriter::fourcc('m', 'p', '4', 'v');
      video_writer_.open(
        filename,
        fourcc, 30.0, processed_frame.size());

      if(video_writer_.isOpened()){
        RCLCPP_INFO(this->get_logger(), "Started recording to: %s", filename.c_str());
        is_writer_initialized_ = true;
        
      }
      else{
        RCLCPP_ERROR(this->get_logger(), "Failed to open video writer in prequal node!");
      }
    }
    if (is_writer_initialized_){
      video_writer_.write(processed_frame);
    }
  }

  cv::Mat StitchImg(cv::Mat & raw_frame, cv::Mat & processed_frame)
  {
    // stitch together original feed + raw feed
    cv::Mat combined_frame;
    if (raw_frame.rows == processed_frame.rows && raw_frame.cols == processed_frame.cols) {
      std::vector<cv::Mat> images = {raw_frame, processed_frame};
      cv::hconcat(images, combined_frame);
    } else {
      combined_frame = processed_frame;
    }

    return combined_frame;
  }
  // image callback
  void image_callback(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    try {
      // convert ros to opencv
      cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, "bgr8");
      cv::Mat raw_frame = cv_ptr->image;
      cv::Mat processed_frame;
      cv::Mat mask;

      // improvements
      preprocesser_->all_preprocessing(raw_frame, processed_frame);

      //get the color mask
      applyColorHSVMask(processed_frame, mask,PoleLow1, PoleHigh1, PoleLow2, PoleHigh2);

      PoleShapeData pole = getPoleShape(mask);
      geometry_msgs::msg::Vector3 coord_msg;

      coord_msg.z = 0; //0 = no pole
      coord_msg.x = 0;
      coord_msg.y = 0;

      if(pole.detected && is_calibrated_){
        MarkerAngles angles = getAnglesToTop(pole, camera_matrix_);

        //publish angle stuff
        coord_msg.x = angles.yaw;
        coord_msg.y = angles.pitch;
        coord_msg.z = 1; // 1 = pole detected

        //ddraw the pole detection
        cv::circle(processed_frame, pole.centerTop, 10, cv::Scalar(0,255, 0), -1);
        

      }
      coords_pub_->publish(coord_msg);

      // stitch images
      cv::Mat combined_frame = StitchImg(raw_frame, processed_frame);
      cv::Mat ImgToWrite = combined_frame;

      WriteVideo(combined_frame);

      // in addition to writing the vid it will be published (to view in realtime)
    //   std_msgs::msg::Header header = msg->header; // timestamp
      cv_bridge::CvImage img_bridge = cv_bridge::CvImage(msg->header, "bgr8", combined_frame);
      publisher_->publish(*img_bridge.toImageMsg());
    } catch (cv_bridge::Exception & e) {
      RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
    }
  }

  // variables  ///////////////////////////////////////////////
  std::unique_ptr<process_images::img_preprocesser> preprocesser_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr subscription_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
  rclcpp::Publisher<geometry_msgs::msg::Vector3>::SharedPtr coords_pub_;
  // camera init vars
  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr info_sub_;
  cv::Mat camera_matrix_;
  bool is_calibrated_ = false;

  // Pole detection colors
  std::array<float,3> PoleLow1 = {0.0f, 76.5f, 76.5f};
  std::array<float,3> PoleLow2 = {157.5f, 76.5f, 76.5f};
  std::array<float,3> PoleHigh1 = {20.0f, 255.0f, 255.0f};
  std::array<float,3> PoleHigh2 = {179.0f, 255.0f, 255.0f};

  //vid writing vars
  cv::VideoWriter video_writer_;
  bool is_writer_initialized_ = false;

  
};

int main(int argc, char * argv[])
{
  // init ros
  rclcpp::init(argc, argv);

  // spin - keep the node active
  rclcpp::spin(std::make_shared<prequal_node>());

  // shutdown
  rclcpp::shutdown();
  return 0;
}
