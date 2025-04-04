from utils import read_file
from asistente import Asistente

import sys
import os

import json

# Agrega la carpeta principal (afuera de audio_processing)
directorio_principal = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(directorio_principal)

CONFIG_PARAMS = read_file(directorio_principal + "/" +"config", "yaml")

def main():

    model = CONFIG_PARAMS["stt"]["model_size"]
    record_timeout = CONFIG_PARAMS["stt"]["recording_time"]
    phrase_timeout = CONFIG_PARAMS["stt"]["silence_break"]
    energy_threshold = CONFIG_PARAMS["stt"]["sensibility"]
    wake_word = CONFIG_PARAMS["asistente"]["wake_word"]

    comandos = CONFIG_PARAMS["comandos"]

    prompt = CONFIG_PARAMS["prompt"]

    respuestas_basicas = {}

    try:
        with open(directorio_principal + "/" + "respuestas_basicas.json", "r", encoding='utf-8') as f:
            respuestas_basicas = json.load(f)
            respuestas_basicas = {key.lower(): value for key, value in respuestas_basicas.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error al cargar respuestas básicas.")
        respuestas_basicas = {}

    while True:
        va = Asistente(model, record_timeout, phrase_timeout, energy_threshold, wake_word,comandos,prompt,respuestas_basicas)
        print(va.listen_movement_comand())
    #va.write_transcript()

if __name__ == "__main__":
    main()

#en caso de que no coja el mic poner esto en bash: rm -rf ~/.config/pulse/ 