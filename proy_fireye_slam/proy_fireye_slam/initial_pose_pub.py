"""
Nodo publicador de la pose inicial para el Proyecto Fireye.

Este script publica automáticamente la posición y orientación inicial del
robot en el topic /initialpose para inicializar el sistema de localización AMCL.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped

class InitialPosePublisher(Node):
    """
    Clase que representa el nodo publicador de la pose inicial.
    """
    def __init__(self):
        super().__init__('initial_pose_pub_node')
        
        # Creamos el publicador
        self.publisher_ = self.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )
        
        # Usamos un temporizador de 1 segundo para dar tiempo a que AMCL y RViz 
        # se conecten antes de lanzar el mensaje.
        self.timer = self.create_timer(1.0, self.publish_initial_pose)
        self.pose_published = False

    def publish_initial_pose(self):
        """Construye y publica el mensaje de la posición inicial una sola vez."""
        if not self.pose_published:
            msg = PoseWithCovarianceStamped()
            
            # 1. Cabecera del mensaje
            msg.header.frame_id = 'map'
            msg.header.stamp = self.get_clock().now().to_msg()
            
            # 2. Posición (Ajusta estas coordenadas según dónde empiece tu robot)
            msg.pose.pose.position.x = 0.0  
            msg.pose.pose.position.y = 0.0  
            msg.pose.pose.position.z = 0.0
            
            # 3. Orientación en Cuaterniones (w=1.0 significa mirando al frente sin rotar)
            msg.pose.pose.orientation.x = 0.0
            msg.pose.pose.orientation.y = 0.0
            msg.pose.pose.orientation.z = 0.0
            msg.pose.pose.orientation.w = 1.0
            
            # Publicamos y marcamos como completado
            self.publisher_.publish(msg)
            self.get_logger().info('¡Pose inicial publicada correctamente en AMCL!')
            self.pose_published = True

def main(args=None):
    rclpy.init(args=args)
    node = InitialPosePublisher()
    
    # Hacemos spin hasta que se publique el mensaje, luego cerramos limpiamente
    while rclpy.ok() and not node.pose_published:
        rclpy.spin_once(node)
        
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()