# ==============================================================
# SCRIPT: connection_node.py
# --------------------------------------------------------------
# AUTOR: Manuel Perez
# FECHA: 12-05-2026
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo intermediario en ROS 2 que actúa como puente entre el
# sistema robótico y una API REST (FirEye backend en Node.js).
#
# Funcionalidad principal:
# - Recibe telemetría del robot mediante topics ROS 2.
# - Envía datos del robot a una API REST mediante HTTP POST.
# - Expone un servicio ROS 2 para consultas GET al backend.
# - Expone un servicio ROS 2 para ejecutar acciones remotas vía POST.
#
# En resumen, centraliza la comunicación entre ROS 2 y la API web,
# desacoplando la lógica del robot del sistema backend.
# ============================================================== 
import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import String
from example_interfaces.srv import Trigger, SetBool 

class ApiHubNode(Node):
    """
    Nodo intermediario entre ROS 2 y la API REST de FirEye.

    Este nodo actúa como un puente de comunicación entre:
    - El ecosistema ROS 2 del robot.
    - El backend HTTP/REST desarrollado en Node.js.

    Funcionalidades principales:
    -----------------------------
    1. Recibir telemetría del robot mediante topics ROS.
    2. Consultar información de la base de datos mediante servicios ROS.
    3. Ejecutar acciones remotas mediante peticiones POST.
    """

    def __init__(self):
        """
        Inicializa el nodo ROS y registra:
        - Subscribers
        - Services
        - Configuración base de la API
        """

        super().__init__('api_hub_node')

        self.api_base_url = "http://localhost:3000/api"

        # ==========================================================
        # SUBSCRIPTOR DE TELEMETRÍA
        # ==========================================================
        #
        # Escucha información publicada por el robot:
        # posición, batería, sensores, etc.
        #
        # El robot publica datos y este nodo los reenvía a la API.
        #
        self.sub_pos = self.create_subscription(String, 'robot_telemetria', self.telemetria_callback, 10)

        # ==========================================================
        # SERVICIO GET (CONSULTAS)
        # ==========================================================
        #
        # Servicio ROS usado para solicitar datos del backend.
        #
        self.srv_get = self.create_service(Trigger, 'consultar_datos', self.handle_get)

        # ==========================================================
        # SERVICIO POST (ACCIONES)
        # ==========================================================
        #
        # Servicio ROS usado para ejecutar acciones remotas:
        # resets, cambios de estado, comandos, etc.
        #
        self.srv_post = self.create_service(SetBool, 'ejecutar_accion', self.handle_post)

        self.get_logger().info('🚀 Hub de Comunicación FirEye Operativo')

    
    # ==============================================================
    # CALLBACK TELEMETRÍA
    # ==============================================================
    def telemetria_callback(self, msg):
        """
        Callback ejecutado al recibir telemetría del robot.

        Parameters
        ----------
        msg : std_msgs.msg.String
            Mensaje recibido desde ROS 2.

        Funcionamiento
        ---------------
        Envía la información recibida al backend mediante HTTP POST.

        Ejemplo de contenido:
        ---------------------
        {
            "x": 1.2,
            "y": 4.5,
            "battery": 80
        }
        """

        try:
            requests.post(
                f"{self.api_base_url}/robot/update",
                json={"data": msg.data},
                timeout=0.1
            )

        except:
            pass


    # ==============================================================
    # SERVICIO GET
    # ==============================================================
    def handle_get(self, request, response):
        """
        Gestiona peticiones GET desde ROS 2.

        Parameters
        ----------
        request : Trigger.Request
            Petición ROS recibida.

        response : Trigger.Response
            Respuesta que será devuelta al cliente ROS.

        Returns
        -------
        Trigger.Response
            Resultado de la operación.
        """

        try:
            res = requests.get(
                f"{self.api_base_url}/config/parametros"
            )

            if res.status_code == 200:
                response.success = True
                response.message = str(res.json())

            return response

        except:
            response.success = False
            return response
        
    # ==============================================================
    # SERVICIO POST
    # ==============================================================
    def handle_post(self, request, response):
        """
        Gestiona acciones remotas mediante HTTP POST.

        Parameters
        ----------
        request : SetBool.Request
            Petición ROS recibida.

        response : SetBool.Response
            Resultado de la operación.

        Returns
        -------
        SetBool.Response
            Estado final de la operación.
        """

        payload = {
            "accion": "reset_sistema",
            "valor": request.data
        }

        try:
            res = requests.post(
                f"{self.api_base_url}/acciones/ejecutar",
                json=payload
            )

            response.success = (res.status_code == 200)

            return response

        except:
            response.success = False
            return response


# ==============================================================
# MAIN
# ==============================================================
def main(args=None):
    """
    Punto de entrada del nodo ROS 2.
    """

    rclpy.init(args=args)

    node = ApiHubNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


# ==============================================================
# EJECUCIÓN DIRECTA
# ==============================================================
if __name__ == '__main__':
    main()

# ==============================================================
# EJEMPLOS DE USO
# ==============================================================
# INSERT::
# En el nodo de control
#msg = String()
#msg.data = '{"x": 1.2, "y": 4.5, "battery": 80}'
#self.publisher_telemetria.publish(msg)

# GET:
#client = self.create_client(Trigger, 'consultar_datos')
#req = Trigger.Request()
#future = client.call_async(req)
# Al terminar el future, tendrás en 'message' los datos de la DB

# enviar alerta desde ros2:
#import requests

#def enviar_incendio(self, pos_x, pos_y, score_ia):
#    url = "http://localhost:3000/api/alerta" # O la IP de la web
#    payload = {
#        "tipo_nombre": "Incendio",   # Debe coincidir con los SEEDS de tu SQL
#        "confianza": score_ia,       # ej: 0.98
#        "x": pos_x,
#        "y": pos_y,
#        "descripcion": "Detección de llama en el pasillo central"
#    }
    
#    try:
#        response = requests.post(url, json=payload)
#        print(response.json())
#    except Exception as e:
#        print(f"Error: {e}")    