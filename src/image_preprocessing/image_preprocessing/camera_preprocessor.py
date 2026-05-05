import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2


class CameraPreprocessor(Node):
    def __init__(self):
        super().__init__('camera_preprocessor')

        self.bridge = CvBridge()

        # 修改这里：换成你自己的摄像头 topic
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.get_logger().info('Camera preprocessor node started.')

    def image_callback(self, msg):
        try:
            # ROS Image 转 OpenCV 图像，ROS 摄像头通常是 bgr8
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'图像转换失败: {e}')
            return

        # Tarea 1.1：灰度化
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Tarea 1.2：GaussianBlur 降噪
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Tarea 1.3：HSV 转换
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 可选：边缘检测，用于检查边缘是否还清晰
        edges = cv2.Canny(blurred, 50, 150)

        # 显示处理结果
        cv2.imshow('Robot Camera - Original', frame)
        cv2.imshow('Gray', gray)
        cv2.imshow('GaussianBlur', blurred)
        cv2.imshow('HSV', hsv)
        cv2.imshow('Edges', edges)

        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)

    node = CameraPreprocessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    cv2.destroyAllWindows()
    rclpy.shutdown()


if __name__ == '__main__':
    main()