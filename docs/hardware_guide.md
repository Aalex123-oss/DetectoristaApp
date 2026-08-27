# Guía de hardware para ROV de 150 m

## Alcance y advertencias de seguridad

Este diseño describe un ROV de inspección de bajo coste para una profundidad de
trabajo de 150 m. No es un vehículo tripulado ni un sistema certificado para
salvamento. La construcción, las pruebas y las inmersiones deben estar a cargo
de personas capacitadas.

* La presión indicada es peligrosa y puede provocar una implosión violenta.
  Nadie debe permanecer encima, debajo ni junto a un recipiente durante una
  prueba de presión.
* Toda prueba hidrostática se hace con agua, a distancia y con una barrera
  física; nunca se prueba un recipiente presurizado con aire.
* La batería de 12 V debe llevar fusible cerca de su terminal positivo,
  conectores aislados y un interruptor de corte accesible en superficie.
* El cable de descenso debe tener alivio de tensión independiente de los
  conductores y no debe usarse para izar el ROV sin un punto mecánico
  dimensionado para ello.
* Se debe comprobar la continuidad, la polaridad, el aislamiento y el
  funcionamiento del paro de emergencia antes de cada inmersión.
* El operador debe mantener comunicación con el equipo de apoyo, registrar la
  profundidad y abortar ante pérdida de vídeo, control o alimentación.
* El presupuesto no incluye certificación, lastre, estructura, herramientas,
  equipo de recuperación ni el adaptador USB-RS485 si no se posee.

## Lista de materiales

Los precios son orientativos en dólares estadounidenses y corresponden a
componentes genéricos. El total de los elementos de esta tabla es **US$97.50**
y no incluye el joystick USB.

| Elemento | Cantidad | Precio (US$) | Sustitución más económica |
|---|---:|---:|---|
| ESP32 DevKit v1 | 1 | 6.00 | ESP32 genérico de segunda mano, US$3–5 |
| L298N dual driver | 2 | 6.00 | Dos puentes H discretos recuperados, US$3–4 |
| Cartucho de bomba de sentina 12 V (thrusters) | 3 | 18.00 | Bombas de achique usadas compatibles, US$12–15 |
| Módulo MAX485 | 2 | 2.00 | Transceptores MAX3485 recuperados, US$1 |
| Cable UTP Cat5e de 150 m | 1 | 18.00 | Cable exterior Cat5e usado, US$10–14 |
| Vídeo balun pasivo | 2 | 5.00 | Baluns recuperados de CCTV, US$2–3 |
| Cámara analógica mini 700TVL | 1 | 6.00 | Cámara CCTV usada, US$3–5 |
| Tarjeta de captura USB (EasyCap) | 1 | 5.00 | Capturadora UVC usada, US$3–4 |
| Fuente 12 V 5 A / batería SLA | 1 | 10.00 | Batería SLA recuperada, US$5–8 |
| Tubo PVC schedule 40 4" + tapón roscado/cleanout | 1 | 8.00 | Tramo corto de PVC recuperado con tapa, US$4–6 |
| Resina epoxi 500 g | 1 | 5.00 | Epoxi marino comprado a granel, US$3–4 |
| Grasa marina + juego de O-rings | 1 | 4.00 | Grasa de silicona y juntas compatibles, US$2–3 |
| Convertidor buck LM2596 + cableado/fusible/termorretráctil | 1 | 4.50 | Buck recuperado y cableado existente, US$2–3 |
| **Total** |  | **97.50** |  |

El adaptador USB-RS485 de superficie puede reutilizarse o pedirse prestado y
contarse como **US$0** si ya está disponible. Como alternativa, un adaptador
nuevo suele costar US$5–10. Un joystick USB es adicional al total.

## Presión, carcasa y prueba obligatoria

La presión hidrostática se estima mediante:

\[
\Delta p=\rho g h=1000\ \mathrm{kg/m^3}\times9.81\ \mathrm{m/s^2}
\times150\ \mathrm{m}\approx1.47\ \mathrm{MPa}
\]

Sumando la atmósfera, la presión absoluta a 150 m es aproximadamente **15.5
bar**, o **1.5 MPa**. La diferencia de presión externa es la que carga la
carcasa. El PVC schedule 40 de 4 pulgadas está diseñado principalmente para
presión interna: bajo presión externa, una imperfección, ovalidad, tapa o
penetrador puede iniciar pandeo y el tubo colapsa antes de que aparezca una
rotura tipo estallido. Por eso el enfoque recomendado es inundar o llenar con
aceite mineral las cavidades que no necesiten aire, usar tramos cortos con
refuerzos y no confiar en una cámara de aire larga de PVC sin cálculo
estructural.

