# ==============================================================
# SCRIPT: fireye_mission_bt.py
# --------------------------------------------------------------
# AUTOR: 
# FECHA: 
# --------------------------------------------------------------
# DESCRIPCIÓN:
# Implementación de un Árbol de Comportamiento (Behavior Tree) 
# para la gestión autónoma de misiones del robot FirEye.
#
# Funcionalidad principal:
# - Orquestación de tareas mediante py_trees.
# - Secuenciación de localización inicial, navegación y espera.
# - Uso del BasicNavigator para interactuar con el stack Nav2.
#
# Este script define la lógica de ejecución continua del robot,
# asegurando que cada etapa de la misión se complete antes de
# proceder a la siguiente.
# ==============================================================

import rclpy
import py_trees
import time
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# ==============================================================
# NODO 1: ESTABLECER POSE INICIAL (Bypass Manual)
# ==============================================================
class SetInitialPose(py_trees.behaviour.Behaviour):
    """
    Comportamiento para forzar la localización inicial en AMCL.
    
    Este nodo crea un publicador temporal para enviar la pose (0,0)
    al tópico '/initialpose', permitiendo que el robot se sitúe
    en el mapa al comenzar la misión.
    """
    def __init__(self, name, node):
        """
        Inicializa el comportamiento y el publicador de ROS 2.
        """
        super().__init__(name)
        self.node = node
        self.publisher = self.node.create_publisher(
            PoseWithCovarianceStamped, 
            '/initialpose', 
            10
        )

    def update(self):
        """
        Ejecuta la publicación de la pose y devuelve SUCCESS tras una pausa.
        """
        print(f"  [BT] Publicando pose inicial directamente a /initialpose...")
        
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.node.get_clock().now().to_msg()
        
        # Posición inicial configurada en el origen (0,0,0)
        msg.pose.pose.position.x = 0.0
        msg.pose.pose.position.y = 0.0
        msg.pose.pose.position.z = 0.0
        
        # Orientación neutra (mirando hacia adelante)
        msg.pose.pose.orientation.w = 1.0
        
        # Matriz de covarianza estándar para inicialización de AMCL
        msg.pose.covariance = [0.0] * 36
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06

        # Publicación múltiple para mitigar pérdidas de paquetes
        for _ in range(3):
            self.publisher.publish(msg)
            time.sleep(0.1)

        print(f"  [BT] Pose publicada. Esperando un momento...")
        time.sleep(2.0)
        return py_trees.common.Status.SUCCESS

# ==============================================================
# NODO 2: NAVEGAR A UN PUNTO
# ==============================================================
class NavToPose(py_trees.behaviour.Behaviour):
    """
    Comportamiento para desplazar el robot a una coordenada.
    
    Gestiona el ciclo de vida de una meta de navegación:
    envío de la pose, monitorización y retorno de estado final.
    """
    def __init__(self, name, nav, x, y):
        """
        Define el destino y el objeto navigator.
        """
        super().__init__(name)
        self.nav = nav
        self.x = x
        self.y = y

    def initialise(self):
        """
        Envía la solicitud de navegación a Nav2 al entrar en el estado.
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
        Comprueba periódicamente si el robot ha llegado a su destino.
        """
        if not self.nav.isTaskComplete():
            return py_trees.common.Status.RUNNING
        
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            print(f"  [BT] ¡Meta alcanzada!")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE

# ==============================================================
# NODO 3: ESPERAR
# ==============================================================
class WaitNode(py_trees.behaviour.Behaviour):
    """
    Comportamiento de bloqueo temporal (pausa activa).
    
    Útil para realizar tareas de inspección visual o escaneo 
    con LIDAR en un punto de interés.
    """
    def __init__(self, name, seconds):
        """
        Define el tiempo de espera en segundos.
        """
        super().__init__(name)
        self.seconds = seconds
        self.start_time = None

    def initialise(self):
        """
        Captura el tiempo de inicio al activarse el comportamiento.
        """
        print(f"  [BT] Iniciando inspección de {self.seconds} segundos...")
        self.start_time = time.time()

    def update(self):
        """
        Mantiene el estado RUNNING hasta que se cumple el tiempo.
        """
        if time.time() - self.start_time < self.seconds:
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.SUCCESS

# ==============================================================
# MAIN: ORQUESTACIÓN DEL ÁRBOL
# ==============================================================
def main():
    """
    Punto de entrada para la ejecución del Árbol de Comportamiento.
    """
    rclpy.init()
    
    # El Navigator de Nav2 gestiona la comunicación con los servidores de acción
    nav = BasicNavigator()
    
    print("Esperando a que Nav2 esté activo...")
    nav.waitUntilNav2Active()

    # Configuración de Waypoints
    PUNTO_MISION = {"x": 6.447230, "y": -0.803581}
    PUNTO_BASE = {"x": 0.0, "y": 0.0}

    # Definición de la secuencia raíz (Sequence con memoria)
    root = py_trees.composites.Sequence(name="Misión Fireye", memory=True)
    
    # Instanciación de comportamientos
    localizar = SetInitialPose("Localizar Robot", nav)
    ir_a_inspeccion = NavToPose("Zona de Inspección", nav, PUNTO_MISION["x"], PUNTO_MISION["y"])
    esperar = WaitNode("Esperar/Escanear", 5)
    volver_a_casa = NavToPose("Volver a Base", nav, PUNTO_BASE["x"], PUNTO_BASE["y"])

    # Composición del árbol
    root.add_children([localizar, ir_a_inspeccion, esperar, volver_a_casa])

    print("\n--- INICIANDO ÁRBOL DE COMPORTAMIENTO ---")
    try:
        while rclpy.ok():
            # Ejecuta un ciclo del árbol
            root.tick_once()
            
            # Evaluación de estados finales
            if root.status == py_trees.common.Status.SUCCESS:
                print("\n[!] Misión completada con éxito.")
                break
            elif root.status == py_trees.common.Status.FAILURE:
                print("\n[X] La misión ha fallado.")
                break
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[!] Interrupción manual detectada.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()