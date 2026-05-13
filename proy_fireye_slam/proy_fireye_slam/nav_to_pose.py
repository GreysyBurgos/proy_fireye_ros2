# ==============================================================
# SCRIPT: nav_to_pose.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de navegación autónoma punto a punto que utiliza el stack
# Nav2 para desplazar al robot FirEye a una ubicación específica.
#
# Funcionalidad principal:
# - Definición de una meta única (Goal Pose) en el mapa global.
# - Monitorización en tiempo real de la distancia euclidiana restante.
# - Gestión de estados finales de la tarea (Éxito, Error o Cancelado).
#
# Este script es la unidad básica de movimiento autónomo, ideal
# para enviar al robot a una zona de inspección concreta.
# ==============================================================

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def main():
    """
    Punto de entrada para la ejecución de navegación simple.
    """
    rclpy.init()

    # ==========================================================
    # INICIALIZACIÓN DEL NAVEGADOR
    # ==========================================================
    # El objeto BasicNavigator centraliza la lógica de control de Nav2.
    nav = BasicNavigator()

    # Espera bloqueante para asegurar que los servidores de acción estén listos.
    nav.waitUntilNav2Active()

    # ==========================================================
    # CONFIGURACIÓN DE LA META (GOAL)
    # ==========================================================
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = nav.get_clock().now().to_msg()

    # Coordenadas destino obtenidas del mapa de la instalación.
    goal_pose.pose.position.x = -10.287074
    goal_pose.pose.position.y = -6.764256
    goal_pose.pose.orientation.w = -0.00143432

    # ==========================================================
    # EJECUCIÓN Y SEGUIMIENTO
    # ==========================================================
    print(f"Enviando al robot a: X={goal_pose.pose.position.x}, Y={goal_pose.pose.position.y}...")
    nav.goToPose(goal_pose)

    i = 0
    while not nav.isTaskComplete():
        i += 1
        feedback = nav.getFeedback()
        
        # Monitorización: Se muestra el progreso cada 5 ciclos de feedback.
        if feedback and i % 5 == 0:
            print(f'Distancia restante: {feedback.distance_remaining:.2f} metros.')

    # ==========================================================
    # VALIDACIÓN DEL RESULTADO
    # ==========================================================
    result = nav.getResult()
    
    if result == TaskResult.SUCCEEDED:
        print(' ¡Victoria! El robot ha llegado a la meta.')
    elif result == TaskResult.CANCELED:
        print(' La misión ha sido cancelada.')
    elif result == TaskResult.FAILED:
        print(' Error: La navegación ha fallado.')

    # Cierre limpio del sistema de comunicación
    rclpy.shutdown()

if __name__ == '__main__':
    main()