from setuptools import find_packages, setup
import os
from glob import glob 

package_name = "main"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # Include all launch files (Python, XML, or YAML)
        (os.path.join("share", package_name, "launch"), glob("launch/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer='root',
    maintainer_email='creeon99@gmail.com',
    description='Main mission control and launch package for TigerFish',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'main_node = main.main_node:main'
        ],
    },
)