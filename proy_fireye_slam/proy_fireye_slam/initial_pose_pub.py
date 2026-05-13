# ==============================================================
# SCRIPT: initial_pose_pub.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo especializado en la inicialización de la localización del
# robot FirEye dentro del mapa global.
#
# Funcionalidad principal:
# - Publicar un mensaje de tipo PoseWithCovarianceStamped.
# - Notificar al sistema AMCL la ubicación exacta de inicio.
# - Sincronizar la visualización en RViz con el estado del robot.
#
# Este nodo es crítico para evitar errores de deriva en los
# filtros de partículas de AMCL al arrancar el sistema.
# ==============================================================

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped

class InitialPosePublisher(Node):
    """
    Clase que representa el nodo publicador de la pose inicial.

    Gestiona la creación del mensaje y asegura que se publique una sola vez
    tras un breve retardo para garantizar que el resto de nodos estén listos.
    """
    def __init__(self):
        """
        Inicializa el nodo, el publicador y el temporizador de disparo.
        """
        super().__init__('initial_pose_pub_node')
        
        # ==========================================================
        # CONFIGURACIÓN DEL PUBLICADOR
        # ==========================================================
        self.publisher_ = self.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )
        
        # Temporizador para dar margen de conexión a AMCL/RViz (1 segundo)
        self.timer = self.create_timer(1.0, self.publish_initial_pose)
        self.pose_published = False

    def publish_initial_pose(self):
        """
        Construye y publica el mensaje de la posición inicial.

        Define las coordenadas (x, y, z) y la orientación (cuaternión)
        que coinciden con el punto de spawn o inicio real del robot.
        """
        if not self.pose_published:
            msg = PoseWithCovarianceStamped()
            
            # 1. Cabecera (Timestamp y Frame de referencia)
            msg.header.frame_id = 'map'
            msg.header.stamp = self.get_clock().now().to_msg()
            
            # 2. Posición: Origen de coordenadas del mapa
            msg.pose.pose.position.x = 0.0  
            msg.pose.pose.position.y = 0.0  
            msg.pose.pose.position.z = 0.0
            
            # 3. Orientación: Mirando hacia el frente (Eje X positivo)
            msg.pose.pose.orientation.x = 0.0
            msg.pose.pose.orientation.y = 0.0
            msg.pose.pose.orientation.z = 0.0
            msg.pose.pose.orientation.w = 1.0
            
            # Publicación efectiva
            self.publisher_.publish(msg)
            self.get_logger().info('✅ ¡Pose inicial publicada correctamente en AMCL!')
            self.pose_published = True

# ==============================================================
# MAIN
# ==============================================================
def main(args=None):
    """
    Punto de entrada para el nodo de inicialización de pose.
    """
    rclpy.init(args=args)
    node = InitialPosePublisher()
    
    # Mantiene el nodo activo solo hasta que se cumpla la tarea
    while rclpy.ok() and not node.pose_published:
        rclpy.spin_once(node)
        
    # Limpieza de recursos al finalizar
    node.destroy_node()
    rclpy.shutdown()

# ==============================================================
# EJECUCIÓN DIRECTA
# ==============================================================
if __name__ == '__main__':
    main()