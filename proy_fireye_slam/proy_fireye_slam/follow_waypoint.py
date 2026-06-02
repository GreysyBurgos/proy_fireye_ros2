#!/usr/bin/env python3
# ==============================================================================
# SCRIPT: follow_waypoints_real.py (Optimizado para entorno REAL)
# ==============================================================================

import math
import time
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def euler_to_quaternion(yaw):
    """
    Convierte un ángulo Yaw (rotación en Z) a un cuaternión (x, y, z, w).
    """
    qx = 0.0
    qy = 0.0
    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)
    return qx, qy, qz, qw

def main():
    """
    Punto de entrada para la ejecución de la patrulla en entorno real.
    """
    rclpy.init()
    
    # Inicialización del controlador de navegación de Nav2
    nav = BasicNavigator()

    # Bloqueo preventivo hasta que el hardware y Nav2 estén listos
    print("Esperando a que Nav2 y los sensores reales estén listos...")
    nav.waitUntilNav2Active()

    # ==========================================================
    # DEFINICIÓN DE LA RUTA REAL (4 PUNTOS CORREGIDOS)
    # ==========================================================
    ruta = []

    # Tus puntos reales exactos (Corregidos a floats puros)
    puntos_datos = [
        (0.235, 0.351, 0.189),
        (0.74, 0.369, -0.00143),
        (0.235, 0.351, 0.189),
        (0.0, 0.0, 0.0)  # <-- ¡Corregido de (0,0,0) a (0.0, 0.0, 0.0)!
    ]

    # Procesar puntos
    for i, (x, y, yaw) in enumerate(puntos_datos):
        p = PoseStamped()
        p.header.frame_id = 'map'
        # Usamos el tiempo real del sistema
        p.header.stamp = nav.get_clock().now().to_msg()
        
        # Coordenadas físicas en metros (Forzamos float por seguridad)
        p.pose.position.x = float(x)
        p.pose.position.y = float(y)
        p.pose.position.z = 0.0
        
        # Conversión de la orientación real
        qx, qy, qz, qw = euler_to_quaternion(float(yaw))
        p.pose.orientation.x = qx
        p.pose.orientation.y = qy
        p.pose.orientation.z = qz
        p.pose.orientation.w = qw
        
        ruta.append(p)

    # ==========================================================
    # EJECUCIÓN Y SEGUIMIENTO EN TIEMPO REAL
    # ==========================================================
    print(f"Lanzando patrulla real con {len(ruta)} puntos...")
    
    # Envío de la ruta al Waypoint Follower
    nav.followWaypoints(ruta)

    # Monitoreo de telemetría en tiempo real
    ultimo_wp = -1
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            current_wp = feedback.current_waypoint
            print(f'Robot real en ruta -> Alcanzando punto: {current_wp + 1} de {len(ruta)}  ', end='\r')
            
            # Si el robot acaba de cambiar de punto, le damos un respiro para estabilizar hardware
            if current_wp != ultimo_wp and ultimo_wp != -1:
                time.sleep(0.5) 
            ultimo_wp = current_wp

    # ==========================================================
    # DIAGNÓSTICO FINAL DEL ROBOT
    # ==========================================================
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print('\n [ÉXITO] ¡El robot real completó toda la ruta y regresó a salvo!')
    elif result == TaskResult.CANCELED:
        print('\n [ALERTA] La operación fue cancelada por seguridad.')
    elif result == TaskResult.FAILED:
        print('\n [ERROR] El robot no pudo llegar a un punto. Posible obstáculo real bloqueando la ruta.')

    rclpy.shutdown()

if __name__ == '__main__':
    main()