#ifndef IMG_PREPROCESSING_HPP
#define IMG_PREPROCESSING_HPP

// libraries
#include <opencv2/opencv.hpp>

namespace process_images
{
class img_preprocesser
{
public:
  //constructor - define the CLAHE clipping limit as well as the kernel to use
  img_preprocesser(
    double CLAHE_clip_lim = 2.0, cv::Size tile_grid_size = cv::Size(8, 8),
    double gamma_ = 0.7);

  // define the functions that will be used to improve the image
  void CLAHE_Improve(const cv::Mat & input_img, cv::Mat & output_img);
  void color_enhance(const cv::Mat & input_img, cv::Mat & output_img);
  void gamma_correction(const cv::Mat & input_img, cv::Mat & output_img);
  void sharpness_correction(const cv::Mat & input_img, cv::Mat & output_img);

  // // define a function to do all of the improvements at once - convenience function
  void all_preprocessing(const cv::Mat & input_img, cv::Mat & output_img);

private:
  cv::Ptr<cv::CLAHE> clahe_preprocessor_;
  cv::Mat gamma_lut_;           //used for gamma correction
};

} // namespace process_images

#endif // IMG_PREPROCESSING_HPP
