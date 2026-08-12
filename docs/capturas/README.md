Colocar aqui las capturas pedidas en el informe:

- `serial-publicador.png` — monitor serial del ESP32 publicador
- `serial-suscriptor.png` — monitor serial del ESP32 suscriptor
- `lcd-suscriptor.png` — LCD del suscriptor en Wokwi
- `wireshark-mqtt.png` — filtro `mqtt` o `tcp.port == 1883`
- `wireshark-tcp.png` — handshake TCP hacia el broker

Como obtenerlas:
1. Simular publicador y suscriptor en Wokwi.
2. Capturar el Serial Monitor de ambos.
3. Icono WiFi en Wokwi -> descargar PCAP -> abrir en Wireshark.
