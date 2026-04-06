import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare the argument (e.g., "0" or "0,1" or "0,1,2,3")
    camera_ids_arg = DeclareLaunchArgument(
        'cam_ids',
        default_value='0,1',
        description='Comma-separated list of camera indices'
    )
    rec_type = DeclareLaunchArgument('record_type', default_value='mp4', description="type of recording (ie mp4)")

    cam_ids_str = LaunchConfiguration('cam_ids')

    
    def create_camera_nodes(context):
        # Convert the string '0,1,2' back into a list [0, 1, 2]
        ids_str = cam_ids_str.perform(context)
        ids = ids_str.split(',')


        rec_type = context.launch_configurations.get('record_type', 'mp4')
        entities = []
        for i in ids:
            i = i.strip()

            clean_ns = i.replace('/', "_").replace('.', '_')
            ns=f"cam_{clean_ns}"
            ns = f"cam_{i}"
            
            idx= int(i) if i.isdigit() else i
            
            # Publisher
            entities.append(Node(
                package='cameras',
                executable='camera_publisher',
                namespace=ns,
                parameters=[{'camera_index': idx}],
                output='screen'
            ))

            # Subscriber (Processor)
            entities.append(Node(
                package='cameras',
                executable='subscriber_node',
                namespace=ns,
                parameters=[{'record_type': rec_type}],
                output='screen'
            ))
        return entities

    # Using OpaqueFunction allows to parse the string inside the launch process
    from launch.actions import OpaqueFunction
    return LaunchDescription([
        camera_ids_arg,
        rec_type,
        OpaqueFunction(function=create_camera_nodes)
    ])