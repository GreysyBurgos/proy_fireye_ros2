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

        self.get_logger().info('MisionTriggerNode listo. Esperando en /fireye/start_mission...')

    def start_mision_callback(self, request, response):
        self.get_logger().info('Servicio recibido. Llamando al Action Server /fireye/mision...')

        if not self.mision_client.wait_for_server(timeout_sec=5.0):
            response.success = False
            response.message = 'ERROR: Action Server /fireye/mision no disponible'
            return response

        goal_msg = Mision.Goal()
        goal_msg.nombre_ruta = 'ruta_demo'

        done_event = threading.Event()
        result_container = {
            'success': False,
            'message': 'Sin resultado'
        }

        def feedback_cb(feedback_msg):
            feedback = feedback_msg.feedback
            self.get_logger().info(
                f'Feedback: {feedback.etapa_actual} - {feedback.progreso}%'
            )

        def goal_response_cb(future):
            goal_handle = future.result()

            if not goal_handle.accepted:
                self.get_logger().warn('Mision goal rechazado.')
                result_container['success'] = False
                result_container['message'] = 'Mision goal rechazado'
                done_event.set()
                return

            self.get_logger().info('Mision goal aceptado.')
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(result_cb)
            self._current_result_future = result_future

        def result_cb(future):
            result = future.result().result
            result_container['success'] = result.exito
            result_container['message'] = result.mensaje
            done_event.set()

        send_future = self.mision_client.send_goal_async(
            goal_msg,
            feedback_callback=feedback_cb
        )
        send_future.add_done_callback(goal_response_cb)
        self._current_send_future = send_future

        finished = done_event.wait(timeout=120.0)

        if not finished:
            response.success = False
            response.message = 'ERROR: timeout esperando resultado de la misión'
            return response

        response.success = result_container['success']
        response.message = result_container['message']
        return response


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
        rclpy.shutdown()


if __name__ == '__main__':
    main()