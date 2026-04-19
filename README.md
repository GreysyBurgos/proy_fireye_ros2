# 🤖 proy-fireye-ros2
**6º Proyecto de Grado en Tecnologías Interactivas.** Backend robótico, sistemas de navegación y entorno de simulación para el robot **Fireye**, un sistema de patrullaje autónomo diseñado para entornos rurales y fincas privadas.
---

## 📋 Descripción
Este repositorio contiene el núcleo lógico y la configuración de ROS 2 para el robot **Fireye**. El proyecto se centra en la implementación de autonomía para vigilancia en exteriores, integrando sensores LiDAR, odometría y sistemas de visión en un entorno de simulación de alta fidelidad.

Permite realizar dos tareas críticas:
1. **Mapeo (SLAM):** Exploración y generación de mapas de terrenos desconocidos.
2. **Navegación:** Patrullaje inteligente utilizando mapas pre-existentes con evitación de obstáculos dinámica.
---
## 🛠️ Tecnologías utilizadas
- **Lenguajes:** C++ y Python
---
## 📁 Estructura del proyecto
```
turtlebot3_ws...
├──proy_fireye_ros2/
    ├── src/
    │   ├── proy_fireye_ros2/          # Código principal del robot
    │   ├── proy_fireye_mundo/    # Mundo de simulación
        ├── proy_fireye_SLAM/      #navegación del robot
        ├── proy_fireye_bags/      #pruebas simulación
---

## 🚀 Instalación

⚠️ IMPORTANTE: Este repositorio debe clonarse dentro de la carpeta src de tu espacio de trabajo de TurtleBot3 (turtlebot3_ws) para asegurar la compatibilidad con las dependencias de simulación existentes.

```
1. Accede a la carpeta 'src' de tu workspace de TurtleBot3
(Si tu carpeta tiene otro nombre, ajusta la ruta)
cd ~/turtlebot3_ws/src

2. Clona el repositorio dentro de la carpeta src
git clone [https://github.com/GreysyBurgos/proy_fireye_ros2.git](https://github.com/GreysyBurgos/proy_fireye_ros2.git)

3. Regresa a la raíz del workspace para compilar
cd ..

4. Instalar dependencias faltantes
rosdep install --from-paths src --ignore-src -y

5. Compilar el proyecto
colcon build --symlink-install
source install/setup.bash
```
---

## 🛠️ Compilación

⚠️ Importante: ejecutar siempre desde la raíz del workspace

```
colcon build
```

Después de compilar:

```
source install/setup.bash
```

---
## 🤖 Funcionalidades

* Simulación de entorno personalizado
* Control del robot mediante nodos ROS 2
* Comunicación mediante servicios y/o topics
* Ejecución de movimientos (ej: ir hacia un punto, esperar 5 segundos y volver al origen)

---
## 🌍 Lanzar el mundo y los diferentes servicios

Terminal 1:
```
ros2 launch proy_fireye_mundo fireye_mundo.launch.py
```
Terminal 2:
```
ros2 launch proy_fireye_slam my_tb3_navigator.launch.py use_sim_time:=True
```
Terminal 3:
```
#navegar a un punto 
ros2 run proy_fireye_slam initial_pose_pub
ros2 run proy_fireye_slam nav_to_pose

#navegar una ruta
ros2 run proy_fireye_slam initial_pose_pub
ros2 run proy_fireye_slam follow_waypoints

#pose inicial -> navegar a un punto -> esperar 5 segundos -> volver a pose inicial
ros2 run proy_fireye_slam fireye_mission_bt
```
---
## 👥 Autores

* GRUPO 6
* Pablo Chasi, Imanol Fifuero, Manuel Pérez, Yixuan Chen, Yulin Jiang y Greysy Burgos

---
## 📌 Estado del proyecto

🚧 En desarrollo
# Proyecto-Robotica
6º Proyecto de grado en tecnologías interactivas
