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
from video_audio_response.video_generation import total_video_generation
from audio_processing.utils import read_file
from audio_processing.assistant import Assistant
import numpy as np
# Add the directory of rospy in case it's not found
sys.path.append('/opt/ros/noetic/lib/python3/dist-packages')
import rospy
from std_msgs.msg import String

# Add the directory of the present file        
current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(current_dir)


# Establish the main images routes
# These are going to show along with the commands that are established in the config.yaml
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

#Blinking secuence
SECUENCIA_IMAGENES = [IMAGEN_PARPADEO,IMAGEN_DEFAULT]

# List of time for the blinking sequence, the first item belongs to the closed eyes and the second belongs to the eyes while open
TIEMPOS_IMAGENES = [0.1, 2.0]  # Time in seconds por each image in SECUENCIA_IMAGENES


# Begining posicion of the window
window_position = [0, 0]
pasosHorizontal = 5
pasosVertical = 5

# The function below is to select de desired display in case there are more than one
# 
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

    # Calculate the global position of the selected screen
    x_global = sum(pantallas[i][0] for i in range(seleccionada))
    y_global = 0  # Assuming the screens are aligned horizontally

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



# This funtion is for moving the window in case it's necesary to be adjusted to the robot
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



class final_face:
    def __init__(self):
        rospy.init_node('final_face')
        self.pub_commands = rospy.Publisher('/movement_commands', String, queue_size=1)
        
        self.number = "0"
        self.respuesta = ""
        CONFIG_PARAMS = read_file(current_dir + "/" + "config", "yaml")
        self.comands = CONFIG_PARAMS["comands"]


        try:
            with open(current_dir + "/" + "basics_responses.json", "r", encoding='utf-8') as f:
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


        # Window settings
        pygame.init()

        # Screen selection
        seleccionada, res_pantalla,position = seleccionar_pantalla()
        centrar_ventana(res_pantalla,position)

        self.window_width, self.window_height = 800, 480
        # Set window to selected position
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_position[0]},{window_position[1]}"
        self.window = pygame.display.set_mode((self.window_width, self.window_height), pygame.NOFRAME)
        pygame.display.set_caption("YAREN Face")

        # Sequence of images and times
        self.expressions = cycle(SECUENCIA_IMAGENES)
        self.times = cycle(TIEMPOS_IMAGENES)
        self.current_image = next(self.expressions)
        self.current_time = next(self.times)
        self.last_switch_time = pygame.time.get_ticks()  # Time of last image change

        self.video_queue = Queue()
        self.video_ready = threading.Event()
        self.detect_commands_running = threading.Event()  # Signal to pause/resume command detection


    def detect_commands(self):
        while not rospy.is_shutdown():
            # Wait if command detection is paused
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

        # Initialize and play audio if present
        if video_clip.audio:
            video_clip.audio.write_audiofile("temp_audio.mp3", fps=44100)
            pygame.mixer.init()
            pygame.mixer.music.load("temp_audio.mp3")
            pygame.mixer.music.play()

        # Play frames while audio is active
        for frame in video_clip.iter_frames(fps=24, with_times=False):
            if not pygame.mixer.music.get_busy():  # Stop if audio ended
                break

            frame_surface = pygame.surfarray.make_surface(np.swapaxes(frame, 0, 1))
            frame_surface = pygame.transform.scale(frame_surface, (self.window_width, self.window_height))
            self.window.blit(frame_surface, (0, 0))
            pygame.display.flip()

        # Make sure to stop the audio if it isn't already.
        pygame.mixer.music.stop()
        video_clip.close()

        # Resume command detection after playing video
        self.detect_commands_running.set()

    def generate_video(self, respuesta):
        try:
            
            video_clip = total_video_generation(respuesta)
            self.video_queue.put(video_clip)
            self.video_ready.set()

            # Pause command detection while video is being generated
            self.detect_commands_running.clear()

        except Exception as e:
            rospy.logerr(f"Error generando video: {e}")

    def show_special_image(self, image_path,sleep_time=5):
        image = pygame.image.load(image_path)

        # Clear the window before drawing the new image
        self.window.fill((0, 0, 0))  # Fill the window with black (RGB: 0, 0, 0)
    
        self.window.blit(image, (0, 0))
        pygame.display.flip()
        time.sleep(sleep_time)  # Display the image for 5 seconds
    

    def main(self):
        clock = pygame.time.Clock()
        running = True
        
        # Start thread for command detection
        command_thread = threading.Thread(target=self.detect_commands, daemon=True)
        command_thread.start()

        
        # Activate command detection initially
        self.detect_commands_running.set()

        while running and not rospy.is_shutdown():
            

            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False


                # Get current time
                current_ticks = pygame.time.get_ticks()

                # Play video if ready
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

                    # Show special image if the number is "1", "2", or "4"
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
                        # Add list of durations for each image
                        TIEMPOS_IMAGENES_BARNEY = [0.1, 2.0]
    
                        # PLAY BARNEY SONG
                        # Initialize pygame mixer
                        pygame.mixer.init()
    
                        # Load MP3 file
                        archivo_mp3 = current_dir + "/songs/Te quiero - Barney Latinoamérica.mp3"  # Reemplaza con la ruta de tu archivo MP3
                        pygame.mixer.music.load(archivo_mp3)

                        # Play the file
                        pygame.mixer.music.play()

                        # Wait while the audio is playing
                        while pygame.mixer.music.get_busy():
                            # pygame.time.Clock().tick(10)  # Avoid high CPU usage
                            for i, imagen in enumerate(SECUENCIA_IMAGENES_BARNEY):
                                # Handle events to prevent window from freezing
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        pygame.mixer.music.stop()
                                        pygame.quit()
                                        exit()
                                self.show_special_image(imagen,TIEMPOS_IMAGENES_BARNEY[i])
                        
                        # Ensure the audio is stopped if it is not already
                        pygame.mixer.music.stop()

                    self.number = str(1)
                    self.pub_commands.publish(f"{self.number}")
                    print(f"Publicado: {self.number}")

                # Switch image if time condition is met
                elif (current_ticks - self.last_switch_time) / 1000.0 >= self.current_time:
                    self.current_image = next(self.expressions)
                    self.current_time = next(self.times)
                    self.last_switch_time = current_ticks

                    # Display the current image
                    image = pygame.image.load(self.current_image)

                    # Clear the window before drawing the new image
                    self.window.fill((0, 0, 0))  # Fill the window with black (RGB: 0, 0, 0)

                    self.window.blit(image, (0, 0))
                    pygame.display.flip()

                    moverVentana()

                    # Update window position using wmctrl
                    subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-e', f'0,{window_position[0]},{window_position[1]},-1,-1'])


                    # Update the display
                clock.tick(60)


            except Exception as e:
                print(f"Error en el bucle principal: {e}")
                running = False


        pygame.quit()
        print("Programa finalizado correctamente.")


if __name__ == "__main__":
    face = final_face()
    face.main()
