# VARIABLES ---------------------------------------------------------
IMAGE_NAME = ros2-jazzy-app
WS_PATH = /home/ros2_ws


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

.PHONY: build test buildTest lint format formatLint view-sm clean-docker stop-view-sm checkAll

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
### END Utility commands - ADD NEW COMMANDS ABOVE ##############################