La estructura final debe tener un margen de seguridad mínimo de 2 frente a la
presión de trabajo, y preferiblemente 3 para piezas impresas, tapas
modificadas, juntas y penetradores. El margen debe calcularse sobre la
geometría real, su ovalidad, la temperatura, el envejecimiento y el material;
la presión nominal de una tubería para servicio interno no demuestra
resistencia al colapso externo.

Antes de cualquier inmersión real:

1. Inspeccionar el tubo, tapa, juntas y penetradores, y medir la ovalidad.
2. Montar una carcasa de prueba idéntica y colocar dentro papel indicador de
   humedad, un registrador y una masa inerte; no usar una batería energizada.
3. Probar a una presión equivalente a **1.5 veces la profundidad de trabajo**,
   aproximadamente 225 m de columna de agua (unos 2.2 MPa de diferencia).
   Usar una cámara hidrostática certificada. Como sustituto de laboratorio,
   puede emplearse una columna de agua con bomba de lavadora y un sistema de
   peso muerto que limite la presión, siempre con contención remota y
   manómetro calibrado; no se debe improvisar una cámara cerrada.
4. Mantener la presión de prueba de forma gradual, observar desde lejos y
   descargar lentamente. Cualquier deformación, fuga o ruido invalida la
   pieza.
5. Repetir el montaje a presión de trabajo y dejarlo en remojo **3 días**,
   revisando el indicador de humedad diariamente. Secar, abrir e inspeccionar
   después de la prueba.

## Impermeabilización paso a paso

### Cartuchos de las bombas de sentina

1. Abrir el cartucho y eliminar grasa, polvo y humedad con un limpiador
   compatible. Raspar suavemente las zonas donde se adherirá el epoxi.
2. Guiar los cables por un alivio mecánico. Rellenar con epoxi la cavidad del
   cartucho alrededor de los pasos de cable, sin bloquear las partes móviles.
3. En el canister del motor, usar aceite mineral limpio como compensación de
   presión. El aceite debe ser compatible con el aislamiento, el pegamento y
   la junta; expulsar el aire lentamente antes de cerrar.
4. Mantener un sello mecánico en el eje: la junta del fabricante debe estar
   asentada y se debe añadir un retén radial compatible, no simplemente
   epoxi sobre un eje giratorio.
5. Dejar curar el epoxi según su ficha técnica, normalmente 24 h para
   manipulación y 72 h para carga e inmersión. Después probar aislamiento y
   giro a baja tensión en un recipiente de agua dulce.

### Tapa y penetrador

1. Limpiar la rosca del tapón roscado/cleanout de PVC y las ranuras de dos
   O-rings. Lubricar las juntas con grasa marina sin exceso y apretar a mano
   más el par indicado por el fabricante; no usar cinta como sustituto de las
   juntas.
2. Hacer el penetrador con un racor de compresión. El racor proporciona la
   retención mecánica; la resina proporciona el sello, no debe ser el único
   elemento que soporte el tirón.
3. En el extremo del UTP, retirar únicamente la cubierta exterior dentro del
   racor, separar los conductores y dejar la torsión intacta hasta el punto
   más cercano posible. Sellar cada conductor con epoxi de baja viscosidad
   para detener la migración de agua por el núcleo del cable.
4. Encapsular la zona de transición y el racor, evitando cubrir la rosca o
   crear una arista que corte la cubierta. Mantener el cable sujeto mientras
   cura.
5. Dejar curar 24–48 h según el epoxi; esperar 72 h antes de presurizar.
   Repetir una prueba de vacío o baja presión y revisar el indicador de
   humedad antes de la prueba hidrostática.

### Qué hacer y qué evitar

| Hacer | No hacer |
|---|---|
| Desengrasar, secar y lijar las superficies de unión. | Encapsular suciedad, agua o silicona no compatible. |
| Usar alivio de tensión y doble junta en cada paso crítico. | Colgar el ROV del UTP o de los cables de motor. |
| Respetar mezcla, espesor y curado del epoxi. | Sumergir una pieza que sólo está seca al tacto. |
| Probar primero sin energía y luego a baja tensión. | Alimentar motores durante una fuga o una prueba de presión. |
| Sustituir O-rings dañados y lubricarlos ligeramente. | Reutilizar una junta mordida, plana o endurecida. |
| Medir el aislamiento y documentar cada prueba. | Dar por segura la carcasa sólo porque no entra agua superficial. |

## Cableado y esquema

El UTP lleva un par azul/azul-blanco para RS-485, un par naranja/naranja-blanco
para vídeo compuesto balanceado mediante baluns, y dos pares (verde y marrón)
con conductores duplicados para 12 V y retorno. En ambos extremos del bus
RS-485 se instala una terminación de 120 ohmios entre A y B, colocada junto al
transceptor. No se deben derivar ramales largos.

