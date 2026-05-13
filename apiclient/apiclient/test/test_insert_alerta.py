# ==============================================================
# SCRIPT: test_insert_alerta.py
# --------------------------------------------------------------
# AUTOR: Manuel Perez
# FECHA: 12-05-2026
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Nodo de prueba técnica para validar la inserción de alertas desde ROS 2 hacia el backend de FirEye.
# Funcionalidad principal:
# - Ejecutar una petición HTTP POST única al iniciar.
# - Validar la comunicación con el endpoint /api/alerta.
# - Comprobar la respuesta del controlador universal de la API.
# Este script es una herramienta de depuración para asegurar que la cadena ROS 2 -> API -> PostgreSQL funciona correctamente.
# ==============================================================

## ros2 run apiclient test_insert_alerta
import rclpy
from rclpy.node import Node
import requests


class TestInsertAlerta(Node):
    """
    Nodo de prueba para la inserción manual de alertas en la base de datos.

    Realiza una petición síncrona al backend para verificar que los datos
    son procesados correctamente por el script de consulta 'alertas.js'.
    """
    def __init__(self):
        """
        Inicializa el nodo y ejecuta la prueba de inserción de forma inmediata.
        """
        super().__init__('test_insert_alerta')

        self.get_logger().info("INSERT ALERTA TEST")

    # ==========================================================
    # CONFIGURACIÓN DEL PAYLOAD
    # ==========================================================
    # Define los datos simulados de la incidencia.
    # tipo_nombre debe existir en la tabla 'tipos_alerta'.
        payload = {
            "tipo_nombre": "Incendio",
            "confianza": 0.92,
            "x": 10,
            "y": 20,
            "descripcion": "TEST INSERT ROS2"
        }
        
    # ==========================================================
    # EJECUCIÓN DE LA PETICIÓN HTTP
    # ==========================================================
        try:
            res = requests.post("http://localhost:3000/api/alerta", json=payload, timeout=2)
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
    node = TestInsertAlerta()
    rclpy.spin_once(node, timeout_sec=1)
    node.destroy_node()
    rclpy.shutdown()