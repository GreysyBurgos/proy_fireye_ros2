import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'proy_fireye_slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'param'), glob('param/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'map'), glob('map/*.pgm')),
        (os.path.join('share', package_name, 'map'), glob('map/*.yaml'))

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Grupo6',
    maintainer_email='gbursal@upv.es',
    description='Paquete de SLAM para el proyecto Fireye',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'initial_pose_pub = proy_fireye_slam.initial_pose_pub:main',
            'nav_to_pose = proy_fireye_slam.nav_to_pose:main',
            'follow_waypoints = proy_fireye_slam.follow_waypoints:main',
            'fireye_mission_bt = proy_fireye_slam.fireye_mission_bt:main',
            'fireye_mision_servicio = proy_fireye_slam.fireye_mision_servicio:main',
        ],
    },
)
