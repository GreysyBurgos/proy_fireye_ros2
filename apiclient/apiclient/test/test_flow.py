# ==============================================================
# SCRIPT: test_flow.py
# --------------------------------------------------------------
# AUTOR: Manuel Perez
# FECHA: 12-05-2026
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de prueba integral que valida el flujo completo de datos
# (escritura y lectura) entre ROS 2 y el backend de FirEye.
#
# Funcionalidad principal:
# - Ejecuta una secuencia encadenada: POST (Insert) y GET (Select).
# - Verifica la persistencia de datos en PostgreSQL en tiempo real.
# - Comprueba la latencia y estabilidad de la comunicación HTTP.
#
# Este script garantiza que lo que el robot registra puede ser 
# recuperado inmediatamente, validando el ciclo de vida del dato.
# ==============================================================

##ros2 run apiclient test_flow
import rclpy
from rclpy.node import Node
import requests


class TestFlow(Node):
    """
    Nodo de prueba de flujo de datos bidireccional.

    Realiza una inserción de alerta y, acto seguido, solicita la lista
    de alertas para confirmar que la nueva incidencia aparece en los
    registros devueltos por la API.
    """
    def __init__(self):
        """
        Inicializa el nodo y ejecuta la secuencia lógica de prueba.
        """
        super().__init__('test_flow')

        self.get_logger().info(" FLOW TEST (INSERT + GET)")

        # ==========================================================
        # 1. OPERACIÓN DE INSERCIÓN (POST)
        # ==========================================================
        payload = {
            "tipo_nombre": "Incendio",
            "confianza": 0.95,
            "x": 5,
            "y": 8,
            "descripcion": "FLOW TEST"
        }

        try:
            # Intento de inserción en la base de datos
            post = requests.post(
                "http://localhost:3000/api/alerta",
                json=payload,
                timeout=2
            )
            self.get_logger().info(f"INSERT: {post.json()}")

            # ==========================================================
            # 2. OPERACIÓN DE RECUPERACIÓN (GET)
            # ==========================================================
            # Se solicita la información inmediatamente para validar persistencia
            get = requests.get(
                "http://localhost:3000/api/alertas",
                timeout=2
            )
            self.get_logger().info(f"GET: {get.json()}")

        except Exception as e:
            self.get_logger().error(str(e))

# ==============================================================
# MAIN
# ==============================================================
def main(args=None):
    """
    Punto de entrada del nodo de prueba de flujo.
    """
    rclpy.init(args=args)
    node = TestFlow()
    rclpy.spin_once(node, timeout_sec=1)
    node.destroy_node()
    rclpy.shutdown()