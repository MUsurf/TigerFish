from flask import Flask, request, jsonify, Response
from typing import Callable
from datetime import datetime
import numpy as np

from nav_msgs.msg import Odometry
from messages.msg import ControllerInput

def make_http_str_get(
        str_getter: Callable,
        timestamp_getter: Callable | None = None
) -> Callable:
        
    def handler() -> tuple[Response, int]:

        try:
            string = str_getter()

            if timestamp_getter != None:
                timestamp = timestamp_getter()
            else:
                # datetime(1970,1,1) indicates no data present
                timestamp = datetime(1970,1,1)
        except Exception as e:
            return jsonify({
                "error": f"failed to get str and/or timestamp; error msg: {e}"
            }), 500

        response = {
            "str": string,
            "timestamp": timestamp.strftime(r"%H:%M:%S:%f")
        }

        return jsonify(response), 200

    return handler



def make_http_str_post(
        str_setter: Callable[[str], None],
) -> Callable[[], tuple[Response, int]]:
    
    def handler() -> tuple[Response, int]:

        if not request.is_json:
            return jsonify({"error": "Expected application/json"}), 400
        
        data = request.get_json()

        try:
            str_setter(data["str"])

        except Exception as e:
            return jsonify({
                "error": f"failed to parse json; error msg: {e}"
            }), 400


        return jsonify({"message": "success"}), 200
    
    return handler



def make_http_controller_input_post(
        controller_input_setter: Callable[[dict], None],
) -> Callable[[], tuple[Response, int]]:
    
    def handler() -> tuple[Response, int]:

        if not request.is_json:
            return jsonify({"error": "Expected application/json"}), 400
        
        data = request.get_json()

        try:
            controller_input_setter(data["controller_input"])

        except Exception as e:
            return jsonify({
                "error": f"failed to parse json; error msg: {e}"
            }), 400


        return jsonify({"message": "success"}), 200
    
    return handler



def make_http_rpy_get(
        odometry_getter: Callable[[], Odometry],
        timestamp_getter: Callable[[], datetime] | None
):
    def handler() -> tuple[Response, int]:

        # fetch values from node
        try:
            odometry = odometry_getter()

            if timestamp_getter != None:
                timestamp = timestamp_getter()
            else:
                # datetime(1970,1,1) indicates no data present
                timestamp = datetime(1970,1,1)
        except Exception as e:
            return jsonify({
                "error": f"failed to get odometry and/or timestamp; error msg: {e}"
            }), 500
        
        # process values for REST protocol
        r, p, y = rpy_from_quat(odometry.pose.pose.orientation)

        # build and return response
        response = {
            "roll": r,
            "pitch": p,
            "yaw": y,
            "timestamp": timestamp.strftime(r"%H:%M:%S:%f")
        }
        return jsonify(response), 200

    return handler



# TODO: make a utilities library folder on sub so code like this doesn't have to bloat scripts
#       this copied and pasted from the main node
def rpy_from_quat(q):
    """
    Convert geometry_msgs.msg.Quaternion to roll, pitch, yaw (radians).
    
    Assumes quaternion fields:
        q.x, q.y, q.z, q.w
    Uses XYZ (roll, pitch, yaw) convention.
    """

    x = q.x
    y = q.y
    z = q.z
    w = q.w

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.sign(sinp) * (np.pi / 2.0)  # use 90° if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw



def build_app(
        get_endpoints: dict[str, Callable],
        post_endpoints: dict[str, Callable]
) -> Flask:
    app = Flask("remote_controller")

    for endpoint in get_endpoints.keys():
        func = get_endpoints[endpoint]

        app.add_url_rule(
            rule=f"/{endpoint}",
            endpoint=f"get_{endpoint}",
            view_func=func,
            methods=["GET"]
        )

    for endpoint in post_endpoints.keys():
        func = post_endpoints[endpoint]

        app.add_url_rule(
            rule=f"/{endpoint}",
            endpoint=f"post_{endpoint}",
            view_func=func,
            methods=["POST"]
        )

    return app