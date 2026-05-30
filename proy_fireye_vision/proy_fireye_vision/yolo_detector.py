import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
from ultralytics import YOLO

from std_msgs.msg import String
import json


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        self.bridge = CvBridge()

        self.model_path = '/home/yilun/proy_fireye_ros2/dataset/runs/detect/train/weights/best.pt'
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

        self.info_publisher = self.create_publisher(
            String,
            '/yolo/object_info',
            10
        )

        self.peligrosidad = {
            "lata": 1,
            "latas": 1,
            "botella": 3,
            "aerosol": 5,
            "aerosoles": 5,
            "aerosole": 5,
        }

        self.peligrosidad_texto = {
            1: "BAJA",
            3: "MEDIA",
            5: "ALTA",
        }

        self.get_logger().info('YOLO detector started')
        self.get_logger().info(f'Model: {self.model_path}')
        self.get_logger().info(f'Subscribed to: {self.camera_topic}')
        self.get_logger().info('Publishing annotated image to: /yolo/image_annotated')
        self.get_logger().info('Publishing object info to: /yolo/object_info')

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

        annotated_frame = frame.copy()

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            object_name = self.model.names[class_id]

            danger = self.peligrosidad.get(object_name, 1)
            danger_text = self.peligrosidad_texto.get(danger, "DESCONOCIDO")

            info = {
                "object": object_name,
                "confidence": round(confidence, 2),
                "danger": danger,
                "danger_text": danger_text
            }

            msg_info = String()
            msg_info.data = json.dumps(info)
            self.info_publisher.publish(msg_info)

            self.get_logger().info(
                f'Detectado YOLO: {object_name} | conf={confidence:.2f} | danger={danger} | {danger_text}'
            )

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

            label1 = f"{object_name} {confidence:.2f}"
            label2 = f"Peligrosidad: {danger_text}"

            text_y1 = y1 - 35
            text_y2 = y1 - 10

            if text_y1 < 20:
                text_y1 = y1 + 30
                text_y2 = y1 + 60

            cv2.putText(
                annotated_frame,
                label1,
                (x1, text_y1),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 0),
                2
            )

            cv2.putText(
                annotated_frame,
                label2,
                (x1, text_y2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )

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