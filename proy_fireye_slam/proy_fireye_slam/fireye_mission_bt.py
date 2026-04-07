import rclpy
import py_trees
import time
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# --- NODO 1: ESTABLECER POSE INICIAL (Bypass Manual) ---
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

# --- NODO 2: NAVEGAR A UN PUNTO ---
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

# --- NODO 3: ESPERAR ---
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

def main():
    rclpy.init()
    # El Navigator es un Nodo de ROS 2
    nav = BasicNavigator()
    
    print("Esperando a que Nav2 esté activo...")
    nav.waitUntilNav2Active()

    # CONFIGURACIÓN DE PUNTOS
    PUNTO_MISION = {"x": 6.447230, "y": -0.803581}
    PUNTO_BASE = {"x": 0.0, "y": 0.0}

    # CONSTRUCCIÓN DEL ÁRBOL
    root = py_trees.composites.Sequence(name="Misión Fireye", memory=True)
    
    # IMPORTANTE: Pasamos el objeto 'nav' que actúa como nodo
    localizar = SetInitialPose("Localizar Robot", nav)
    ir_a_inspeccion = NavToPose("Zona de Inspección", nav, PUNTO_MISION["x"], PUNTO_MISION["y"])
    esperar = WaitNode("Esperar/Escanear", 5)
    volver_a_casa = NavToPose("Volver a Base", nav, PUNTO_BASE["x"], PUNTO_BASE["y"])

    root.add_children([localizar, ir_a_inspeccion, esperar, volver_a_casa])

    print("\n--- INICIANDO ÁRBOL DE COMPORTAMIENTO ---")
    try:
        while rclpy.ok():
            root.tick_once()
            if root.status == py_trees.common.Status.SUCCESS:
                print("\n[!] Misión completada con éxito.")
                break
            elif root.status == py_trees.common.Status.FAILURE:
                print("\n[X] La misión ha fallado.")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()

if __name__ == '__main__':
    main()