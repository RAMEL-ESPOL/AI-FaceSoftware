# Multi-Platform AI-Based Software for Managing Children's Stress
![Imagen de Yaren](https://github.com/RAMEL-ESPOL/SoftwareInteractive/blob/main/MultiplatformSoftware.png)

## Ejecución del funcionamiento
Clonar el repositorio
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
```bash
roslaunch software_interactive multiplatform.launch
```
## Movimientos Corporales y juegos
![Imagen de Yaren](https://github.com/RAMEL-ESPOL/SoftwareInteractive/blob/main/MultiplatformSoftware.png)
En caso de querer acceder al repositorio acerca del control de los motores para poder tener interacciones no verbales (bailes, movimientos corporales, etc) y poder jugar en la pantalla LCD mediante las articulaciones del robot, visitar el siguiente enlace: https://github.com/RAMEL-ESPOL/YAREN.git.






