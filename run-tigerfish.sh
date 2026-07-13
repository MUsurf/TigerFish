#!/usr/bin/env bash

set -e

cd ~/TigerFish

docker compose --profile pi run --rm --service-ports --entrypoint /home/ros2_ws/run.sh pi
