import rclpy
import py_trees
import time
import math

from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from proy_fireye_interfaces.action import Mision

import threading


# ──────────────────────────────────────────────────────────────────────────────
# NODO 1: ESTABLECER POSE INICIAL
# Sin sleep bloqueante — usa timestamps para esperar sin detener el executor
# ──────────────────────────────────────────────────────────────────────────────

class SetInitialPose(py_trees.behaviour.Behaviour):
    def __init__(self, name, node):
        super().__init__(name)
        self.node = node
        self._publisher = None
        self._pub_count = 0
        self._next_pub_time = None
        self._wait_until = None

    def setup(self, **kwargs):
        # Se llama UNA SOLA VEZ al iniciar el árbol, no en cada tick
        self._publisher = self.node.create_publisher(
            PoseWithCovarianceStamped, '/initialpose', 10)

    def initialise(self):
        # Se llama cada vez que el nodo pasa de IDLE a RUNNING
        self._pub_count = 0
        self._next_pub_time = time.time()
        self._wait_until = None

    def update(self):
        now = time.time()

        # Fase 1: publicar 3 veces con 100 ms de separación (sin sleep)
        if self._pub_count < 3:
            if now >= self._next_pub_time:
                msg = PoseWithCovarianceStamped()
                msg.header.frame_id = 'map'
                msg.header.stamp = self.node.get_clock().now().to_msg()
                msg.pose.pose.position.x = 0.0
                msg.pose.pose.position.y = 0.0
                msg.pose.pose.position.z = 0.0
                msg.pose.pose.orientation.x = 0.0
                msg.pose.pose.orientation.y = 0.0
                msg.pose.pose.orientation.z = 0.0
                msg.pose.pose.orientation.w = 1.0
                msg.pose.covariance = [0.0] * 36
                msg.pose.covariance[0]  = 0.25
                msg.pose.covariance[7]  = 0.25
                msg.pose.covariance[35] = 0.06
                self._publisher.publish(msg)
                self._pub_count += 1
                self._next_pub_time = now + 0.1
            return py_trees.common.Status.RUNNING

        # Fase 2: esperar 2 s para que AMCL procese la pose (sin sleep)
        if self._wait_until is None:
            self._wait_until = now + 2.0

        if now < self._wait_until:
            return py_trees.common.Status.RUNNING

        return py_trees.common.Status.SUCCESS


# ──────────────────────────────────────────────────────────────────────────────
# NODO 2: NAVEGAR A UN PUNTO
# initialise() lanza la navegación una sola vez
# update() solo consulta el estado sin bloquear
# ──────────────────────────────────────────────────────────────────────────────

class NavToPose(py_trees.behaviour.Behaviour):
    def __init__(self, name, nav, x, y, yaw_deg=0.0):
        super().__init__(name)
        self.nav = nav
        self.x = x
        self.y = y
        self.yaw_deg = yaw_deg

    def initialise(self):
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.nav.get_clock().now().to_msg()
        goal.pose.position.x = self.x
        goal.pose.position.y = self.y
        goal.pose.position.z = 0.0
        yaw = math.radians(self.yaw_deg)
        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.0
        goal.pose.orientation.z = math.sin(yaw / 2)
        goal.pose.orientation.w = math.cos(yaw / 2)
        self.nav.goToPose(goal)

    def update(self):
        if not self.nav.isTaskComplete():
            return py_trees.common.Status.RUNNING
        if self.nav.getResult() == TaskResult.SUCCEEDED:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


# ──────────────────────────────────────────────────────────────────────────────
# NODO 3: ESPERAR N SEGUNDOS
# No bloquea — usa timestamps
# Detecta cancelación desde el servidor de acción
# ──────────────────────────────────────────────────────────────────────────────

class WaitNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, seconds, goal_handle=None):
        super().__init__(name)
        self.seconds = seconds
        self.goal_handle = goal_handle  # para detectar cancelación externa
        self.start_time = None

    def initialise(self):
        self.start_time = time.time()

    def update(self):
        # Propaga cancelación desde el servidor de acción
        if self.goal_handle and self.goal_handle.is_cancel_requested:
            return py_trees.common.Status.FAILURE

        if time.time() - self.start_time < self.seconds:
            return py_trees.common.Status.RUNNING

        return py_trees.common.Status.SUCCESS


# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE RUTAS
# Cada goal construye un árbol NUEVO para evitar problemas con memory=True
# Añade rutas nuevas añadiendo un bloque elif
# ──────────────────────────────────────────────────────────────────────────────

RUTAS_DISPONIBLES = ['inspeccion_a', 'inspeccion_b', 'patrulla']


def construir_arbol(nombre_ruta: str, nav, node, goal_handle):
    root = py_trees.composites.Sequence(name=nombre_ruta, memory=True)
    localizar = SetInitialPose("Localizar Robot", node)

    if nombre_ruta == 'inspeccion_a':
        root.add_children([
            localizar,
            NavToPose("Ir a Inspección A", nav, 6.447230, -0.803581, yaw_deg=0.0),
            WaitNode("Escanear A", 5, goal_handle),
            NavToPose("Volver a Base", nav, 0.0, 0.0, yaw_deg=0.0),
        ])

    elif nombre_ruta == 'inspeccion_b':
        root.add_children([
            localizar,
            NavToPose("Ir a Inspección B", nav, -2.0, 1.5, yaw_deg=90.0),
            WaitNode("Escanear B", 5, goal_handle),
            NavToPose("Volver a Base", nav, 0.0, 0.0, yaw_deg=0.0),
        ])

    elif nombre_ruta == 'patrulla':
        root.add_children([
            localizar,
            NavToPose("Waypoint 1", nav, 2.0, 0.0,  yaw_deg=0.0),
            NavToPose("Waypoint 2", nav, 2.0, 2.0,  yaw_deg=90.0),
            NavToPose("Waypoint 3", nav, 0.0, 2.0,  yaw_deg=180.0),
            WaitNode("Pausa patrulla", 2, goal_handle),
            NavToPose("Volver a Base", nav, 0.0, 0.0, yaw_deg=270.0),
        ])

    else:
        raise ValueError(f'Ruta desconocida: {nombre_ruta}')

    # Inicializa el árbol completo (llama a setup() en todos los nodos)
    root.setup_with_descendants()
    return root


