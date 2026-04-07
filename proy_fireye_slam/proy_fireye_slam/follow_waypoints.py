import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def main():
    rclpy.init()
    nav = BasicNavigator()

    # Esperar a que Nav2 esté listo
    nav.waitUntilNav2Active()

    # Crear una ruta (lista de puntos)
    ruta = []

    # Punto 1
    p1 = PoseStamped()
    p1.header.frame_id = 'map'
    p1.header.stamp = nav.get_clock().now().to_msg()
    p1.pose.position.x = -10.287074  
    p1.pose.position.y = -6.764256
    p1.pose.orientation.w = 1.0
    ruta.append(p1)

    # Punto 2
    p2 = PoseStamped()
    p2.header.frame_id = 'map'
    p2.header.stamp = nav.get_clock().now().to_msg()
    p2.pose.position.x = -2.685082
    p2.pose.position.y = -17.167942
    p2.pose.orientation.w = 1.0
    ruta.append(p2)

    # Punto 3 
    p3 = PoseStamped()
    p3.header.frame_id = 'map'
    p3.header.stamp = nav.get_clock().now().to_msg()
    p3.pose.position.x = 6.6849079
    p3.pose.position.y = -11.807257
    p3.pose.orientation.w = 1.0
    ruta.append(p3)

    # Punto 4
    p4 = PoseStamped()
    p4.header.frame_id = 'map'
    p4.header.stamp = nav.get_clock().now().to_msg()
    p4.pose.position.x = 2.946637
    p4.pose.position.y = -0.690302
    p4.pose.orientation.w = 1.0
    ruta.append(p4)

    # Enviar la ruta completa
    print(f"Enviando ruta con {len(ruta)} puntos...")
    nav.followWaypoints(ruta)

    # Monitorizar progreso
    i = 0
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback:
            # El feedback en waypoints nos dice qué punto de la lista está visitando
            print(f'Visitando punto: {feedback.current_waypoint + 1} de {len(ruta)}', end='\r')

    # 5. Resultado final
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print('\n¡Ruta completada con éxito!')
    else:
        print('\nLa ruta ha fallado o ha sido cancelada.')

    rclpy.shutdown()

if __name__ == '__main__':
    main()