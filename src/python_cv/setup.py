from setuptools import find_packages, setup

package_name = 'python_cv'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models', ['resource/models/gate_yolo.pt']),
        ('share/' + package_name + '/models', ['resource/models/bin_yolo.pt']),
        ('share/' + package_name + '/models', ['resource/models/bin_task_model.pt']),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='creeon99@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        "console_scripts": ["gate_cv = python_cv.front_cv:main"],
    },
)
