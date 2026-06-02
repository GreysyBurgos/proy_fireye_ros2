import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import time


class ImageCapture(Node):
    def __init__(self):
        super().__init__('image_capture_node')

        self.bridge = CvBridge()
        self.count = 0
        self.max_images = 100
        self.last_save_time = 0
        self.save_interval = 1.0

        self.save_dir = '/home/diego/proy_fireye_ros2/dataset/raw_images'
        os.makedirs(self.save_dir, exist_ok=True)

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.get_logger().info('Guardando imagen cada 1 segundo...')

    def image_callback(self, msg):
        if self.count >= self.max_images:
            self.get_logger().info('Captura terminada.')
            rclpy.shutdown()
            return

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        cv2.imshow('Robot Camera Capture', frame)
        cv2.waitKey(1)

        current_time = time.time()

        if current_time - self.last_save_time >= self.save_interval:
            filename = os.path.join(
                self.save_dir,
                f'image_{self.count:04d}.jpg'
            )
            cv2.imwrite(filename, frame)
            self.get_logger().info(f'Imagen guardada: {filename}')
            self.count += 1
            self.last_save_time = current_time


def main():
    rclpy.init()
    node = ImageCapture()
    rclpy.spin(node)
    node.destroy_node()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
