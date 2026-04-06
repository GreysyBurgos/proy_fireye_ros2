import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def main():
    rclpy.init()

    # Creamos el objeto navegador
    nav = BasicNavigator()

    # 1. Esperamos a que Nav2 esté totalmente activo
    # (Esto evita errores si lanzas el script muy rápido)
    nav.waitUntilNav2Active()

    # 2. Definimos la meta (Goal)
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = nav.get_clock().now().to_msg()

    # --- AQUÍ CAMBIAS LAS COORDENADAS ---
    goal_pose.pose.position.x = 1.5  # Modifica esto según tu mapa
    goal_pose.pose.position.y = 0.5
    goal_pose.pose.orientation.w = 1.0 # Mirando hacia "adelante"
    # ------------------------------------

    # 3. ¡A navegar!
    print(f"Enviando al robot a: X={goal_pose.pose.position.x}, Y={goal_pose.pose.position.y}...")
    nav.goToPose(goal_pose)

    # 4. Bucle para ver el progreso
    i = 0
    while not nav.isTaskComplete():
        i += 1
        feedback = nav.getFeedback()
        # Imprimimos la distancia restante cada 5 iteraciones
        if feedback and i % 5 == 0:
            print(f'Distancia restante: {feedback.distance_remaining:.2f} metros.')

    # 5. Resultado final
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print('¡Victoria! El robot ha llegado a la meta.')
    elif result == TaskResult.CANCELED:
        print('La misión ha sido cancelada.')
    elif result == TaskResult.FAILED:
        print('Error: La navegación ha fallado.')

    rclpy.shutdown()

if __name__ == '__main__':
    main()