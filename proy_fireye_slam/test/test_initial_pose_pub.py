import pytest
import rclpy
import time
from geometry_msgs.msg import PoseWithCovarianceStamped
from proy_fireye_slam.fireye_mission_bt import SetInitialPose

class TestInitialPosePublishing:
    
    @classmethod
    def setup_class(cls):
        # Iniciamos ROS 2 para los tests
        rclpy.init()

    @classmethod
    def teardown_class(cls):
        # Apagamos ROS 2 al terminar
        rclpy.shutdown()

    def test_publish_initial_pose(self):
        # 1. Creamos un nodo "ficticio" para poder usar publicadores y suscriptores
        test_node = rclpy.create_node('test_initial_pose_node')
        
        # 2. Variable para guardar el mensaje si llega
        mensaje_recibido = []

        # 3. Creamos un suscriptor espía en /initialpose
        def callback_espia(msg):
            mensaje_recibido.append(msg)
            
        test_node.create_subscription(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            callback_espia, 
            10
        )

        # 4. Instanciamos nuestro nodo del Behavior Tree usando el nodo ficticio
        bt_node = SetInitialPose(name="TestPose", node=test_node)
        
        # 5. Ejecutamos la función (debería publicar)
        bt_node.update()

        # 6. Damos un poco de tiempo a ROS para que procese los mensajes
        start_time = time.time()
        while time.time() - start_time < 2.0 and not mensaje_recibido:
            rclpy.spin_once(test_node, timeout_sec=0.1)

        # 7. LA PRUEBA DE FUEGO: ¿Ha llegado algo al array espía?
        assert len(mensaje_recibido) > 0, "No se publicó ningún mensaje en /initialpose"
        
        # 8. Comprobamos que el mensaje tiene la covarianza que le pusimos (el arreglo Anti-Bug)
        msg = mensaje_recibido[0]
        assert msg.pose.covariance[0] == 0.25, "La covarianza de X no es la correcta (0.25)"

        test_node.destroy_node()