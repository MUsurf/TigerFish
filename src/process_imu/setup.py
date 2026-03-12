from setuptools import find_packages, setup

package_name = "process_imu"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="root",
    maintainer_email="creeon99@gmail.com",
    description="IMU data processing node for TigerFish",
    license="Apache-2.0",
    extras_require={
        "test": ["pytest"],
    },
    entry_points={
        "console_scripts": ["process_imu_node = process_imu.process_imu_node:main"],
    },
)
