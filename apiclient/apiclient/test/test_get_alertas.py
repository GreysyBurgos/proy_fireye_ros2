# ==============================================================
# SCRIPT: test_get_alertas.py
# --------------------------------------------------------------
# AUTOR: Manuel Perez
# FECHA: 12-05-2026
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de prueba técnica para validar la recuperación de alertas
# desde el backend de FirEye hacia ROS 2.
#
# Funcionalidad principal:
# - Ejecutar una petición HTTP GET única al iniciar.
# - Validar la comunicación con el endpoint /api/alertas.
# - Comprobar la recepción de datos desde PostgreSQL procesados 
#   por el controlador universal.
#
# Este script permite verificar que el flujo de datos desde la 
# base de datos hasta el entorno del robot es correcto.
# ==============================================================

## ros2 run apiclient test_get_alertas
import rclpy
from rclpy.node import Node
import requests


class TestGetAlertas(Node):
    """
    Nodo de prueba para la consulta de alertas registradas.

    Realiza una petición síncrona al backend para obtener el listado
    de alertas, verificando la integridad de la conexión y el formato
    de respuesta del servidor Node.js.
    """
    def __init__(self):
        """
        Inicializa el nodo y ejecuta la prueba de lectura de forma inmediata.
        """
        super().__init__('test_get_alertas')

        self.get_logger().info(" GET ALERTAS TEST")

        # ==========================================================
        # EJECUCIÓN DE LA PETICIÓN HTTP (GET)
        # ==========================================================
        try:
            # Se realiza el GET al endpoint que devuelve el histórico/activas
            res = requests.get("http://localhost:3000/api/alertas", timeout=2)
            
            # Registro del resultado en los logs de ROS 2
            self.get_logger().info(f"RESPUESTA: {res.json()}")
            
        except Exception as e:
            self.get_logger().error(str(e))

# ==============================================================
# MAIN
# ==============================================================
def main(args=None):
    """
    Punto de entrada del nodo de prueba.
    """
    rclpy.init(args=args)
    node = TestGetAlertas()
    rclpy.spin_once(node, timeout_sec=1)
    node.destroy_node()
    rclpy.shutdown()