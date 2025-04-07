# SoftwareInteractive
Development of a Multi-Platform AI-Based Software for Managing Children's Stress in Hospitals
![Imagen de Yaren](https://github.com/RAMEL-ESPOL/YAREN/blob/main/YarenPerfil.png)

## Ejecución del funcionamiento
### Primer paso
Habilitar permisos 
```bash
git clone https://github.com/RAMEL-ESPOL/SoftwareInteractive.git
```

Ingresar a la siguiente dirección
```bash
    cd/SoftwareInteractive
```

Instalar las siguientes dependencias
```bash
    sudo apt install -y portaudio19-dev python3-pyaudio wmctrl ffmpeg
```

```bash
    pip install -r requirements.txt
```

En caso de no tener instalado ROS, visitar: https://wiki.ros.org/ROS/Installation
Se recomienda instalar las extensiones de python y pyhton debugger

Recordar dar permisos a los archivos con chmod +x nomarchivo.launch

    catkin_make

    source devel/setup.bash

Para correr el sistema de expresión facial 
    roslaunch software_interactive multiplatform.launch








