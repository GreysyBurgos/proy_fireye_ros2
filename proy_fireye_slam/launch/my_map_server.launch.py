"""
Módulo de lanzamiento para la localización y mapeo (SLAM) del Proyecto Fireye.

Este archivo configura e inicia los nodos de map_server, amcl y rviz2 para
proporcionar el mapa al sistema y localizar el robot en la simulación.
"""
import os

import launch.actions
import launch_ros.actions
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """Genera la descripción de lanzamiento para el sistema de localización.

    Obtiene las rutas de los archivos de configuración (parámetros, mapa y rviz)
    del paquete proy_fireye_slam y levanta los nodos necesarios para Nav2.

    Returns:
        LaunchDescription: Objeto que contiene las acciones y nodos a ejecutar.
    """
    # Rutas a los archivos
    nav2_yaml = os.path.join(get_package_share_directory('proy_fireye_slam'), 'param', 'burger.yaml')
    map_file = os.path.join(get_package_share_directory('proy_fireye_slam'), 'map', 'my_map.yaml')
    rviz_config_dir = os.path.join(get_package_share_directory('proy_fireye_slam'), 'rviz', 'tb3_navigation2.rviz')

    return LaunchDescription([
        Node(
            package = 'nav2_map_server',
            executable = 'map_server',
            name = 'map_server',
            output = 'screen',
            parameters=[nav2_yaml,
                        {'yaml_filename':map_file}]
        ),

        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[nav2_yaml]
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{'use_sim_time': True},
                        {'autostart': True},
                        {'node_names': ['map_server', 'amcl']}]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
    ])