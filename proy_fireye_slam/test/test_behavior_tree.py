import time
import pytest
import py_trees
# Importamos el nodo que creamos en nuestro script
from proy_fireye_slam.fireye_mission_bt import WaitNode

def test_wait_node_logic():
    # 1. Configuración: Creamos un nodo que espere solo 1 segundo para el test
    wait_time = 1.0
    nodo_espera = WaitNode(name="TestEspera", seconds=wait_time)
    
    # 2. Inicializamos el nodo (como si el árbol hiciera el primer "tick")
    nodo_espera.initialise()
    
    # 3. Comprobación 1: Justo al empezar, debe estar en RUNNING
    estado_inicial = nodo_espera.update()
    assert estado_inicial == py_trees.common.Status.RUNNING, "El nodo no devolvió RUNNING al empezar."
    
    # 4. Simulamos que pasa el tiempo
    time.sleep(wait_time + 0.1) # Esperamos 1.1s para estar seguros
    
    # 5. Comprobación 2: Tras el tiempo, debe devolver SUCCESS
    estado_final = nodo_espera.update()
    assert estado_final == py_trees.common.Status.SUCCESS, "El nodo no devolvió SUCCESS tras la espera."