import rclpy
from rclpy.node import Node
import requests
from std_msgs.msg import String
from example_interfaces.srv import Trigger, SetBool # Usamos interfaces estándar por ahora

class ApiHubNode(Node):
    def __init__(self):
        super().__init__('api_hub_node')
        self.api_base_url = "http://localhost:3000/api"

        # --- 1. SUSCRIPTOR (Para Updates continuos como la posición) ---
        # No bloquea al robot. Él publica y se olvida.
        self.sub_pos = self.create_subscription(String, 'robot_telemetria', self.telemetria_callback, 10)

        # --- 2. SERVICIO DE CONSULTA (Para traer datos: SELECT) ---
        self.srv_get = self.create_service(Trigger, 'consultar_datos', self.handle_get)

        # --- 3. SERVICIO DE ACCIÓN (Para insertar o actualizar: INSERT/UPDATE) ---
        self.srv_post = self.create_service(SetBool, 'ejecutar_accion', self.handle_post)

        self.get_logger().info('🚀 Hub de Comunicación FirEye Operativo')

    # Lógica para recibir Telemetría (Topic)
    def telemetria_callback(self, msg):
        try:
            # Mandamos los datos a un endpoint de actualización
            requests.post(f"{self.api_base_url}/robot/update", json={"data": msg.data}, timeout=0.1)
        except:
            pass

    # Lógica para Consultar (GET)
    def handle_get(self, request, response):
        try:
            res = requests.get(f"{self.api_base_url}/config/parametros")
            if res.status_code == 200:
                response.success = True
                response.message = str(res.json()) # Devolvemos lo que diga la DB
            return response
        except Exception as e:
            response.success = False
            return response

    # Lógica para Insertar/Actualizar (POST)
    def handle_post(self, request, response):
        # El request.data (booleano) podría indicar si es una limpieza o un reset
        payload = {"accion": "reset_sistema", "valor": request.data}
        try:
            res = requests.post(f"{self.api_base_url}/acciones/ejecutar", json=payload)
            response.success = (res.status_code == 200)
            return response
        except:
            response.success = False
            return response
        

## Ejemplo de uso:
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