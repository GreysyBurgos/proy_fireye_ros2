"""
Módulo de lanzamiento para el entorno de simulación del Proyecto Fireye.

Este archivo configura el servidor y cliente de Gazebo Harmonic, carga el mundo
especificado, posiciona el robot y gestiona las variables de entorno necesarias.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Genera la descripción de lanzamiento para la simulación completa.

    Configura el mundo 'harmonic.sdf', lanza el simulador Gazebo, publica el estado
    del robot y realiza el spawn del TurtleBot3 en las coordenadas especificadas.

    Returns:
        LaunchDescription: Objeto que contiene todas las acciones de lanzamiento.
    """
    launch_file_dir = os.path.join(get_package_share_directory('proy_fireye_mundo'), 'launch')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Configuraciones de lanzamiento
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='2.0')
    y_pose = LaunchConfiguration('y_pose', default='8.0')

    world = os.path.join(
        get_package_share_directory('proy_fireye_mundo'),
        'worlds',
        'harmonic.sdf'
    )

    # Comando para el servidor de Gazebo
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -s -v2 ', world],
            'on_exit_shutdown': 'false'
        }.items()

    
    )


    # Comando para el cliente de Gazebo (interfaz gráfica)
    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-g -v2 ', 'on_exit_shutdown': 'true'}.items()
    )

    # Publicador del estado del robot
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # Comando para spawnear el robot
    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose
        }.items()
    )

    # Configuración de variables de entorno para recursos de Gazebo
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(
            get_package_share_directory('proy_fireye_mundo'),
            'models')
    )




    # Creación de la descripción de lanzamiento
    ld = LaunchDescription()

    ld.add_action(set_env_vars_resources)
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(spawn_turtlebot_cmd)
    ld.add_action(robot_state_publisher_cmd)
    

    return ld
