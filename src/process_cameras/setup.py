import os
from glob import glob
from setuptools import find_packages, setup

package_name = "ros2_opencv"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Raquel",
    maintainer_email="rrfgvd@umsystem.edu",
    description="TODO: Package description",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "publisher_node=ros2_opencv.cameraPublisher:main",
            "subscriber_node=ros2_opencv.subscriberImage:main",
            "servo_controller = servo_controller.servo_controller:main",
        ],
    },
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
    ],
)
