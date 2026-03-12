# TapeWorm

This repository contains the code for the new autonomous underwater robot tentatively named TapeWorm. The express purpose of this code is to be better than the code for last competition while upgrading major dependencies, such as Python versions and ROS versions.

## Development

Place desired commands to run the code in run.sh. catkin_ws is located in the ~ directory which is /root for this container.

**Do not develop within the container** as your changes will not be saved. To install a dependency please add it to the Dockerfile.

## Docker

To run you must have the Docker Engine installed an NVIDIA Jetson. This can run on any device so long as the path to the GPIO is changed for RUN_OPTS in build.sh

To run you must use a bash terminal. For Windows you can use GitBash.

### Build the Docker Container

`sudo bash build.sh <name>` or `./build.sh <name>`
Replace `<name>` with the desired name of the container. The script will prompt to delete a container if an existing one is found.

### Run the Docker Container

`sudo bash run.sh <name>` or `./run.sh <name>`
Replace `<name>` with the desired name of the container.

#### Using The Docker Container

Instructions on how to run and launch ros nodes and scripts will be located inside run.sh,
build.sh will use the dockerfile to create and run the container

## Running with ROS

Before you run anything with ros you need to have sourced ros this is usually done with the command `source XXXX`

Steps to run ROS

1. Source ROS into system
2. cd catkin_workspace directory
3. catkin_make
4. source devel/setup.bash
5. rosrun 'package_name' 'python_file'.py

Common Problems

+ ROS is not sourced roscore will not run
+ catkin_make fails because you are missing a dependency
+ catkin_make fails because you did not configure CMakeLists
+ Python files are not executables

+ Check that I2C address is correct
+ All files should be run with python3 as the interpreter
+ Types for launch files are **Very important**

At step 2 you should see a directory with the following structure

    catkin_workspace
    |___
        src
        |___
            CMakeLists.txt
            'package_name'/
            |___
                CMakeLists
                package.xml
                src/
                |___
                    **python files**
                scripts/
                |___
                    **python files**

## make file commands
To run a make command ensure that you are using wsl. Then, you can type make "command".
IMPORTANT: run "make checkAll" to make sure that your changes compile + adhere to formatting
Debugging formatting may be easier with just running "make format"
make sure to update the makefile if you want to exclude particular packages from formatting (see variables in makefile)

**ALL COMMANDS:**
- _make build_ : this will build your ros packages. run this before running the other commands (excluding checkAll, buildTest)
- _make test_ : this will run all of the test files for the packages. honestly we don't have tests right now, but this is good to run for posterity
- _make buildTest_ : runs build and test together
- _make format_ : formats your code for you. some code may need to be manually formatted

- _make lint_ : lints (or checks) for formatting. Will not update formatting. suggested to run after format
- _make formatLint_ : runs format and lint together

- _make checkAll_ : runs format, lint, build, and test. This is what will be done on github
- _make clean-docker_ : theoretically will clean up any docker containers made by tigerfish. use with caution

- _make view-sm_ : run after build. This runs the statemachine and will display it on localhost:5000
- _make stop-view-sm_ : ensures that view-sm is cleaned up (shouldn't be necessary)


## Documentation Practices
- Commits: try to list all the big changes you've made in a commit message. for example: "added forward motor control". This will help with keeping track of major changes.

### Catkin Modules

All nodes in Catkin Workspace must have the following documentation added at the head of the file. White Space is important here!

    '''

    "Control System: eg. ROS or ROS2"

    Node: "Name"
    Publishes: 
        "Topics each on own line"
    Subscribes:
        "Topics each on own line"
    
    Maintainer: "Name"

    '''

Note: The maintainer is not just the person writing this code but is also the person who all questions should be refered to.

An optional but highly encouraged additional piece of documentation to add to each file is a short addendum to the above segment explaining what and why the node exists.

    '''
    
    This Node functions to do X

    This Node is here to break out the behavoirs of X system into multiple nodes.

    '''

### Documentation Builder

Documentation will be built with [Sphinx](https://www.sphinx-doc.org/en/master/) this requires that there be a second file system 'Documentation' which is compiled into docs.

All code in 'Generated/' is automatically grabbed by 'Generate_docs.sh' **do not edit here all changes can be overwritten**.

## History

The starter code in this repository was developed for Jelly2, the sub for 23-24 SURF and 2024 Robosub.

### Why Docker?

It may not be evident why we chose to dockerize our ROS system even though a Nvidia Jetson is still required. However it proved very usefull when at competition one of the SSDs was non-operable. Additionally docker in theory allows us to move over a Raspberry pi 5 easily.

### Async Control System

The choice to not use a time interupt based system was made because it seemed to complicate the motor control unnessisarily and introduce the consideration of where the submarine was when considering tasks. The alternative was to disregard position and just deal with velocity and change in position. For example you don't care about where a bouy is just that you are in a constant poisition relative to it.

### Acknoledgement of Contributions

Many helped create this code for the submarine for competition, and their contributions are reflected on the [GitHub page](https://github.com/MUsurf/JellyRos2). Many also played pivotal roles in the progress seen in this code, and while not contributing directly to the code, they make it possible to continue the work we have done and are continuing to do. This blurb serves as a reminder of the hours of work put into this team and as a thank you to those working on every aspect of this project seen or not.
