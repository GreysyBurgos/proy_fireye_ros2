# ==============================================================
# SCRIPT: follow_waypoints.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de navegación secuencial que utiliza el stack Nav2 para
# recorrer una lista de puntos de paso (waypoints) predefinidos.
#
# Funcionalidad principal:
# - Definición de una ruta compleja mediante coordenadas cartesianas.
# - Uso del método 'followWaypoints' para navegación encadenada.
# - Monitorización en tiempo real del progreso entre puntos.
#
# Este script permite al robot realizar patrullas o recorridos
# multi-punto de forma automatizada y fluida.
# ==============================================================

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def main():
    """
    Punto de entrada para la ejecución de la patrulla por waypoints.
    """
    rclpy.init()
    
    # Inicialización del controlador de navegación de Nav2
    nav = BasicNavigator()

    # Bloqueo preventivo hasta que los servidores de Nav2 estén operativos
    print("Esperando a que Nav2 esté listo...")
    nav.waitUntilNav2Active()

    # ==========================================================
    # DEFINICIÓN DE LA RUTA
    # ==========================================================
    # Lista para almacenar los objetos PoseStamped que forman el camino.
    ruta = []

    # Punto 1: Localización inicial de patrulla
    p1 = PoseStamped()
    p1.header.frame_id = 'map'
    p1.header.stamp = nav.get_clock().now().to_msg()
    p1.pose.position.x = -10.287074  
    p1.pose.position.y = -6.764256
    p1.pose.orientation.w = 1.0
    ruta.append(p1)

    # Punto 2: Esquina inferior izquierda
    p2 = PoseStamped()
    p2.header.frame_id = 'map'
    p2.header.stamp = nav.get_clock().now().to_msg()
    p2.pose.position.x = -2.685082
    p2.pose.position.y = -17.167942
    p2.pose.orientation.w = 1.0
    ruta.append(p2)

    # Punto 3: Punto de retorno bajo
    p3 = PoseStamped()
    p3.header.frame_id = 'map'
    p3.header.stamp = nav.get_clock().now().to_msg()
    p3.pose.position.x = 6.6849079
    p3.pose.position.y = -11.807257
    p3.pose.orientation.w = 1.0
    ruta.append(p3)

    # Punto 4: Final de ruta / Zona de carga
    p4 = PoseStamped()
    p4.header.frame_id = 'map'
    p4.header.stamp = nav.get_clock().now().to_msg()
    p4.pose.position.x = 2.946637
    p4.pose.position.y = -0.690302
    p4.pose.orientation.w = 1.0
    ruta.append(p4)

    # ==========================================================
    # EJECUCIÓN Y MONITORIZACIÓN
    # ==========================================================
    print(f"Enviando ruta con {len(ruta)} puntos...")
    
    # Orden de navegación secuencial
    nav.followWaypoints(ruta)

    # Bucle de feedback para informar al operador sobre el estado del robot
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            # El feedback indica el índice del waypoint actual (0 a N-1)
            print(f'Visitando punto: {feedback.current_waypoint + 1} de {len(ruta)}', end='\r')

    # ==========================================================
    # RESULTADO FINAL
    # ==========================================================
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print('\n ¡Ruta completada con éxito!')
    elif result == TaskResult.CANCELED:
        print('\n La ruta ha sido cancelada por el usuario.')
    elif result == TaskResult.FAILED:
        print('\n La ruta ha fallado. Revisa posibles obstáculos.')

    rclpy.shutdown()

if __name__ == '__main__':
    main()