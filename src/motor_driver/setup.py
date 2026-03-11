from setuptools import find_packages, setup
from glob import glob

<<<<<<< HEAD:pid_node/setup.py
package_name = "pid_node"
=======

package_name = 'motor_driver'
>>>>>>> clean_branch:src/motor_driver/setup.py

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
<<<<<<< HEAD:pid_node/setup.py
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
=======
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),  
        (f'share/{package_name}/data', glob('data/*.json')),
>>>>>>> clean_branch:src/motor_driver/setup.py
    ],
    install_requires=["setuptools"],
    zip_safe=True,
<<<<<<< HEAD:pid_node/setup.py
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "pid_node = pid_node.pid:main",
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
            'motor_interface=motor_driver.motor_interface:main'
>>>>>>> clean_branch:src/motor_driver/setup.py
        ],
    },
)
