#importar  biblioteca Python ROS2
import rclpy
import py_trees
import time
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_srvs.srv import Trigger

class SetInitialPose(py_trees.behaviour.Behaviour):
    def __init__(self, name, node):
        super().__init__(name)
        self.node = node
        # Creamos nuestro propio publicador para evitar el fallo del Navigator
        self.publisher = self.node.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )

    def update(self):
        print(f"  [BT] Publicando pose inicial directamente a /initialpose...")
        
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.node.get_clock().now().to_msg()
        
        # Posición (0,0,0)
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0
        
        # Orientación (Frente)
        msg.pose.pose.orientation.x = 0.0
        msg.pose.pose.orientation.y = 0.0
        msg.pose.pose.orientation.z = 0.0
        msg.pose.pose.orientation.w = 1.0
        
        # Covarianza obligatoria para AMCL
        msg.pose.covariance = [0.0] * 36
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06

        # Publicamos 3 veces para asegurar que AMCL lo reciba
        for _ in range(3):
            self.publisher.publish(msg)
            time.sleep(0.1)

        print(f"  [BT] Pose publicada. Esperando un momento...")
        time.sleep(2.0)
        return py_trees.common.Status.SUCCESS

class NavToPose(py_trees.behaviour.Behaviour):
    def __init__(self, name, nav, x, y):
        super().__init__(name)
        self.nav = nav
        self.x = x
        self.y = y

    def initialise(self):
        print(f"  [BT] Enviando robot a {self.name}...")
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.nav.get_clock().now().to_msg()
        goal.pose.position.x = self.x
        goal.pose.position.y = self.y
        goal.pose.orientation.w = 1.0
        self.nav.goToPose(goal)

    def update(self):
        if not self.nav.isTaskComplete():
            return py_trees.common.Status.RUNNING
        
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            print(f"  [BT] ¡Meta alcanzada!")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

class WaitNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, seconds):
        super().__init__(name)
        self.seconds = seconds
        self.start_time = None

    def initialise(self):
        print(f"  [BT] Iniciando inspección de {self.seconds} segundos...")
        self.start_time = time.time()

    def update(self):
        if time.time() - self.start_time < self.seconds:
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.SUCCESS

class FireyeMisionServicio(Node):
    def __init__(self):
        super().__init__('fireye_mision_servicio')
        self.get_logger().info('Nodo de servicio de misión iniciado')
        self.nav = BasicNavigator()
        self.nav.waitUntilNav2Active()
        self.srv = self.create_service(Trigger, 'iniciar_mision', self.mision_callback)
        self.get_logger().info('Misión iniciada')

    def mision_callback(self, request, response):
            # CONFIGURACIÓN DE PUNTOS
        PUNTO_MISION = {"x": 6.447230, "y": -0.803581}
        PUNTO_BASE = {"x": 0.0, "y": 0.0}

        root = py_trees.composites.Sequence(name="Misión Fireye", memory=True)

        localizar = SetInitialPose("Localizar Robot", self)
        ir_a_inspeccion = NavToPose("Zona de Inspección", self.nav, PUNTO_MISION["x"], PUNTO_MISION["y"])
        esperar = WaitNode("Esperar/Escanear", 5)
        volver_a_casa = NavToPose("Volver a Base", self.nav, PUNTO_BASE["x"], PUNTO_BASE["y"])

        root.add_children([localizar, ir_a_inspeccion, esperar, volver_a_casa])

        try:
            while rclpy.ok():
                root.tick_once()
                if root.status == py_trees.common.Status.SUCCESS:
                    response.success = True
                    response.message = 'Misión iniciada correctamente'
                    break
                elif root.status == py_trees.common.Status.FAILURE:
                    response.success = False
                    response.message = 'Misión fallida'
                    break
        except Exception as e:
            response.success = False
            response.message = f'Error durante la misión: {str(e)}'
        return response

def main(args=None):
    # inicializa la comunicacion ROS2
    rclpy.init(args=args)
    # creamos el nodo
    service = FireyeMisionServicio()
    try:
        #dejamos abierto el servicio
        rclpy.spin(service)
    except KeyboardInterrupt:
        service.get_logger().info('Cerrando el nodo service')
    finally:
        #destruimos el nodo
        service.destroy_node()
        #cerramos la comunicacion
        rclpy.shutdown()
if __name__=='__main__':
    main()