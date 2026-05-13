import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from proy_fireye_interfaces.action import Mision
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus

import time
import threading


class FireyeMissionServer(Node):
    """Servidor de acción ROS2 que ejecuta misiones de patrulla via Nav2.

    Expone ``/fireye/mission`` y navega la secuencia: Punto A → pausa → Punto B.
    """

    def __init__(self):
        """Inicializa el nodo, el action server y el action client de Nav2."""
        super().__init__('fireye_mission_server')

        self.cb_group = ReentrantCallbackGroup()

        self._action_server = ActionServer(
            self, Mision, '/fireye/mission',
            self.execute_callback, callback_group=self.cb_group
        )

        self._nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=self.cb_group
        )

        self.get_logger().info('FireyeMissionServer listo en /fireye/mission')

    def make_pose(self, x: float, y: float,
                  yaw_w: float = 1.0, yaw_z: float = 0.0) -> PoseStamped:
        """Construye un PoseStamped en el frame ``map`` con la posición y orientación dadas."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = yaw_w
        pose.pose.orientation.z = yaw_z
        return pose

    def navigate_to(self, pose: PoseStamped) -> bool:
        """Envía un goal a Nav2 y bloquea hasta obtener resultado (timeout 90s).

        Returns:
            True si Nav2 completó con éxito, False en caso contrario.
        """
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Nav2 no disponible.')
            return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose

        done_event = threading.Event()
        result_container = {'success': False}

        def goal_response_cb(future):
            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().warn('Goal rechazado por Nav2.')
                done_event.set()
                return
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(result_cb)
            self._current_result_future = result_future

        def result_cb(future):
            status = future.result().status
            self.get_logger().info(f'Nav2 status: {status}')
            result_container['success'] = status in [4, 6]
            done_event.set()

        send_future = self._nav_client.send_goal_async(goal_msg)
        send_future.add_done_callback(goal_response_cb)
        self._current_send_future = send_future

        reached = done_event.wait(timeout=90.0)
        if not reached:
            self.get_logger().error('Timeout navegación.')
            return False

        return result_container['success']

    async def execute_callback(self, goal_handle) -> Mision.Result:
        """Ejecuta la misión: navega a Punto A, pausa 5s y regresa a Punto B.

        Publica feedback de progreso en cada etapa. Aborta si algún tramo falla.
        """
        self.get_logger().info(f'Misión recibida: {goal_handle.request.nombre_ruta}')

        feedback_msg = Mision.Feedback()
        result = Mision.Result()

        PUNTO_A   = self.make_pose(x=4.447230, y=-0.019378357602993706)
        PUNTO_B   = self.make_pose(x=0, y=0)
        PAUSA_SEG = 5.0

        feedback_msg.etapa_actual = 'Navegando al Punto A'
        feedback_msg.progreso = 0.0
        goal_handle.publish_feedback(feedback_msg)

        self.get_logger().info('Navegando a Punto A...')
        if not self.navigate_to(PUNTO_A):
            goal_handle.abort()
            result.exito = False
            result.mensaje = 'ERROR: no se pudo llegar al Punto A'
            return result

        feedback_msg.etapa_actual = 'Pausa en Punto A'
        feedback_msg.progreso = 50.0
        goal_handle.publish_feedback(feedback_msg)

        self.get_logger().info(f'Pausa de {PAUSA_SEG}s en Punto A...')
        time.sleep(PAUSA_SEG)

        feedback_msg.etapa_actual = 'Navegando al Punto B'
        feedback_msg.progreso = 75.0
        goal_handle.publish_feedback(feedback_msg)

        self.get_logger().info('Navegando a Punto B...')
        if not self.navigate_to(PUNTO_B):
            goal_handle.abort()
            result.exito = False
            result.mensaje = 'ERROR: no se pudo llegar al Punto B'
            return result

        feedback_msg.etapa_actual = 'Misión completada'
        feedback_msg.progreso = 100.0
        goal_handle.publish_feedback(feedback_msg)

        goal_handle.succeed()
        result.exito = True
        result.mensaje = 'Misión completada: A → pausa → B ✓'
        self.get_logger().info('¡Misión completada!')
        return result


def main(args=None):
    """Inicializa el nodo y lo ejecuta con MultiThreadedExecutor."""
    rclpy.init(args=args)
    node = FireyeMissionServer()

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