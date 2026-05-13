# ==============================================================
# SCRIPT: setup.py
# --------------------------------------------------------------
# AUTOR: Manuel Perez
# FECHA: 12-05-2026
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Archivo de configuración de empaquetado para el paquete ROS 2 
# 'apiclient'. Define las dependencias, metadatos y los puntos 
# de entrada (ejecutables) para los nodos del sistema.
#
# Funcionalidad principal:
# - Registrar los nodos de comunicación y pruebas en el sistema ROS 2.
# - Gestionar las dependencias de Python (como 'requests').
# - Configurar la instalación de recursos y archivos de índice.
#
# Este archivo es fundamental para que comandos como 'ros2 run'
# puedan localizar y ejecutar los nodos desarrollados.
# ==============================================================
from setuptools import setup, find_packages

package_name = 'apiclient'

setup(
    name=package_name,
    version='0.0.1',

    # ==========================================================
    # PAQUETES Y RECURSOS
    # ==========================================================
    packages=find_packages(),

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    
    # ==========================================================
    # DEPENDENCIAS
    # ==========================================================
    install_requires=[
        'setuptools',
        'requests'
    ],

    zip_safe=True,
    maintainer='Manuel Perez',
    description='Servicio de comunicación con API local',
    license='Apache-2.0',

    # ==========================================================
    # PUNTOS DE ENTRADA (EJECUTABLES)
    # ==========================================================
    # Mapeo de comandos de consola a funciones main de los scripts.
    entry_points={
        'console_scripts': [
            'connection_service = apiclient.connection_node:main',

            'test_get_alertas = apiclient.test.test_get_alertas:main',

            'test_insert_alerta = apiclient.test.test_insert_alerta:main',

            'test_flow = apiclient.test.test_flow:main',
        ],
    },
)