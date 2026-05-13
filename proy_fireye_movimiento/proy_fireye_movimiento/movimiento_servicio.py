# ==============================================================
# SCRIPT: movimiento_servicio.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de servicio que permite el control directo del movimiento
# del robot FirEye mediante peticiones de alto nivel.
#
# Funcionalidad principal:
# - Expone el servicio 'movimiento' usando la interfaz personalizada.
# - Traduce comandos de texto ("derecha", "parar", etc.) en
#   mensajes de velocidad de tipo geometry_msgs/Twist.
# - Publica continuamente en el tópico 'cmd_vel' para controlar
#   el actuador del robot o el simulador.
# ==============================================================

# Importar mensajes
from geometry_msgs.msg import Twist
from proy_fireye_interfaces.srv import MiMovimientoMsg

# importar biblioteca Python ROS2
import rclpy
from rclpy.node import Node

class Service(Node):
    """
    Clase que implementa un nodo de servicio ROS 2 para el control de movimiento.

    Esta clase gestiona un servidor de servicio que recibe comandos de direccion
    y los traduce en comandos de velocidad (Twist) publicados en el topic cmd_vel.
    """

    def __init__(self):
        """
        Inicializa el nodo 'movimiento_servicio', crea el servidor de servicio
        y el publicador para los comandos de velocidad.
        """
        # constructor con el nombre del nodo
        super().__init__('movimiento_servicio')
        
        # declara el objeto servicio pasando como parametros
        # tipo de mensaje, nombre del servicio y callback del servicio
        self.srv = self.create_service(MiMovimientoMsg, 'movimiento', self.my_first_service_callback)

        # declara el objeto publisher pasando como parametros
        # tipo de mensaje, nombre del topic y tamaño de la cola
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def my_first_service_callback(self, request, response):
        """
        Callback que procesa las peticiones de movimiento recibidas por el servicio.

        Args:
            request (MiMovimientoMsg.Request): Objeto que contiene el string 'move' 
                                               con la instruccion de movimiento.
            response (MiMovimientoMsg.Response): Objeto de respuesta que indica 
                                                 el exito de la operacion.

        Returns:
            MiMovimientoMsg.Response: Respuesta con el campo 'success' actualizado.
        """
        # crea un mensaje tipo Twist
        msg = Twist()

        if request.move == "derecha":
            # rellena el mensaje msg con la velocidad angular y lineal
            # necesaria para hacer un giro a la derecha
            msg.linear.x = 0.1
            msg.angular.z = -0.2
            # publica el mensaje
            self.publisher.publish(msg)
            # imprime mensaje informando del movimiento
            self.get_logger().info('Girando hacia la derecha')
            # devuelve la respuesta
            response.success = True
        elif request.move == "izquierda":
            # rellena el mensaje msg con la velocidad angular y lineal
            # necesaria para hacer un giro a la izquierda
            msg.linear.x = 0.1
            msg.angular.z = 0.2
            # publica el mensaje
            self.publisher.publish(msg)
            # imprime mensaje informando del movimiento
            self.get_logger().info('Girando hacia la izquierda')
            # devuelve la respuesta
            response.success = True
        elif request.move == "delante":
            # rellena el mensaje msg con la velocidad angular y lineal
            # necesaria para moverse hacia delante
            msg.linear.x = 0.1
            msg.angular.z = 0.0
            # publica el mensaje
            self.publisher.publish(msg)
            # imprime mensaje informando del movimiento
            self.get_logger().info('Hacia delante')
            # devuelve la respuesta
            response.success = True
        elif request.move == "atras":
            # rellena el mensaje msg con la velocidad angular y lineal
            # necesaria para moverse hacia atras
            msg.linear.x = -0.1
            msg.angular.z = 0.0
            # publica el mensaje
            self.publisher.publish(msg)
            # imprime mensaje informando del movimiento
            self.get_logger().info('Hacia atras')
            # devuelve la respuesta
            response.success = True
        elif request.move == "parar":
            # rellena el mensaje msg con la velocidad angular y lineal
            # necesaria para parar el robot
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            # publica el mensaje
            self.publisher.publish(msg)
            # imprime mensaje informando del movimiento
            self.get_logger().info('Parando')
            # devuelve la respuesta
            response.success = True
        else:
            # estado de la respuesta
            # si no se ha dado ningun caso anterior
            response.success = False

        # devuelve la respuesta
        return response

def main(args=None):
    """
    Punto de entrada principal para ejecutar el nodo de servicio de movimiento.

    Args:
        args (list, optional): Argumentos de linea de comandos pasados al inicializar rclpy.
    """
    # inicializa la comunicacion ROS2
    rclpy.init(args=args)
    # creamos el nodo
    service = Service()
    try:
        # dejamos abierto el servicio
        rclpy.spin(service)
    except KeyboardInterrupt:
        service.get_logger().info('Cerrando el nodo service')
    finally:
        # destruimos el nodo
        service.destroy_node()
        # cerramos la comunicacion
        rclpy.shutdown()

# definimos el ejecutable
if __name__=='__main__':
    main()