import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np


class CameraPreprocessor(Node):

    def detect_neck(self, mask, x, y, w, h):
        """
        Detecta una reducción brusca de anchura en la parte superior del objeto.
        Se usa para clasificar botellas.
        """
        roi = mask[y:y+h, x:x+w]

        if roi.size == 0:
            return False

        top_part = roi[0:int(h * 0.30), :]
        middle_part = roi[int(h * 0.40):int(h * 0.70), :]

        top_width = cv2.countNonZero(top_part)
        middle_width = cv2.countNonZero(middle_part)

        if middle_width == 0:
            return False

        ratio = top_width / float(middle_width)

        return ratio < 0.65
    
    def __init__(self):
        super().__init__('camera_preprocessor')

        self.bridge = CvBridge()

        # ==============================
        # 这里改成你的机器人摄像头 topic
        # 常见名字：
        # /camera/image_raw
        # /camera/color/image_raw
        # /image_raw
        # ==============================
        self.camera_topic = '/camera/image_raw'

        self.subscription = self.create_subscription(
            Image,
            self.camera_topic,
            self.image_callback,
            10
        )

        # ==============================
        # Tarea 2.1：Canny 阈值，可调参数
        # ==============================
        self.canny_low = 50
        self.canny_high = 150

        # 面积过滤：太小的轮廓通常是噪声
        self.min_area = 500
        self.max_area = 50000

        self.get_logger().info('Nodo de segmentacion y deteccion iniciado.')
        self.get_logger().info(f'Suscrito al topic: {self.camera_topic}')

    def image_callback(self, msg):
        try:
            # ROS Image 转 OpenCV BGR 图像
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Error convirtiendo imagen ROS a OpenCV: {e}')
            return

        # 为了避免窗口太大，可以缩小图像
        # 如果你不想缩小，可以注释掉这一行
        frame = cv2.resize(frame, (640, 480))

        # 复制一份图像用于画检测结果
        output = frame.copy()

        # ====================================================
        # 1. 预处理：灰度化
        # ====================================================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ====================================================
        # 2. 预处理：GaussianBlur 降噪
        # ====================================================
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # ====================================================
        # Tarea 2.1：Canny 边缘检测
        # 阈值 self.canny_low 和 self.canny_high 可以调
        # ====================================================
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)

        # ====================================================
        # Tarea 2.2：findContours 找轮廓
        # RETR_EXTERNAL：只找外部轮廓
        # 如果你想同时看内部细节，可以改成 RETR_TREE
        # ====================================================
        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # ====================================================
        # Tarea 2.3：HSV + inRange 创建颜色掩码
        # 用于隔离金属罐、玻璃反光、亮白区域
        # ====================================================
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 这个范围用于检测“亮色 / 白色 / 金属反光”
        # HSV 含义：
        # H: 色相，0~179
        # S: 饱和度，0~255，越低越接近白/灰/金属
        # V: 亮度，0~255，越高越亮
        lower_bright = np.array([0, 0, 160])
        upper_bright = np.array([179, 80, 255])

        mask_bright = cv2.inRange(hsv, lower_bright, upper_bright)

        # 对 mask 做形态学处理，减少噪声
        kernel = np.ones((5, 5), np.uint8)
        mask_bright = cv2.morphologyEx(mask_bright, cv2.MORPH_OPEN, kernel)
        mask_bright = cv2.morphologyEx(mask_bright, cv2.MORPH_CLOSE, kernel)

        # ====================================================
        # 遍历所有轮廓，筛选候选物体
        # ====================================================
        candidate_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # 过滤太小或太大的区域
            if area < self.min_area or area > self.max_area:
                continue

            # 获取矩形框
            x, y, w, h = cv2.boundingRect(contour)

            # 过滤奇怪形状
            if w == 0 or h == 0:
                continue

            aspect_ratio = h / float(w)

            perimeter = cv2.arcLength(contour, True)
            epsilon = 0.04 * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)
            vertices = len(approx)

            object_type = 'Candidato'

            has_neck = self.detect_neck(mask_bright, x, y, w, h)

            if vertices == 4 and 0.4 <= aspect_ratio <= 1.2:
                object_type = 'Lata'
            elif has_neck:
                object_type = 'Botella'
            elif aspect_ratio > 2.0 and vertices >= 5:
                object_type = 'Aerosol'

            # 候选物体一般不要太扁，也不要太细
            if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                continue

            # ====================================================
            # 检查这个轮廓区域里面是否有亮色/金属/反光 mask
            # ====================================================
            roi_mask = mask_bright[y:y+h, x:x+w]

            bright_pixels = cv2.countNonZero(roi_mask)
            total_pixels = w * h

            if total_pixels == 0:
                continue

            bright_ratio = bright_pixels / float(total_pixels)

            # 如果亮色区域太少，可能不是金属罐或玻璃反光
            # 这个值可以调：0.03、0.05、0.10 都可以试
            #if bright_ratio < 0.03:
                #continue

            candidate_count += 1

            M = cv2.moments(contour)
            
            if M["m00"] != 0:
               center_x = int(M["m10"] / M["m00"])
               center_y = int(M["m01"] / M["m00"])
            else:
               center_x = x + w // 2
               center_y = y + h // 2

            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.circle(output, (center_x, center_y), 5, (0, 0, 255), -1)
            self.get_logger().info(
                    f'Detectado: {object_type} | centroide=({center_x},{center_y}) | bbox=({x},{y},{w},{h}) | vertices={vertices} | aspect_ratio={aspect_ratio:.2f}'

            )

            # ====================================================
            # 画矩形框：调试用
            # ====================================================
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

        

            # 写文字
            cv2.putText(
                output,
               f'{object_type} {candidate_count} ({center_x},{center_y})',
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # 在左上角显示检测数量
        cv2.putText(
            output,
            f'Candidatos: {candidate_count}',
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        # ====================================================
        # 显示调试窗口
        # ====================================================
        cv2.imshow('Original', frame)
        cv2.imshow('Gray', gray)
        cv2.imshow('GaussianBlur', blurred)
        cv2.imshow('Canny Edges', edges)
        cv2.imshow('HSV Bright Mask', mask_bright)
        cv2.imshow('Detection Output', output)

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