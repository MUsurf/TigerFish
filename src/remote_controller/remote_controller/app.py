from flask import Flask, request, jsonify, Response
from typing import Callable
from datetime import datetime

from remote_controller.ControllerValues import ControllerValues

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
        except:
            return jsonify({"error": "failed to get str and/or timestamp"}), 500

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

        except:
            return jsonify({"error": "failed to parse json"}), 400
        
        

        return jsonify({"message": "success"}), 200
    
    return handler



def make_http_dict_get(
        dict_getter: Callable,
        timestamp_getter: Callable | None = None
) -> Callable:
        
    def handler() -> tuple[Response, int]:

        try:
            string = dict_getter()

            if timestamp_getter != None:
                timestamp = timestamp_getter()
            else:
                # datetime(1970,1,1) indicates no data present
                timestamp = datetime(1970,1,1)
        except:
            return jsonify({"error": "failed to get str and/or timestamp"}), 500

        response = {
            "str": string,
            "timestamp": timestamp.strftime(r"%H:%M:%S:%f")
        }

        return jsonify(response), 200

    return handler


def make_http_dict_post(
        str_setter: Callable[[str], None],
) -> Callable[[], tuple[Response, int]]:
    
    def handler() -> tuple[Response, int]:

        if not request.is_json:
            return jsonify({"error": "Expected application/json"}), 400
        
        data = request.get_json()

        try:
            str_setter(data["str"])

        except:
            return jsonify({"error": "failed to parse json"}), 400
        
        

        return jsonify({"message": "success"}), 200
    
    return handler



def make_http_imu_get(
        imu_getter: Callable,
        timestamp_getter: Callable | None = None
) -> Callable:
    
    def handler() -> tuple[Response, int]:

        try:
            imu = imu_getter()

            if timestamp_getter != None:
                timestamp = timestamp_getter()
            else:
                # datetime(1970,1,1) indicates no data present
                timestamp = datetime(1970,1,1)
        except:
            return jsonify({"error": "failed to get imu and/or timestamp"}), 500

        response = {
            "x": imu.x,
            "y": imu.y,
            "z": imu.z,
            "roll": imu.roll,
            "pitch": imu.pitch,
            "yaw": imu.yaw,
            "timestamp": timestamp.strftime(r"%H:%M:%S:%f")
        }

        return jsonify(response), 200

    return handler



def make_http_imu_post(
        imu_setter: Callable[[ControllerValues], None],
) -> Callable[[], tuple[Response, int]]:
    
    def handler() -> tuple[Response, int]:

        if not request.is_json:
            return jsonify({"error": "Expected application/json"}), 400
        
        data = request.get_json()

        try:
            imu = ControllerValues.from_dict(data)
            imu_setter(imu)
        except:
            return jsonify({"error": "failed to parse json"}), 400
        
        return jsonify({"message": "success"}), 200
    
    return handler



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