#!/usr/bin/env python3

import pygame
from itertools import cycle
import subprocess
import sys
import os
import json
import threading
import time
from moviepy.editor import VideoFileClip
from queue import Queue
# Añade el directorio src a sys.path
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from video_audio_response.video_generation import total_video_generation
import numpy as np
sys.path.append('/opt/ros/noetic/lib/python3/dist-packages')
import rospy
from std_msgs.msg import String

# Agregar la ruta del archivo actual a PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


# Rutas de las imágenes
carpetaImgs = os.path.abspath(os.path.join(os.path.dirname(__file__), 'faces')) + "/"
IMAGEN_DEFAULT = carpetaImgs + "default.png"
IMAGEN_PARPADEO = carpetaImgs + "blink2_normal.png"
IMAGEN_FELIZ = carpetaImgs + "happy.png"
IMAGEN_MEH = carpetaImgs + "meh.png"
IMAGEN_MUERTO = carpetaImgs + "game_over.png"
IMAGEN_DINERO = carpetaImgs + "money.png"
IMAGEN_PENSANDO = carpetaImgs + "thinking.png"
IMAGEN_BOCAABIERTA = carpetaImgs + "open_mouth.png"
IMAGEN_BOCACERRADA = carpetaImgs + "close_mouth.png"
IMAGEN_LISTO = carpetaImgs + "ready.png"
# Lista de rutas de imágenes

SECUENCIA_IMAGENES = [IMAGEN_PARPADEO,IMAGEN_DEFAULT]

# Añadir lista de tiempos para cada imagen
TIEMPOS_IMAGENES = [0.1, 2.0]  # Tiempo en segundos para cada imagen en SECUENCIA_IMAGENES


# Posición de inicio de la ventana
window_position = [0, 0]
pasosHorizontal = 5
pasosVertical = 5




# Agrega la carpeta principal catkin_ws/src
directorio_principal = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(directorio_principal)

# Ahora puedes usar funciones o clases de utilidad
from audio_processing.utils import read_file
from audio_processing.assistant import Assistant


def moverVentana():
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:  # Izquierda
        window_position[0] -= pasosHorizontal
    if keys[pygame.K_d]:  # Derecha
        window_position[0] += pasosHorizontal
    if keys[pygame.K_w]:  # Arriba
        window_position[1] -= pasosVertical
    if keys[pygame.K_s]:  # Abajo
        window_position[1] += pasosVertical
    #print(f"Posición de la ventana: {window_position}")

