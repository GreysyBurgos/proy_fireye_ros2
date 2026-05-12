from setuptools import setup
import os
from glob import glob

package_name = 'apiclient'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'requests'],
    zip_safe=True,
    maintainer='Manuel Perez',
    description='Servicio de comunicación con API local',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'connection_service = apiclient.connection_node:main',
        ],
    },
)