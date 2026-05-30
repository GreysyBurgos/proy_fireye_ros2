import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
from ultralytics import YOLO


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        self.bridge = CvBridge()

        self.model_path = '/home/diego/proy_fireye_ros2/dataset/runs/detect/train/weights/best.pt'
        self.model = YOLO(self.model_path)

        self.camera_topic = '/camera/image_raw'

        self.subscription = self.create_subscription(
            Image,
            self.camera_topic,
            self.image_callback,
            10
        )

        self.publisher = self.create_publisher(
            Image,
            '/yolo/image_annotated',
            10
        )

        self.get_logger().info('YOLO detector started')
        self.get_logger().info(f'Model: {self.model_path}')
        self.get_logger().info(f'Subscribed to: {self.camera_topic}')
        self.get_logger().info('Publishing annotated image to: /yolo/image_annotated')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Error converting ROS image to OpenCV: {e}')
            return

        results = self.model.predict(
            source=frame,
            conf=0.5,
            verbose=False
        )

        annotated_frame = results[0].plot()

        annotated_msg = self.bridge.cv2_to_imgmsg(
            annotated_frame,
            encoding='bgr8'
        )

        annotated_msg.header = msg.header
        self.publisher.publish(annotated_msg)


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()