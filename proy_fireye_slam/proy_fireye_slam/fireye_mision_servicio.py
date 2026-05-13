# ==============================================================
# SCRIPT: fireye_mision_servicio.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de misión avanzada que utiliza Behavior Trees (Árboles de 
# Comportamiento) y Nav2 para gestionar la autonomía del robot.
#
# Funcionalidad principal:
# - Expone un servicio ROS 2 llamado 'iniciar_mision'.
# - Implementa comportamientos (py_trees) para:
#   1. Establecer la pose inicial (AMCL).
#   2. Navegar a puntos de inspección específicos.
#   3. Gestionar tiempos de espera y escaneo de sensores.
#   4. Retornar automáticamente a la base.
#
# Este nodo centraliza la lógica de alto nivel, permitiendo que
# el robot ejecute misiones complejas de forma secuencial y robusta.
# ==============================================================

import rclpy
import py_trees
import time
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_srvs.srv import Trigger

class SetInitialPose(py_trees.behaviour.Behaviour):
    """
    Comportamiento del BT para establecer la pose inicial del robot.
    
    Publica directamente en el tópico '/initialpose' para asegurar
    que el sistema de localización (AMCL) sepa dónde está el robot.
    """
    def __init__(self, name, node):
        super().__init__(name)
        self.node = node
        self.publisher = self.node.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )

    def update(self):
        """
        Publica la pose (0,0) con covarianza y devuelve SUCCESS.
        """
        print(f"  [BT] Publicando pose inicial directamente a /initialpose...")
        
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.node.get_clock().now().to_msg()
        
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0
        
        msg.pose.pose.orientation.w = 1.0
        
        # Covarianza necesaria para inicializar el filtro de partículas
        msg.pose.covariance = [0.0] * 36
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06

        for _ in range(3):
            self.publisher.publish(msg)
            time.sleep(0.1)

        print(f"  [BT] Pose publicada. Esperando un momento...")
        time.sleep(2.0)
        return py_trees.common.Status.SUCCESS

class NavToPose(py_trees.behaviour.Behaviour):
    """
    Comportamiento del BT para navegar a una coordenada específica.
    
    Utiliza el BasicNavigator de Nav2 para gestionar la planificación
    y ejecución de la trayectoria.
    """
    def __init__(self, name, nav, x, y):
        super().__init__(name)
        self.nav = nav
        self.x = x
        self.y = y

    def initialise(self):
        """
        Envía la meta de navegación al servidor de Nav2.
        """
        print(f"  [BT] Enviando robot a {self.name}...")
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.nav.get_clock().now().to_msg()
        goal.pose.position.x = self.x
        goal.pose.position.y = self.y
        goal.pose.orientation.w = 1.0
        self.nav.goToPose(goal)

    def update(self):
        """
        Monitoriza el estado de la navegación.
        """
        if not self.nav.isTaskComplete():
            return py_trees.common.Status.RUNNING
        
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            print(f"  [BT] ¡Meta alcanzada!")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

class WaitNode(py_trees.behaviour.Behaviour):
    """
    Comportamiento del BT para realizar una pausa temporal.
    
    Simula una tarea de inspección o escaneo estático.
    """
    def __init__(self, name, seconds):
        super().__init__(name)
        self.seconds = seconds
        self.start_time = None

    def initialise(self):
        """
        Registra el tiempo de inicio de la espera.
        """
        print(f"  [BT] Iniciando inspección de {self.seconds} segundos...")
        self.start_time = time.time()

    def update(self):
        """
        Devuelve RUNNING hasta que transcurra el tiempo configurado.
        """
        if time.time() - self.start_time < self.seconds:
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.SUCCESS

class FireyeMisionServicio(Node):
    """
    Nodo de ROS 2 que orquestra la misión mediante un servicio de disparo (Trigger).
    """
    def __init__(self):
        super().__init__('fireye_mision_servicio')
        self.get_logger().info('Nodo de servicio de misión iniciado')
        
        self.nav = BasicNavigator()
        self.srv = self.create_service(Trigger, 'iniciar_mision', self.mision_callback)
        self.get_logger().info('Servicio listo, esperando llamada...')

    def mision_callback(self, request, response):
        """
        Define y ejecuta el árbol de comportamiento de la misión.
        """
        self.get_logger().info('Misión recibida. Esperando Nav2...')
        self.nav.waitUntilNav2Active()

        # Configuración de coordenadas
        PUNTO_MISION = {"x": 6.447230, "y": -0.803581}
        PUNTO_BASE   = {"x": 0.0,      "y": 0.0}

        # Construcción de la secuencia lógica del árbol
        root = py_trees.composites.Sequence(name="Misión Fireye", memory=True)
        root.add_children([
            SetInitialPose("Localizar Robot", self),
            NavToPose("Zona de Inspección", self.nav, PUNTO_MISION["x"], PUNTO_MISION["y"]),
            WaitNode("Esperar/Escanear", 5),
            NavToPose("Volver a Base", self.nav, PUNTO_BASE["x"], PUNTO_BASE["y"]),
        ])

        # Ejecución del árbol mediante 'ticks'
        try:
            while rclpy.ok():
                root.tick_once()
                if root.status == py_trees.common.Status.SUCCESS:
                    response.success = True
                    response.message = 'Misión completada correctamente'
                    break
                elif root.status == py_trees.common.Status.FAILURE:
                    response.success = False
                    response.message = 'Misión fallida'
                    break
                time.sleep(0.1)
        except Exception as e:
            response.success = False
            response.message = f'Error: {str(e)}'

        return response

def main(args=None):
    """
    Punto de entrada para el servicio de misión.
    """
    rclpy.init(args=args)
    service = FireyeMisionServicio()
    
    try:
        rclpy.spin(service)
    except KeyboardInterrupt:
        service.get_logger().info('Cerrando el nodo service')
    finally:
        service.destroy_node()
        rclpy.shutdown()

if __name__=='__main__':
    main()