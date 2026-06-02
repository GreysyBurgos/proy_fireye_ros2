import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class WaypointServiceNode(Node):
    def __init__(self):
        super().__init__('waypoint_service_node')
        
        # 1. Crear el servidor del servicio (Nombre: 'iniciar_ruta')
        self.srv = self.create_service(Trigger, 'iniciar_ruta', self.execute_route_callback)
        
        # 2. Inicializar el BasicNavigator
        self.nav = BasicNavigator()
        
        self.get_logger().info('Servicio "iniciar_ruta" listo. Esperando llamadas...')

    def execute_route_callback(self, request, response):
        self.get_logger().info('¡Llamada recibida! Preparando Nav2...')
        
        # Esperar a que Nav2 esté listo
        self.nav.waitUntilNav2Active()

        # Crear la ruta con tus waypoints
        ruta = []

        # Punto 1
        p1 = PoseStamped()
        p1.header.frame_id = 'map'
        p1.header.stamp = self.nav.get_clock().now().to_msg()
        p1.pose.position.x = -10.287074  
        p1.pose.position.y = -6.764256
        p1.pose.orientation.w = 1.0
        ruta.append(p1)

        # Punto 2
        p2 = PoseStamped()
        p2.header.frame_id = 'map'
        p2.header.stamp = self.nav.get_clock().now().to_msg()
        p2.pose.position.x = -2.685082
        p2.pose.position.y = -17.167942
        p2.pose.orientation.w = 1.0
        ruta.append(p2)

        # Punto 3 
        p3 = PoseStamped()
        p3.header.frame_id = 'map'
        p3.header.stamp = self.nav.get_clock().now().to_msg()
        p3.pose.position.x = 6.6849079
        p3.pose.position.y = -11.807257
        p3.pose.orientation.w = 1.0
        ruta.append(p3)

        # Punto 4
        p4 = PoseStamped()
        p4.header.frame_id = 'map'
        p4.header.stamp = self.nav.get_clock().now().to_msg()
        p4.pose.position.x = 2.946637
        p4.pose.position.y = -0.690302
        p4.pose.orientation.w = 1.0
        ruta.append(p4)

        # Enviar la ruta completa
        self.get_logger().info(f"Enviando ruta con {len(ruta)} puntos al robot...")
        self.nav.followWaypoints(ruta)

        # Monitorizar progreso (esto bloquea el servicio hasta que termine)
        while not self.nav.isTaskComplete():
            feedback = self.nav.getFeedback()
            if feedback:
                print(f'Visitando punto: {feedback.current_waypoint + 1} de {len(ruta)}', end='\r')

        # Evaluar el resultado final y rellenar la respuesta del servicio
        result = self.nav.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('\n¡Ruta completada con éxito!')
            response.success = True
            response.message = "Ruta completada exitosamente."
        else:
            self.get_logger().warn('\nLa ruta ha fallado o ha sido cancelada.')
            response.success = False
            response.message = "Fallo al completar la ruta."

        return response

def main(args=None):
    rclpy.init(args=args)
    
    waypoint_service = WaypointServiceNode()
    
    try:
        rclpy.spin(waypoint_service)
    except KeyboardInterrupt:
        pass
    finally:
        waypoint_service.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()