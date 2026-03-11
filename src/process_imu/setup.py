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
<<<<<<< HEAD:process_imu/setup.py
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["process_imu = process_imu.process_imu:main"],
=======
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
        'console_scripts': [
            'process_imu_node=process_imu.process_imu_node:main'
        ],
>>>>>>> clean_branch:src/process_imu/setup.py
    },
)
