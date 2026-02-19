# VARIABLES ---------------------------------------------------------
IMAGE_NAME = ros2-jazzy-app
WS_PATH = /home/ros2_ws

# new package creation variables -
NAME ?= my_new_pkg
WS_PATH = /home/ros2_ws
TYPE ?= normal
BUILD ?= cmake

# Define the list of packages to work with. To ignore a package add it to skip packages 
# ENSURE TO UPDATE SKIP PACKAGES if you are using an external github for example or external code
ALL_FOLDERS = $(shell ls -d */ | sed 's|/||')
SKIP_PACKAGES = yasmin yasmin_ros yasmin_viewer yasmin_factory yasmin_viewer_msgs build install log TestImages output_images Helpers imu_cpp # update the packages here
MY_PACKAGES = $(filter-out $(SKIP_PACKAGES), $(ALL_FOLDERS))

# Define colors for the echo statements
CYAN := \033[0;36m
GREEN := \033[0;32m
NC := \033[0m # No Color
# END VARIABLES -----------------------------------------------------


# Note: I would like to give Gemini AI credit in the making of this file.
# You should run build if you are setting up. Otherwise ruff linter+formatter won't be recognized, for example

.PHONY: build test buildTest lint format formatLint view-sm clean-docker stop-view-sm checkAll create_pkg gui-graph shell graph view-cam dashboard reconfigure plot rviz

# builds and then runs a test to make sure everything compiles nicely
buildTest: build test

# formats and lints
formatLint: format lint

# full check: this will run and format everything.
checkAll: format lint build test

# runs a simple docker build and ensures it runs with build kit
build:
	# Force BuildKit to show color during the build process
	DOCKER_BUILDKIT=1 docker build --progress=plain -t $(IMAGE_NAME) .

#Run tests: need to run build before test
test:
	docker run --rm -e FORCE_COLOR=1 $(IMAGE_NAME) bash -c \
		"source /home/ros2_ws/install/setup.bash && \
		colcon test \
			--packages-skip $(SKIP_PACKAGES) \
			--event-handlers console_direct+ \
			--pytest-args -k 'not (flake8 or pep257 or copyright or xmllint)' \
			--ctest-args -E '(uncrustify|cpplint|flake8|lint_cmake|xmllint|copyright|pep257)' && \
		colcon test-result --all --verbose"

# lint + format is not really helpful atm...
# format should be run before the lint command. It will format your code and catch most formatting bugs
format:
	docker run --rm \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		--user "$(shell id -u):$(shell id -g)" \
		-e FORCE_COLOR=1 \
		$(IMAGE_NAME) bash -c \
		"for pkg in $(MY_PACKAGES); do \
			echo -e \"$(CYAN)--- Formatting \$$pkg ---$(NC)\"; \
			pkg_path=/home/ros2_ws/src/TigerFish/\$$pkg; \
			if find \$$pkg_path -name '*.py' | grep -q .; then \
				ruff check \$$pkg_path --fix --no-cache --exclude 'launch,test,*_launch.py,test_*.py' --ignore D,ANN,ERA,EXE,INP,T201 || true; \
				ruff format \$$pkg_path --no-cache --exclude 'launch,test,*_launch.py,test_*.py' || true; \
			fi; \
			source /home/ros2_ws/install/setup.bash && \
			if find \$$pkg_path -name '*.cpp' -o -name '*.hpp' -o -name '*.h' | grep -q .; then \
				ament_uncrustify --reformat \$$pkg_path || true; \
			fi; \
		done && \
		echo -e \"$(GREEN)--- Formatting Complete! ---$(NC)\""

# Lint will check the code for formatting
lint:
	docker run --rm \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		--user "$(shell id -u):$(shell id -g)" \
		-e FORCE_COLOR=1 \
		$(IMAGE_NAME) bash -c \
		"for pkg in $(MY_PACKAGES); do \
			pkg_path=/home/ros2_ws/src/TigerFish/\$$pkg; \
			if [ -d \"\$$pkg_path\" ] && find \"\$$pkg_path\" -name '*.py' | grep -q .; then \
				echo -e \"$(CYAN)--- Linting \$$pkg ---$(NC)\"; \
				ruff check \"\$$pkg_path\" \
					--no-cache \
					--exclude 'launch,test,*_launch.py,test_*.py' \
					--ignore D,ANN,ERA,EXE,INP,T201 || exit 1; \
			fi; \
		done && \
		echo -e \"$(GREEN)--- Linting Passed! ---$(NC)\""

# Kill any running TigerFish-related containers if things get stuck
clean-docker:
	docker ps -q --filter "ancestor=$(IMAGE_NAME)" | xargs -r docker stop

### Utility commands - ADD NEW COMMANDS BELOW ##################################
### REMEMBER TO ADD NEW COMMANDS TO PHONY --------------------------------------

# Port 5000 is the default for the YASMIN viewer - run build first
# to view output change the last line: ros2 run state_machine state_machine_node > /dev/null 2>&1"
# to: ros2 run state_machine state_machine_node"
# note that this function may be laggy, especially if you have not muted output!
view-sm:
	@# Stop existing viewer to prevent 'Port already in use' errors
	-docker stop tigerfish_sm_viewer > /dev/null 2>&1
	@echo -e "\033[0;32m--- Starting YASMIN Viewer at http://127.0.0.1:5000 ---\033[0m"
	docker run --rm -it \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		-p 5000:5000 \
		--name tigerfish_sm_viewer \
		ros2-jazzy-app bash -c \
		"source /home/ros2_ws/install/setup.bash && \
		 (ros2 run yasmin_viewer yasmin_viewer_node --ros-args -p host:=0.0.0.0 > /dev/null 2>&1 &) && \
		 echo -e '\033[0;33m--- State Machine running (Logs Muted) ---\033[0m' && \
		 sleep 5 && \
		 ros2 run state_machine state_machine_node > /dev/null 2>&1"

# Stops the YASMIN viewer specifically
stop-view-sm:
	docker stop yasmin_viewer || true



# package creation

# usage: make create_pkg NAME="pkg_name" TYPE="type" BUILD="cmake/python"
# options:
# NAME=Any valid string for a package
# TYPE=<normal> or <msg> ; use normal for most uses
# BUILD=<cmake> or <python> ; cmake is for c++
create_pkg:
	@echo -e "$(CYAN)--- Creating $(TYPE) package: $(NAME) (Build: $(BUILD)) ---$(NC)"
	
	# 1. Base package creation
	docker run --rm \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) bash -c "cd /home/ros2_ws/src/TigerFish && \
		if [ \"$(BUILD)\" = \"python\" ]; then \
			ros2 pkg create --build-type ament_python --license Apache-2.0 $(NAME); \
		else \
			ros2 pkg create --build-type ament_cmake --license Apache-2.0 $(NAME); \
		fi"
	
	# 2. Universal Logic for Message Packages
ifeq ($(TYPE), msg)
	@echo -e "$(CYAN)--- Configuring interface generation for $(NAME) ---$(NC)"
	docker run --rm \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) bash -c "mkdir -p /home/ros2_ws/src/TigerFish/$(NAME)/msg && \
		printf 'int64 data\nstring status\n' > /home/ros2_ws/src/TigerFish/$(NAME)/msg/MyMessage.msg && \
		printf 'cmake_minimum_required(VERSION 3.8)\nproject($(NAME))\n\nfind_package(ament_cmake REQUIRED)\nfind_package(rosidl_default_generators REQUIRED)\n\nrosidl_generate_interfaces(\$${PROJECT_NAME}\n  \"msg/MyMessage.msg\"\n)\n\nament_package()\n' > /home/ros2_ws/src/TigerFish/$(NAME)/CMakeLists.txt && \
		sed -i '/<\/package>/i \  <build_depend>rosidl_default_generators<\/build_depend>\n  <exec_depend>rosidl_default_runtime<\/exec_depend>\n  <member_of_group>rosidl_interface_packages<\/member_of_group>' /home/ros2_ws/src/TigerFish/$(NAME)/package.xml"
endif
	@echo -e "$(GREEN)--- Success! Package $(NAME) is ready. ---$(NC)"


# graph utility
graph:
	@echo -e "$(CYAN)--- Current Node Graph (Text) ---$(NC)"
	docker run --rm $(IMAGE_NAME) bash -c "source /home/ros2_ws/install/setup.bash && ros2 node list && ros2 topic list"


# opens a ros shell
shell:
	docker run --rm -it \
		-v "$(CURDIR):/home/ros2_ws/src/TigerFish" \
		--net=host \
		$(IMAGE_NAME) /bin/bash

# show gui graph - expects wsl 2.6.2 atleast!
gui-graph:
	@# Grant permission for the local root user (docker) to access X11
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) ros2 run rqt_graph rqt_graph

view-cam:
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-e XDG_RUNTIME_DIR=/tmp \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) ros2 run rqt_image_view rqt_image_view

dashboard:
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-e XDG_RUNTIME_DIR=/tmp \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) rqt

reconfigure:
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		$(IMAGE_NAME) ros2 run rqt_reconfigure rqt_reconfigure

# usage: make plot TOPIC=/model/depth/data
plot:
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		$(IMAGE_NAME) ros2 run rqt_plot rqt_plot $(TOPIC)

rviz:
	xhost +local:docker > /dev/null 2>&1 || true
	docker run --rm -it \
		--net=host \
		-e DISPLAY=$(DISPLAY) \
		-e XDG_RUNTIME_DIR=/tmp/runtime-user \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		--user "$(shell id -u):$(shell id -g)" \
		$(IMAGE_NAME) bash -c "mkdir -p /tmp/runtime-user && chmod 700 /tmp/runtime-user && rviz2"
### END Utility commands - ADD NEW COMMANDS ABOVE ##############################