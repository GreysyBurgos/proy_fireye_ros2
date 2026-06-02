from ultralytics import YOLO
import cv2

model = YOLO(
    "/home/yilun/proy_fireye_ros2/dataset/runs/detect/train/weights/best.pt"
)

img_path = "/home/yilun/Descargas/00000062.jpg"

results = model.predict(
    source=img_path,
    conf=0.5,
    verbose=False
)

img = cv2.imread(img_path)

peligrosidad = {
    "lata": "BAJA",
    "botella": "MEDIO",
    "aerosol": "ALTA",
}

for box in results[0].boxes:

    cls = int(box.cls[0])
    conf = float(box.conf[0])
    nombre = model.names[cls]
    riesgo = peligrosidad.get(nombre, "DESCONOCIDO")

    x1, y1, x2, y2 = map(int, box.xyxy[0])

    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        3
    )

    label1 = f"{nombre} {conf:.2f}"
    label2 = f"Peligrosidad: {riesgo}"

    # 文字放在框外上方
    text_y1 = y1 - 35
    text_y2 = y1 - 10

    # 如果太靠上，就放到框里面上方，避免超出图片
    if text_y1 < 20:
        text_y1 = y1 + 30
        text_y2 = y1 + 60

    cv2.putText(
        img,
        label1,
        (x1, text_y1),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 0),
        2
    )

    cv2.putText(
        img,
        label2,
        (x1, text_y2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 0, 255),
        2
    )

cv2.imwrite("resultado.jpg", img)

print("Imagen guardada: resultado.jpg")