---
name: testing-rov-surface-gui
description: How to run and end-to-end test the ROV surface control station GUI (surface_app) on a headless-ish Linux box with no ROV hardware — synthetic video, virtual serial pair + subsea simulator, and a virtual joystick when /dev/uinput is unavailable.
---

# Probar la estación de superficie del ROV (`surface_app`) sin hardware

Todo el texto y los comentarios del proyecto están en español; mantén ese idioma en scripts y logs.

## Ejecución
```bash
~/rov_venv/bin/python -m surface_app.main --port <puerto> --video <fuente>
```
Ejecutar desde la raíz del repo. Requiere `python3-tk` en el sistema y el venv con
`surface_app/requirements.txt`. Si no existe el venv:
`python3 -m venv ~/rov_venv && ~/rov_venv/bin/pip install -r surface_app/requirements.txt`.

## 1. Vídeo sintético que se mueve de verdad
No uses un archivo `.mp4`: OpenCV lo lee a máxima velocidad y se agota en segundos (después el hilo
de captura solo registra "Se perdió la captura de vídeo" y la imagen se congela). Usa un flujo en
tiempo real por UDP/MPEG-TS:
```bash
ffmpeg -re -f lavfi -i "testsrc=size=640x480:rate=20" \
  -vf "drawtext=text='ROV CAM %{pts\:hms}':fontsize=30:fontcolor=yellow:x=12:y=12" \
  -c:v mpeg2video -q:v 4 -f mpegts "udp://127.0.0.1:5000?pkt_size=1316" &
# y arrancar la app con --video udp://127.0.0.1:5000
```
El reloj superpuesto permite demostrar en capturas que la imagen avanza.
`[mpeg2video] Invalid frame dimensions 0x0` en el log es ruido inofensivo.

## 2. Serie virtual + simulador subsea
```bash
socat pty,raw,echo=0,link=/tmp/ttyROV_app pty,raw,echo=0,link=/tmp/ttyROV_sim &
```
Usa `link=` para tener rutas estables: al matar y relanzar socat el mismo enlace reaparece, que es
lo que hace verificable el botón `RECONECTAR`. La app abre `/tmp/ttyROV_app`; el simulador escucha en
`/tmp/ttyROV_sim`, valida `0xAA` + checksum `(X+Y+Z+FLAGS)&0xFF`, imprime `X/Y/Z/flags` y emite
`TLM;vin=12.4;fps=20;fs=0\n` cada 250 ms. Muestra su log en una terminal visible
(`x-terminal-emulator -e bash -c "tail -f /tmp/rovsim.log"`) al lado de la GUI: así la grabación
prueba a la vez lo que ve el operador y lo que recibe el ROV.

Aviso: `SerialLink.open()` reintenta por su cuenta cada 2 s, así que la recuperación tras restaurar
el pty no es atribuible solo al botón `RECONECTAR`; el criterio útil es "no se cae y recupera".

## 3. Joystick virtual cuando no hay `/dev/uinput`
En cajas con kernel sin módulo `uinput` (`modprobe uinput` → *Module uinput not found*) **no** se
puede crear un gamepad con python-evdev. Alternativa que sí funciona: adjuntar un dispositivo real de
SDL con `SDL_JoystickAttachVirtual` mediante `ctypes` sobre la libSDL2 que trae pygame
(`site-packages/pygame.libs/libSDL2-2-*.so*`), en un lanzador que después llama a
`surface_app.main.main(argv)` en el mismo proceso. Así pygame ve "Virtual Controller" (3 ejes,
4 botones) sin tocar el código de la app, y `SDL_JoystickDetachVirtual` lo elimina de la lista de SDL
(`pygame.joystick.get_count()` → 0), que es exactamente la vía de detección de desconexión de
`Joystick.refresh()`. Controla ejes/botones/desconexión desde fuera con un pequeño servidor UDP en el
propio lanzador.

Bytes esperados con `deadzone=0.10` (`Joystick.axis_to_byte`): eje SDL 20000 → 200,
-25000 → 34, 3200 (0.098, dentro de la zona muerta) → 128. Comprobar siempre un caso dentro de la
zona muerta: si aparece algo distinto de 128, la zona muerta está rota.

## Trampas operativas
- No uses `pkill -f socat` ni `pkill -f vjoy_runner` en una línea del propio shell de la herramienta:
  el patrón coincide con la línea de comando del shell y lo mata. Pon esos `pkill` en un script `.sh`.
- Manda `SIGINT` al PID de Python, no al `bash`/`setsid` padre; si no, parece que Ctrl-C no funciona.
- Solo puede haber una instancia del lanzador: la segunda falla al enlazar el puerto UDP de control.

## Qué mirar en la GUI (texto exacto)
- Estado normal: `Serie: conectado | Joystick: <nombre> (conectado)`, `X=128 Y=128 Z=128 | flags=0x00`,
  `paquetes=` ~17-20 Hz, `Telemetría subsea: vin=12.4; fps=20; fs=0`.
- La línea de telemetría **parpadea** entre el valor y `Sin telemetría` porque `control_tick` pasa la
  telemetría del ciclo (None en 4 de cada 5 ciclos) en vez de `link.last_telemetry`.
- Desconexión del joystick: banner rojo `PARADA DE SEGURIDAD: El joystick no está conectado` y solo
  tramas `aa 80 80 80 00 80`.
- `PARADA DE EMERGENCIA` puede fallar de forma sutil: `control_tick` solo actualiza el banner
  `if not self.emergency`, así que el banner se queda congelado (verde) y se siguen enviando los ejes
  del joystick con `flags=0x04` en vez de la trama neutral. Verifica siempre el color del banner y las
  tramas recibidas, no solo el valor de flags.

## Devin Secrets Needed
Ninguno.
