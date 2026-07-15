#include <gtest/gtest.h>
#include <cmath>

#include "process_images/triangulation.hpp"

namespace
{
// Typical 640x480 camera: principal point at image center.
cv::Mat make_camera_matrix(double fx, double fy, double cx, double cy)
{
  return (cv::Mat_<double>(3, 3) <<
    fx, 0.0, cx,
    0.0, fy, cy,
    0.0, 0.0, 1.0);
}

const double kFx = 600.0;
const double kFy = 580.0;
const double kCx = 320.0;
const double kCy = 240.0;
}  // namespace

class PixelToAngleTest : public ::testing::Test
{
protected:
  cv::Mat camera_matrix_ = make_camera_matrix(kFx, kFy, kCx, kCy);
};

TEST_F(PixelToAngleTest, PrincipalPointMapsToZeroAngles)
{
  cv::Point2d angle = pixel_to_angle(cv::Point2d(kCx, kCy), camera_matrix_);
  EXPECT_DOUBLE_EQ(angle.x, 0.0);
  EXPECT_DOUBLE_EQ(angle.y, 0.0);
}

TEST_F(PixelToAngleTest, MatchesAtan2Formula)
{
  cv::Point2d pixel(450.0, 100.0);
  cv::Point2d angle = pixel_to_angle(pixel, camera_matrix_);
  EXPECT_DOUBLE_EQ(angle.x, std::atan2(pixel.x - kCx, kFx));
  EXPECT_DOUBLE_EQ(angle.y, std::atan2(pixel.y - kCy, kFy));
}

TEST_F(PixelToAngleTest, SignConventions)
{
  // Right of center -> positive azimuth; left -> negative.
  EXPECT_GT(pixel_to_angle(cv::Point2d(kCx + 50.0, kCy), camera_matrix_).x, 0.0);
  EXPECT_LT(pixel_to_angle(cv::Point2d(kCx - 50.0, kCy), camera_matrix_).x, 0.0);
  // Below center (larger y) -> positive elevation; above -> negative.
  EXPECT_GT(pixel_to_angle(cv::Point2d(kCx, kCy + 50.0), camera_matrix_).y, 0.0);
  EXPECT_LT(pixel_to_angle(cv::Point2d(kCx, kCy - 50.0), camera_matrix_).y, 0.0);
}

TEST_F(PixelToAngleTest, SymmetricAboutPrincipalPoint)
{
  cv::Point2d right = pixel_to_angle(cv::Point2d(kCx + 123.0, kCy + 77.0), camera_matrix_);
  cv::Point2d left = pixel_to_angle(cv::Point2d(kCx - 123.0, kCy - 77.0), camera_matrix_);
  EXPECT_DOUBLE_EQ(right.x, -left.x);
  EXPECT_DOUBLE_EQ(right.y, -left.y);
}

TEST_F(PixelToAngleTest, KnownFortyFiveDegreeAngle)
{
  // A pixel offset equal to the focal length subtends exactly 45 degrees.
  cv::Mat wide = make_camera_matrix(200.0, 200.0, 320.0, 240.0);
  cv::Point2d angle = pixel_to_angle(cv::Point2d(320.0 + 200.0, 240.0), wide);
  EXPECT_DOUBLE_EQ(angle.x, M_PI / 4.0);
  EXPECT_DOUBLE_EQ(angle.y, 0.0);
}

TEST_F(PixelToAngleTest, UsesFxAndFyIndependently)
{
  // Same pixel offset in x and y, but fx != fy, so angles must differ.
  cv::Point2d angle = pixel_to_angle(cv::Point2d(kCx + 100.0, kCy + 100.0), camera_matrix_);
  EXPECT_DOUBLE_EQ(angle.x, std::atan2(100.0, kFx));
  EXPECT_DOUBLE_EQ(angle.y, std::atan2(100.0, kFy));
  EXPECT_NE(angle.x, angle.y);
}

TEST_F(PixelToAngleTest, AnglesStayWithinQuarterTurnForValidPixels)
{
  // Corners of the valid image area.
  for (const auto & pixel : {
      cv::Point2d(0.0, 0.0),
      cv::Point2d(2.0 * kCx - 1.0, 0.0),
      cv::Point2d(0.0, 2.0 * kCy - 1.0),
      cv::Point2d(2.0 * kCx - 1.0, 2.0 * kCy - 1.0)})
  {
    cv::Point2d angle = pixel_to_angle(pixel, camera_matrix_);
    EXPECT_GT(angle.x, -M_PI / 2.0);
    EXPECT_LT(angle.x, M_PI / 2.0);
    EXPECT_GT(angle.y, -M_PI / 2.0);
    EXPECT_LT(angle.y, M_PI / 2.0);
  }
}

TEST_F(PixelToAngleTest, TopLeftCornerIsValid)
{
  EXPECT_NO_THROW(pixel_to_angle(cv::Point2d(0.0, 0.0), camera_matrix_));
}

TEST_F(PixelToAngleTest, NegativeCoordinatesThrow)
{
  EXPECT_THROW(
    pixel_to_angle(cv::Point2d(-1.0, kCy), camera_matrix_), std::invalid_argument);
  EXPECT_THROW(
    pixel_to_angle(cv::Point2d(kCx, -1.0), camera_matrix_), std::invalid_argument);
}

TEST_F(PixelToAngleTest, CoordinatesAtOrBeyondImageSizeThrow)
{
  // Bounds are derived from the principal point: width = 2*cx, height = 2*cy.
  EXPECT_THROW(
    pixel_to_angle(cv::Point2d(2.0 * kCx, kCy), camera_matrix_), std::invalid_argument);
  EXPECT_THROW(
    pixel_to_angle(cv::Point2d(kCx, 2.0 * kCy), camera_matrix_), std::invalid_argument);
  EXPECT_THROW(
    pixel_to_angle(cv::Point2d(1e6, 1e6), camera_matrix_), std::invalid_argument);
}

TEST_F(PixelToAngleTest, JustInsideUpperBoundDoesNotThrow)
{
  EXPECT_NO_THROW(
    pixel_to_angle(cv::Point2d(2.0 * kCx - 0.5, 2.0 * kCy - 0.5), camera_matrix_));
}

int main(int argc, char ** argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
