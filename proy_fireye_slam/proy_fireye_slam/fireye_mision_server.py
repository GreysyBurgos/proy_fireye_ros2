# import rclpy
# import threading
# from rclpy.node import Node
# from rclpy.action import ActionClient
# from rclpy.callback_groups import ReentrantCallbackGroup
# from rclpy.executors import MultiThreadedExecutor

# from proy_fireye_interfaces.action import Mision
# from proy_fireye_interfaces.srv import MiMovimientoMsg


# class LanzadorMision(Node):
#     def __init__(self):
#         super().__init__('lanzador_mision')
#         self._cb_group = ReentrantCallbackGroup()

#         self.create_service(
#             MiMovimientoMsg,
#             '/lanzar_mision',
#             self.callback,
#             callback_group=self._cb_group
#         )

#         self._action_client = ActionClient(
#             self,
#             Mision,
#             '/ejecutar_mision',
#             callback_group=self._cb_group
#         )

#     def callback(self, req, res):
#         goal = Mision.Goal()
#         goal.nombre_ruta = req.move

#         # Event para bloquear sin llamar a spin_until_future_complete
#         done = threading.Event()
#         resultado = {}

#         def on_goal(future_gh):
#             goal_handle = future_gh.result()
#             if not goal_handle.accepted:
#                 resultado['exito'] = False
#                 done.set()
#                 return

#             def on_result(future_result):
#                 resultado['exito'] = future_result.result().result.exito
#                 done.set()

#             goal_handle.get_result_async().add_done_callback(on_result)

#         self._action_client.send_goal_async(goal).add_done_callback(on_goal)

#         # Espera bloqueante en este hilo, sin tocar el executor
#         done.wait()

#         res.success = resultado.get('exito', False)
#         return res


# def main(args=None):
#     rclpy.init(args=args)
#     node = LanzadorMision()
#     executor = MultiThreadedExecutor()
#     executor.add_node(node)
#     try:
#         executor.spin()
#     except KeyboardInterrupt:
#         pass
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()


# if __name__ == '__main__':
#     main()