# ──────────────────────────────────────────────────────────────────────────────
# SERVIDOR DE ACCIÓN
# ──────────────────────────────────────────────────────────────────────────────

class MisionAccionServidor(Node):

    def __init__(self):
        super().__init__('mision_accion_servidor')
        self._cb_group = ReentrantCallbackGroup()
        self._navigator = BasicNavigator()

        self._action_server = ActionServer(
            self,
            Mision,
            'ejecutar_mision',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self._cb_group
        )

        self._nav2_ready = False
        # waitUntilNav2Active() es bloqueante — lo lanzamos en un hilo separado
        # para no bloquear el MultiThreadedExecutor
        threading.Thread(target=self._esperar_nav2, daemon=True).start()

        self.get_logger().info(
            f'Servidor de acción listo. Rutas disponibles: {RUTAS_DISPONIBLES}')

    # ── Nav2 en background ───────────────────────────────────────────────────

    def _esperar_nav2(self):
        self._navigator.waitUntilNav2Active()
        self._nav2_ready = True
        self.get_logger().info('Nav2 activo. El servidor acepta misiones.')

    # ── Callbacks de gestión de goal ─────────────────────────────────────────

    def goal_callback(self, goal_request):
        nombre = goal_request.nombre_ruta
        if not self._nav2_ready:
            self.get_logger().warn('Nav2 aún no está listo. Goal rechazado.')
            return GoalResponse.REJECT
        if nombre not in RUTAS_DISPONIBLES:
            self.get_logger().warn(
                f'Ruta desconocida: "{nombre}". '
                f'Disponibles: {RUTAS_DISPONIBLES}')
            return GoalResponse.REJECT
        self.get_logger().info(f'Goal aceptado: ruta "{nombre}"')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancelación solicitada.')
        self._navigator.cancelTask()
        return CancelResponse.ACCEPT

    # ── Ejecución de la misión (bucle de tick del BT) ────────────────────────

    def execute_callback(self, goal_handle):
        nombre = goal_handle.request.nombre_ruta
        self.get_logger().info(f'Ejecutando BT: "{nombre}"')

        feedback_msg = Mision.Feedback()
        result = Mision.Result()

        # Construcción del árbol para esta ruta
        try:
            arbol = construir_arbol(nombre, self._navigator, self, goal_handle)
        except ValueError as e:
            self.get_logger().error(str(e))
            goal_handle.abort()
            result.exito = False
            result.mensaje = str(e)
            return result

        # Bucle de tick a ~10 Hz
        while rclpy.ok():

            # Cancelación externa
            if goal_handle.is_cancel_requested:
                self._navigator.cancelTask()
                goal_handle.canceled()
                result.exito = False
                result.mensaje = f'Ruta "{nombre}" cancelada.'
                self.get_logger().info(result.mensaje)
                return result

            arbol.tick_once()

            # Publicar feedback con el nodo activo y el progreso
            hoja = self._hoja_activa(arbol)
            progreso = self._progreso_bt(arbol)
            feedback_msg.etapa_actual = hoja
            feedback_msg.progreso = progreso
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().debug(f'[BT] {hoja} — {progreso*100:.0f}%')

            if arbol.status == py_trees.common.Status.SUCCESS:
                goal_handle.succeed()
                result.exito = True
                result.mensaje = f'Ruta "{nombre}" completada con éxito.'
                self.get_logger().info(result.mensaje)
                return result

            if arbol.status == py_trees.common.Status.FAILURE:
                goal_handle.abort()
                result.exito = False
                result.mensaje = f'Ruta "{nombre}" falló en: {hoja}'
                self.get_logger().error(result.mensaje)
                return result

            time.sleep(0.1)  # tick a 10 Hz

        # Si rclpy deja de estar activo
        goal_handle.abort()
        result.exito = False
        result.mensaje = 'Servidor detenido durante la misión.'
        return result

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _hoja_activa(self, arbol) -> str:
        """Devuelve el nombre del hijo que está en RUNNING."""
        for child in arbol.children:
            if child.status == py_trees.common.Status.RUNNING:
                return child.name
        return arbol.name

    def _progreso_bt(self, arbol) -> float:
        """Fracción de hijos completados con SUCCESS sobre el total."""
        total = len(arbol.children)
        if total == 0:
            return 0.0
        completados = sum(
            1 for c in arbol.children
            if c.status == py_trees.common.Status.SUCCESS
        )
        return completados / total

    def _get_nav_progress(self) -> float:
        """Progreso interno del navegador (0.0–1.0). Fallback a 0.5."""
        try:
            feedback = self._navigator.getFeedback()
            if feedback and hasattr(feedback, 'distance_remaining'):
                dist = feedback.distance_remaining
                if dist is not None and dist >= 0:
                    return max(0.0, min(1.0, 1.0 - dist / 5.0))
        except Exception as e:
            self.get_logger().debug(f'Nav feedback no disponible: {e}')
        return 0.5


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = MisionAccionServidor()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()