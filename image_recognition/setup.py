from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'image_recognition'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    #packages=[package_name]
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # # Include images directory in live shared package
        # ('share/' + package_name, ['test_images/mask.png']),
        ('share/' + package_name, glob('test_images/*.png')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
		'line_detector = image_recognition.image_detection_script:main',
		'image_publisher = image_recognition.image_publisher:main',
        ],
    },
)
