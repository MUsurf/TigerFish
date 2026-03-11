from setuptools import find_packages, setup
from glob import glob
import os

package_name = "motor_driver"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # Includes launch files
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        # Includes data/config files
        (os.path.join("share", package_name, "data"), glob("data/*.json")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="root",
    maintainer_email="creeon99@gmail.com",
    description="Motor driver package for TigerFish",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "motor_interface = motor_driver.motor_interface:main",
        ],
    },
)