```text
 [Joystick USB]                       SUPERFICIE
       │
 [PC: pygame + Tkinter + OpenCV]──USB──[USB-RS485]
       │                                  DI/RO/DE/RE
       │                                  │
       │                         azul=A ──┼──────────────┐
       │                    azul-blanco=B ───────────────┤ 150 m Cat5e
       │                                  │              │
       │                 120 Ω A-B ──────┘       [MAX485 subsea]
       │                                                 │
       │                                  UART2 RX GPIO16 / TX GPIO17
       │                                  DE y RE GPIO4
       │                                                 │
       │         ┌───────────────[ESP32]─────────────────┘
       │         │ GPIO25/26/27 → L298N #1 ENA/IN1/IN2 → horizontal izquierdo
       │         │ GPIO32/33/14 → L298N #1 ENB/IN3/IN4 → horizontal derecho
       │         │ GPIO13/5/18   → L298N #2 ENA/IN1/IN2 → thruster vertical
       │         │ GPIO23        → relé de luces
       │         │ GPIO34        ← divisor resistivo de tensión
       │         │
       │         └── buck LM2596 12→5 V, masa común y fusible
       │
 [12 V superficie]══ pares verde + marrón duplicados ══[12 V subsea]
 [Cámara 12 V + vídeo]─balun─par naranja─balun─[captura USB]─PC
```

### Tabla de conexiones

| Origen | Señal | Destino |
|---|---|---|
| PC | USB | Adaptador USB-RS485 |
| USB-RS485 | DI/RO/DE/RE | Según el módulo; DE y `/RE` unidos al control de dirección |
| RS-485 superficie | A/B | Azul=A, azul-blanco=B, 120 Ω en el extremo |
| RS-485 subsea | A/B | MAX485, mismo orden y 120 Ω en el extremo |
| MAX485 | RO | ESP32 UART2 RX GPIO16 |
| ESP32 UART2 | TX GPIO17 | MAX485 DI |
| ESP32 | GPIO4 | DE y `/RE` unidos, transmisión habilitada sólo al enviar |
| ESP32 | GPIO25, GPIO26, GPIO27 | L298N #1 ENA, IN1, IN2 |
| ESP32 | GPIO32, GPIO33, GPIO14 | L298N #1 ENB, IN3, IN4 |
| ESP32 | GPIO13, GPIO5, GPIO18 | L298N #2 ENA, IN1, IN2 |
| ESP32 | GPIO19 | L298N #2 ENB, sin motor; mantener bajo |
| L298N #1 A/B | Salidas | Thrusters horizontales izquierdo/derecho |
| L298N #2 A | Salida | Thruster vertical |
| ESP32 | GPIO23 | Entrada del relé de luces |
| Divisor 100 kΩ/10 kΩ | Salida | ESP32 GPIO34; nunca superar el límite ADC |
| Cámara | 12 V y vídeo compuesto | Alimentación y balun submarino |
| Baluns | Par naranja | Balun de superficie y EasyCap |
| Fuente | 12 V y retorno | Pares verde y marrón duplicados, buck subsea |

El negativo de potencia, las masas de los controladores y la masa lógica deben
estar unidos dentro del ROV. El MAX485 alimentado a 5 V requiere que su salida
RO sea segura para el UART elegido; usar un divisor o un transceptor de 3.3 V
si el módulo no garantiza niveles compatibles con ESP32. En el montaje con
Arduino Uno/Nano se usa la UART hardware disponible y se deben adaptar los
terminales a la placa concreta.

## Protocolo de control

Se transmiten 6 bytes a 20 Hz:

| Byte | Significado |
|---:|---|
| 0 | `0xAA`, inicio |
| 1 | X: avance/retroceso, 0–255, 128 neutral |
| 2 | Y: inmersión/emersión, 0–255, 128 neutral |
| 3 | Z: giro, 0–255, 128 neutral |
| 4 | Flags: bit 0 luces, bit 1 armado, bit 2 emergencia; bits 3–7 en cero |
| 5 | `(X + Y + Z + FLAGS) & 0xFF` |

El firmware descarta una trama con checksum incorrecto. Una zona muerta de
±10 alrededor de 128 detiene cada eje. Si transcurren 500 ms sin una trama
válida, si se activa emergencia o si se desarma, todos los PWM pasan a cero y
ENA/ENB de ambos L298N quedan bajos. La telemetría ASCII sale
aproximadamente cada 250 ms con el formato `TLM;vin=12.4;fps=20;fs=0`.