def seleccionar_pantalla():
    pygame.init()
    pantallas = pygame.display.get_desktop_sizes()
    print("Detectando pantallas disponibles:")
    for i, res in enumerate(pantallas):
        print(f"Pantalla {i+1}: {res[0]}x{res[1]}")

    seleccionada = 0
    seleccion_hecha = False
    fuente = pygame.font.SysFont("Arial", 30)
    window_temp = pygame.display.set_mode((500, 300))
    pygame.display.set_caption("Seleccionar Pantalla")

    while not seleccion_hecha:
        window_temp.fill((0, 0, 0))
        texto = fuente.render(f"Seleccione la pantalla (1-{len(pantallas)}): {seleccionada+1}", True, (255, 255, 255))
        window_temp.blit(texto, (50, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    seleccionada = (seleccionada + 1) % len(pantallas)
                elif event.key == pygame.K_LEFT:
                    seleccionada = (seleccionada - 1) % len(pantallas)
                elif event.key == pygame.K_RETURN:
                    seleccion_hecha = True

    # Calcular la posición global de la pantalla seleccionada
    x_global = sum(pantallas[i][0] for i in range(seleccionada))
    y_global = 0  # Asumiendo que las pantallas están alineadas horizontalmente

    pygame.display.quit()
    return seleccionada, pantallas[seleccionada], (x_global, y_global)

def centrar_ventana(pantalla_res, position):
    global window_position
    x_global, y_global = position
    window_width, window_height = 800, 480  # Dimensiones de la ventana
    screen_width, screen_height = pantalla_res
    window_position = [
        (screen_width - window_width) // 2 + x_global,
        (screen_height - window_height) // 2 + y_global
    ]


class final_face:
    def __init__(self):
        rospy.init_node('final_face')
        self.pub_commands = rospy.Publisher('/movement_commands', String, queue_size=1)
        
        self.number = "0"
        self.respuesta = ""
        self.previous_respuesta = ""  # Para rastrear la respuesta anterior
        CONFIG_PARAMS = read_file(directorio_principal + "/" + "config", "yaml")
        self.comands = CONFIG_PARAMS["comands"]


        try:
            with open(directorio_principal + "/" + "basics_responses.json", "r", encoding='utf-8') as f:
                basics_responses = json.load(f)
                self.basics_responses = {key.lower(): value for key, value in basics_responses.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error al cargar respuestas básicas.")
            self.basics_responses = {}

        self.assistant = Assistant(CONFIG_PARAMS["stt"]["model_size"],
                                   CONFIG_PARAMS["stt"]["recording_time"],
                                   CONFIG_PARAMS["stt"]["silence_break"],
                                   CONFIG_PARAMS["stt"]["sensibility"],
                                   CONFIG_PARAMS["assistant"]["wake_word"],
                                   CONFIG_PARAMS["comands"],
                                   CONFIG_PARAMS["prompt"],
                                   self.basics_responses)
        
        #        va = Assistant(model, record_timeout, phrase_timeout, energy_threshold, wake_word,comands,prompt,basics_responses)


        # Configuración de la ventana
        pygame.init()

        # Selección de pantalla
        seleccionada, res_pantalla,position = seleccionar_pantalla()
        centrar_ventana(res_pantalla,position)

        self.window_width, self.window_height = 800, 480
        # Configurar ventana en la posición seleccionada
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_position[0]},{window_position[1]}"
        self.window = pygame.display.set_mode((self.window_width, self.window_height), pygame.NOFRAME)
        pygame.display.set_caption("YAREN Face")

        # Secuencia de imágenes y tiempos
        self.expressions = cycle(SECUENCIA_IMAGENES)
        self.times = cycle(TIEMPOS_IMAGENES)
        self.current_image = next(self.expressions)
        self.current_time = next(self.times)
        self.last_switch_time = pygame.time.get_ticks()  # Tiempo del último cambio de imagen

        self.video_queue = Queue()
        self.video_ready = threading.Event()
        self.detect_commands_running = threading.Event()  # Señal para pausar/reanudar detección de comandos


    def detect_commands(self):
        while not rospy.is_shutdown():
            # Esperar si la detección de comandos está pausada
            self.detect_commands_running.wait()

            pose_num, respuesta = self.assistant.listen_movement_comand()

            self.number = str(pose_num + 1)
            self.pub_commands.publish(f"{self.number}")
            print(f"Publicado: {self.number}")

            if pose_num != -1:
                print(self.comands[pose_num])

            if not self.video_ready.is_set():
                threading.Thread(target=self.generate_video, args=(respuesta,)).start()


    def play_video(self):
        if not self.video_ready.is_set():
            return

        video_clip = self.video_queue.get()
        self.video_ready.clear()

        # Inicializar y reproducir el audio si está presente
        if video_clip.audio:
            video_clip.audio.write_audiofile("temp_audio.mp3", fps=44100)
            pygame.mixer.init()
            pygame.mixer.music.load("temp_audio.mp3")
            pygame.mixer.music.play()

        # Reproducir los frames mientras el audio esté activo
        for frame in video_clip.iter_frames(fps=24, with_times=False):
            if not pygame.mixer.music.get_busy():  # Detener si el audio terminó
                break

            frame_surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
            frame_surface = pygame.transform.scale(frame_surface, (self.window_width, self.window_height))
            self.window.blit(frame_surface, (0, 0))
            pygame.display.flip()

        # Asegurarse de detener el audio si no lo está ya
        pygame.mixer.music.stop()
        video_clip.close()

        # Reanudar detección de comandos después de reproducir el video
        self.detect_commands_running.set()

    def generate_video(self, respuesta):
        try:
            
            video_clip = total_video_generation(respuesta)
            self.video_queue.put(video_clip)
            self.video_ready.set()

            # Pausar detección de comandos mientras se genera el video
            self.detect_commands_running.clear()

        except Exception as e:
            rospy.logerr(f"Error generando video: {e}")

    def show_special_image(self, image_path,sleep_time=5):
        image = pygame.image.load(image_path)

        # Limpiar la ventana antes de dibujar la nueva imagen
        self.window.fill((0, 0, 0))  # Rellena la ventana con negro (RGB: 0, 0, 0)

        self.window.blit(image, (0, 0))
        pygame.display.flip()
        time.sleep(sleep_time)  # Mostrar la imagen durante 5 segundos

    

    def main(self):
        clock = pygame.time.Clock()
        running = True
        
        # Iniciar hilo para detección de comandos
        command_thread = threading.Thread(target=self.detect_commands, daemon=True)
        command_thread.start()

        
        # Activar detección de comandos inicialmente
        self.detect_commands_running.set()

        while running and not rospy.is_shutdown():
            

            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False


                # Obtener tiempo actual
                current_ticks = pygame.time.get_ticks()

                # Reproducir video si está listo
                if self.video_ready.is_set():
                    self.play_video()
   
                    """
                    - dinero
                    - me puedes dar un abrazo
                    - sorpresa
                    - vuela
                    - que tal si luchamos
                    - es cierto que te vas de viaje
                    """

                    # Mostrar imagen especial si el número es "1", "2", o "4"
                    if self.number == "1":
                        self.show_special_image(IMAGEN_DINERO)
                    elif self.number == "2":
                        self.show_special_image(IMAGEN_FELIZ)
                    
                    elif self.number == "3":
                        self.show_special_image(IMAGEN_BOCAABIERTA)
                    
                    elif self.number == "4":
                        self.show_special_image(IMAGEN_BOCACERRADA)

                    elif self.number == "5":
                        self.show_special_image(IMAGEN_LISTO)
                    
                    elif self.number == "6":
                        self.show_special_image(IMAGEN_FELIZ)
                    
                    elif self.number == "7":
                        self.show_special_image(IMAGEN_FELIZ)

                        SECUENCIA_IMAGENES_BARNEY = [IMAGEN_PARPADEO,IMAGEN_DEFAULT]
                        # Añadir lista de tiempos para cada imagen
                        TIEMPOS_IMAGENES_BARNEY = [0.1, 2.0] 

                        #REPRODUCIR CANCION DE BARNEY
                        # Inicializar pygame mixer
                        pygame.mixer.init()

                        # Cargar el archivo MP3
                        archivo_mp3 = current_dir + "/Te quiero - Barney Latinoamérica.mp3"  # Reemplaza con la ruta de tu archivo MP3
                        pygame.mixer.music.load(archivo_mp3)

                        # Reproducir el archivo
                        pygame.mixer.music.play()

                        # Esperar mientras el audio se reproduce
                        while pygame.mixer.music.get_busy():
                            #pygame.time.Clock().tick(10)  # Evitar uso intensivo de CPU
                            for i, imagen in enumerate(SECUENCIA_IMAGENES_BARNEY):
                                # Manejar eventos para evitar que la ventana se congele
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        pygame.mixer.music.stop()
                                        pygame.quit()
                                        exit()
                                self.show_special_image(imagen,TIEMPOS_IMAGENES_BARNEY[i])
                        
                        # Asegurarse de detener el audio si no lo está ya
                        pygame.mixer.music.stop()

                    self.number = str(1)
                    self.pub_commands.publish(f"{self.number}")
                    print(f"Publicado: {self.number}")

                # Cambiar de imagen si se cumple el tiempo
                elif (current_ticks - self.last_switch_time) / 1000.0 >= self.current_time:
                    self.current_image = next(self.expressions)
                    self.current_time = next(self.times)
                    self.last_switch_time = current_ticks

                # Mostrar la imagen actual
                    # Mostrar la imagen actual
                    image = pygame.image.load(self.current_image)

                    # Limpiar la ventana antes de dibujar la nueva imagen
                    self.window.fill((0, 0, 0))  # Rellena la ventana con negro (RGB: 0, 0, 0)

                    self.window.blit(image, (0, 0))
                    pygame.display.flip()

                    moverVentana()

                    # Actualiza la posición de la ventana usando wmctrl
                    subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-e', f'0,{window_position[0]},{window_position[1]},-1,-1'])


                    # Actualizar la pantalla
                clock.tick(60)


            except Exception as e:
                print(f"Error en el bucle principal: {e}")
                running = False


        pygame.quit()
        print("Programa finalizado correctamente.")


if __name__ == "__main__":
    face = final_face()
    face.main()