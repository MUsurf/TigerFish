#include "process_images/img_preprocessing.hpp"

namespace process_images
{
    // Constructor
img_preprocesser::img_preprocesser(double CLAHE_clip_lim, cv::Size tile_grid_size, double gamma_)
{
  clahe_preprocessor_ = cv::createCLAHE(CLAHE_clip_lim, tile_grid_size);

  gamma_lut_ = cv::Mat(1, 256, CV_8U);
  uchar * p = gamma_lut_.ptr();
  for(int i = 0; i < 256; ++i) {
    p[i] = cv::saturate_cast<uchar>(pow(i / 255.0, gamma_) * 255.0);
  }
}

        // define the functions that will be used to improve the image ////////////////////

        //CLAHE transform is important in that it will increase the contrast on the image making it a bit clearer
void img_preprocesser::CLAHE_Improve(const cv::Mat & input_img, cv::Mat & output_img)
{
  if(input_img.empty()) {return;}         //image is bad NOTE: it may be helpful in the future to return an error of some kind

            // CLAHE pre prep. convert to LAB to use the lightness channel for clahe //
            // this is important since CLAHE should just be targeting lightness tbh ^_^
  cv::Mat lab_image;
  cv::cvtColor(input_img, lab_image, cv::COLOR_BGR2Lab);           //convert to LAB space

  std::vector<cv::Mat> channels(3);
  cv::split(lab_image, channels);            //get channels

            // actually apply the CLAHE transformation //
  clahe_preprocessor_->apply(channels[0], channels[0]);

            // reform the image -> the L channel was updated so the original image needs to be updated //
  cv::merge(channels, lab_image);

            // convert the image back to bgr instead of LAB //
  cv::cvtColor(lab_image, output_img, cv::COLOR_Lab2BGR);

}

        // color enhance =========================================================================================================================
        // so the idea of this is that underwater images tend to be very green or blue. This needs to be corrected in order to get a good result
        // one way to do that is the grey world assumption or grey world white balancing.
        // The idea of grey world is that the average of all of the pixels (each pixel is just some color value) in the image should be grey
        // xphoto is one way of using a built in grey world, but to decrease number of libraries pulled in this can be done manually.
        // in addition, since this is c++ this is likely going to be equivalent or just as fast
void img_preprocesser::color_enhance(const cv::Mat & input_img, cv::Mat & output_img)
{
            //split channels out (b g r)
  std::vector<cv::Mat> channels;
  cv::split(input_img, channels);

            //Calculate the means
            // again the average of all these should be a resulting grey value
            // note, channel 0 = blue, channel 1 = green, channel 2 = red (OpenCV stores in bgr order instead of rgb)
  double b_mean = cv::mean(channels[0])[0];
  double g_mean = cv::mean(channels[1])[0];
  double r_mean = cv::mean(channels[2])[0];

  double total_mean = (b_mean + g_mean + r_mean) / 3.0;         // gets the avg of all the channels

            // now that the actual mean is calculated, the channels can be scaled to the total mean (this will result in that grey average)
  channels[0] *= std::min((total_mean / std::max(b_mean, 1.0)), 0.8);
  channels[1] *= (total_mean / std::max(g_mean, 1.0));
            // channels[2] *= (total_mean / r_mean);
  channels[2] *= std::min(total_mean / std::max(r_mean, 20.0), 1.2);


  for(int i = 0; i < 3; i++) {
            // This truncates values at 255
    cv::threshold(channels[i], channels[i], 255, 255, cv::THRESH_TRUNC);

            // Convert back to 8-bit unsigned integers just to be safe
    channels[i].convertTo(channels[i], CV_8U);
  }


            // the channels should be re-merged to form the final image.
  cv::merge(channels, output_img);


}

        //underwater images tend to be dark so gamma correction is important for brightening the image.
        // see the bottom of this article: https://docs.opencv.org/4.x/d3/dc1/tutorial_basic_linear_transform.html
void img_preprocesser::gamma_correction(const cv::Mat & input_img, cv::Mat & output_img)
{
  cv::LUT(input_img, gamma_lut_, output_img);

}

        // after all the other correction some sharpness is lost, so unsharp processing can fix that to some degree
void img_preprocesser::sharpness_correction(const cv::Mat & input_img, cv::Mat & output_img)
{
  cv::Mat blurred;

            // blur again (for the unsharp mask)
  cv::GaussianBlur(input_img, blurred, cv::Size(0, 0), 3);
            //subtract the original and the blurred to get the sharpened image
  cv::addWeighted(input_img, 1.5, blurred, -0.5, 0, output_img);

}

        // // define a function to do all of the improvements at once - convenience function
void img_preprocesser::all_preprocessing(const cv::Mat & input_img, cv::Mat & output_img)
{
  cv::Mat temp;
  cv::Mat temp2;
  cv::Mat temp3;

            //blur the image a lil bit
  cv::GaussianBlur(input_img, temp, cv::Size(3, 3), 0);

            // gamma correction -> color correction -> contrast enhancement ->unsharp mask
  gamma_correction(input_img, temp);
  color_enhance(temp, temp2);
  CLAHE_Improve(temp2, temp3);
  sharpness_correction(temp3, output_img);

}
} //namespace process_images
