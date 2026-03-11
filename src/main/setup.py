from setuptools import find_packages, setup
import os
from glob import glob 

package_name = "main"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
<<<<<<< HEAD:main/setup.py
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # Include all launch files.
        (os.path.join("share", package_name, "launch"), glob("launch/*")),
=======
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
>>>>>>> clean_branch:src/main/setup.py
    ],
    install_requires=["setuptools"],
    zip_safe=True,
<<<<<<< HEAD:main/setup.py
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [],
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
            'main_node=main.main_node:main'
        ],
>>>>>>> clean_branch:src/main/setup.py
    },
)
