# Estación de superficie del ROV

Esta aplicación opera el ROV por un adaptador USB-RS485, muestra vídeo
analógico capturado por una EasyCap y presenta la telemetría del ESP32.

## Instalación

Desde la raíz del repositorio:

```bash
python3 -m venv ~/rov_venv
~/rov_venv/bin/pip install -r surface_app/requirements.txt
```

El usuario que ejecute la aplicación debe tener acceso al puerto serie, por
ejemplo mediante el grupo `dialout` en Linux. La cámara USB se selecciona como
índice (`0`, `1`, etc.) o como URL RTSP.

## Ejecución

```bash
~/rov_venv/bin/python -m surface_app.main --port /dev/ttyUSB0 --video 0
~/rov_venv/bin/python -m surface_app.main --port COM3 --video rtsp://usuario:clave@host/stream
~/rov_venv/bin/python -m surface_app.main --no-video
```

También se puede crear `config.json` en el directorio de ejecución:

```json
{
  "serial_port": "/dev/ttyUSB0",
  "baudrate": 57600,
  "video_source": 0,
  "deadzone": 0.1,
  "invert_x": false,
  "invert_y": false,
  "invert_z": false,
  "send_rate": 20
}
```

## Recordatorio de cableado

El par azul/azul-blanco es RS-485 A/B y debe llevar una terminación de 120
ohmios en cada extremo. El par naranja/naranja-blanco lleva vídeo compuesto
entre los dos baluns. Los pares verde y marrón duplicados llevan 12 V y
retorno. No conectar el MAX485 al ESP32 sin verificar los niveles lógicos del
módulo. Consultar `docs/hardware_guide.md` y ejecutar la prueba hidrostática
antes de sumergir el conjunto.

## Mapa de botones y controles

| Entrada | Acción |
|---|---|
| Eje 0 | X, avance y retroceso |
| Eje 1 | Y, inmersión y emersión |
| Eje 2 | Z, giro |
| Botón 0 | Armado mientras está pulsado |
| Botón 1 | Parada de emergencia |
| Botón 2 | Luces |
| Botón ARMAR | Armado desde la interfaz |
| Botón DESARMAR | Parada y desarmado |
| Botón PARADA DE EMERGENCIA | Parada inmediata y bloqueo hasta rearmar |
| Botón RECONECTAR | Reapertura del enlace serie |

La zona muerta predeterminada es 10 % en la superficie y ±10 cuentas en el
firmware. Ante una desconexión del joystick, una excepción o el cierre de la
ventana, la aplicación envía la trama neutral desarmada.
