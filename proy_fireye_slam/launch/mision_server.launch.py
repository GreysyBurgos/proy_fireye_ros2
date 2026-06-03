from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='proy_fireye_slam',
            executable='fireye_mision_server',
            name='mision_accion_servidor',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),
    ])