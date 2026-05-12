import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Trigger
from proy_fireye_interfaces.action import Mision

import threading


class MisionTriggerNode(Node):

    def __init__(self):
        super().__init__('mision_trigger_node')

        self.cb_group = ReentrantCallbackGroup()

        self.srv = self.create_service(
            Trigger,
            '/fireye/start_mission',
            self.start_mision_callback,
            callback_group=self.cb_group
        )

        self.mision_client = ActionClient(
            self,
            Mision,
            '/fireye/mission',
            callback_group=self.cb_group
        )

        self.mision_activa = False

        self.get_logger().info('MisionTriggerNode listo. Esperando en /fireye/start_mission...')

    def start_mision_callback(self, request, response):
        if self.mision_activa:
            response.success = False
            response.message = 'Ya hay una misión en curso'
            return response

        self.get_logger().info('Servicio recibido. Lanzando misión en segundo plano...')

        self.mision_activa = True

        thread = threading.Thread(target=self.lanzar_mision)
        thread.daemon = True
        thread.start()

        response.success = True
        response.message = 'Misión iniciada correctamente'
        return response

    def lanzar_mision(self):
        self.get_logger().info('Llamando al Action Server /fireye/mission...')

        if not self.mision_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action Server /fireye/mission no disponible')
            self.mision_activa = False
            return

        goal_msg = Mision.Goal()
        goal_msg.nombre_ruta = 'ruta_demo'

        def feedback_cb(feedback_msg):
            feedback = feedback_msg.feedback
            self.get_logger().info(
                f'Feedback: {feedback.etapa_actual} - {feedback.progreso}%'
            )

        def goal_response_cb(future):
            goal_handle = future.result()

            if not goal_handle.accepted:
                self.get_logger().warn('Mision goal rechazado.')
                self.mision_activa = False
                return

            self.get_logger().info('Mision goal aceptado.')

            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(result_cb)
            self._current_result_future = result_future

        def result_cb(future):
            result = future.result().result
            self.get_logger().info(f'Resultado misión: {result.mensaje}')
            self.mision_activa = False

        send_future = self.mision_client.send_goal_async(
            goal_msg,
            feedback_callback=feedback_cb
        )
        send_future.add_done_callback(goal_response_cb)
        self._current_send_future = send_future


def main(args=None):
    rclpy.init(args=args)
    node = MisionTriggerNode()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()