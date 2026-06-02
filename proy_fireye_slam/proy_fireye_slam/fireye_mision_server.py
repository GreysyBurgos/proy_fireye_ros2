#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_srvs.srv import Trigger
import math

class FollowWaypointsService(Node):
    def __init__(self):
        super().__init__('follow_waypoints_service')

        # Waypoints capturados (el último es el origen)
        self.waypoints = [
            (1.9831645488739014,  -0.032464444637298584),
            (3.9874908924102783,  -0.027057688683271408),
            (3.9696831703186035,  -1.327908992767334),
            (7.257323265075684,   -1.3567404747009277),
            (7.3148322105407715,   1.3639671802520752),
            (4.005981922149658,    1.2908923625946045),
            (3.9355010986328125,  -0.04210276901721954),
            (1.9831645488739014,  -0.032464444637298584),
            (-0.05399591103196144,-0.002305725123733282),  # origen
        ]

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._service = self.create_service(Trigger, 'follow_waypoints', self.service_callback)

        self.current_index = 0
        self.running = False

        self.get_logger().info('Servicio follow_waypoints listo.')

    def service_callback(self, request, response):
        if self.running:
            response.success = False
            response.message = 'El robot ya está siguiendo waypoints.'
            return response

        self.current_index = 0
        self.running = True
        self.get_logger().info('Iniciando recorrido de waypoints...')
        self.send_next_goal()

        response.success = True
        response.message = f'Recorrido iniciado con {len(self.waypoints)} puntos.'
        return response

    def send_next_goal(self):
        if self.current_index >= len(self.waypoints):
            self.get_logger().info('✅ Recorrido completado, robot en origen.')
            self.running = False
            return

        x, y = self.waypoints[self.current_index]
        self.get_logger().info(f'Navegando a punto {self.current_index + 1}/{len(self.waypoints)}: x={x:.2f}, y={y:.2f}')

        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0  # sin rotación específica

        goal_msg.pose = pose

        self._action_client.wait_for_server()
        send_goal_future = self._action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rechazado.')
            self.running = False
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

    def goal_result_callback(self, future):
        self.current_index += 1
        self.send_next_goal()


def main(args=None):
    rclpy.init(args=args)
    node = FollowWaypointsService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()