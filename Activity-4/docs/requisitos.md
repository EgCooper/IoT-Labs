# Requisitos, historias de usuario y criterios de aceptación

## Requisitos funcionales

| ID | Requisito |
|----|-----------|
| RF-01 | El nodo debe muestrear LDR, DHT22 y HC-SR04 de forma periódica. |
| RF-02 | Si la intensidad de luz es menor que 300 y la temperatura supera 30 °C, debe activar ventilación (LED azul) y paso peatonal (LED verde). |
| RF-03 | Si la distancia es menor que 30 cm, debe activar semáforo rojo y alarma sonora. |
| RF-04 | Si la temperatura supera 35 °C y la humedad es menor que 40 %, debe activar la alerta combinada (tres LED y buzzer). |
| RF-05 | El LCD 16x2 y el monitor serial deben mostrar valores sensados y el estado del sistema. |
| RF-06 | Una lectura inválida no debe disparar la regla que depende de ese sensor (fail-safe). |
| RF-07 | El operador debe poder reproducir tres escenarios urbanos por Serial (`1`, `2`, `3`) o con los sliders de Wokwi. |

## Requisitos no funcionales

| ID | Tipo | Requisito |
|----|------|-----------|
| RNF-01 | Latencia | El lazo de control debe reaccionar en menos de 250 ms (proximidad y luz). El DHT22 se actualiza cada 2 s por limitación del sensor. |
| RNF-02 | Escalabilidad | Pines y umbrales viven en `config.h`; la lógica no hardcodea GPIO ni constantes mágicas en el loop. |
| RNF-03 | Robustez | Histéresis en luz (+50) y distancia (+5 cm) para evitar chattering en el umbral. |
| RNF-04 | Seguridad eléctrica | LED con 220 Ω; HC-SR04 alimentado a 5 V; en hardware real el ECHO lleva divisor 5 V → 3,3 V. |
| RNF-05 | Mantenibilidad | Módulos sensores / control / actuadores / display con responsabilidades únicas. |
| RNF-06 | Observabilidad | Serial a 115200 con flags C1/C2/C3 y salud de cada sensor. |
| RNF-07 | Portabilidad | Compila con PlatformIO (`esp32dev`) y se simula en Wokwi. |
| RNF-08 | Disponibilidad | Timeouts en el ultrasónico; no se usa `delay()` en el lazo principal. |

## Historias de usuario

### HU-01 — Ventilación y paso en anochecer caluroso

**Como** operador de movilidad y confort urbano,  
**quiero** que el nodo encienda ventilación y habilite el paso peatonal cuando oscurece y hace calor,  
**para** reducir el estrés térmico en el cruce y señalar que se puede cruzar.

**Criterios de aceptación**

1. Dado luz = 180 e intensidad válida, y temperatura = 32,5 °C con DHT válido, cuando corre el ciclo de control, entonces el LED azul y el LED verde quedan en ON y el estado es `VENT+PASO`.
2. Dado luz = 500 o temperatura = 28 °C, entonces C1 no se activa (ambos LED de C1 en OFF, salvo que C3 esté activa).
3. Dado un DHT en fallo, entonces C1 permanece inhibida aunque la luz sea baja.
4. En el umbral de luz, la histéresis evita que los LED parpadeen si la lectura oscila entre 290 y 320.

### HU-02 — Semáforo y alarma por proximidad

**Como** peatón o conductor en el cruce,  
**quiero** un semáforo rojo y una alarma si un objeto está a menos de 30 cm del sensor,  
**para** detener el avance y reducir el riesgo de atropello o colisión.

**Criterios de aceptación**

1. Dado distancia = 18 cm válida, entonces LED rojo ON y buzzer activo; estado `PROX ALARMA`.
2. Dado distancia = 40 cm, entonces C2 se desactiva (el semáforo y la alarma de proximidad se apagan si no hay C3).
3. Dado C2 activa a 28 cm, cuando la distancia sube a 32 cm (aún < 35 cm), entonces la alarma **se mantiene** (histéresis). A 36 cm se apaga.
4. Dado un timeout del ultrasónico, entonces C2 se inhibe y el LCD/serial indican `US FAULT` (no hay sirena indefinida).
5. Si C2 y C3 coinciden, el rojo y el buzzer quedan **continuos** (prioridad de seguridad inmediata).

### HU-03 — Alerta combinada por ola de calor seca

**Como** gestor de emergencias urbanas,  
**quiero** una alerta combinada visible y audible si hay calor extremo y aire seco,  
**para** señalar riesgo de estrés térmico o incendio de vegetación/residuos en la vía.

**Criterios de aceptación**

1. Dado T = 37,2 °C y H = 28 % con DHT válido, entonces los tres LED y el buzzer operan en patrón intermitente y el estado es `ALERTA COMB.`.
2. Dado T = 34 °C o H = 45 %, entonces C3 no se activa.
3. Dado DHT en fallo, entonces C3 se inhibe (no hay falsa emergencia climática).
4. El LCD muestra temperatura, humedad y la etiqueta de alerta; el serial lista C3 = ON.

## Trazabilidad

| Historia | RF cubiertos | Escenario de prueba |
|----------|----------------|---------------------|
| HU-01 | RF-02, RF-05, RF-06, RF-07 | Serial `1` / sliders anochecer |
| HU-02 | RF-03, RF-05, RF-06, RF-07 | Serial `2` / distancia < 30 cm |
| HU-03 | RF-04, RF-05, RF-06, RF-07 | Serial `3` / calor seco |
