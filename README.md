# Arquitectura Zero Trust para una red IoT

Para esta tarea armé el diseño alrededor de una planta de manufactura. Hay sensores de temperatura y vibración, actuadores/PLC que pueden parar una línea, un gateway en el edge, un dashboard de operaciones y técnicos que entran a configurar equipos. Me pareció un caso útil porque mezclan telemetría (poco riesgo) con comandos a maquinaria (mucho riesgo).

La idea de base es simple: no le creo a nadie por estar “dentro” de la fábrica. Cada dispositivo y cada usuario tiene que autenticarse, y solo puede hacer lo mínimo que necesita.

## Principios que apliqué

- Nunca confiar, siempre verificar. Un sensor en la VLAN de planta no gana acceso automático a nada.
- Mínimo privilegio. El sensor manda lecturas y punto. El técnico no toca todos los actuadores “porque es técnico”.
- Asumir que la red ya está comprometida. Por eso corto el tráfico este-oeste y cifro aunque el cable sea interno.
- La identidad es el perímetro, no el firewall de borde.
- Todo lo que no está explícitamente permitido, se deniega.
- Sin visibilidad no hay Zero Trust de verdad. Si no veo quién habla con quién, no puedo decidir ni detectar rarezas.

## Cómo quedó la arquitectura

**Identidad.** Cada sensor lleva un certificado de dispositivo (idealmente en un chip seguro), no una clave compartida en el firmware. El alta la hago con un servicio de provisioning, y si un equipo se pierde o lo clonan, revoco el certificado. Las personas entran por un IdP con MFA. Las apps (analítica, orquestador de comandos) también tienen identidad propia, no “la cuenta del servidor”.

**Microsegmentación.** No dejé una VLAN IoT gigante. Separé sensores, actuadores, gateway, red de mantenimiento, IT de oficina y la plataforma en la nube. Un sensor solo puede hablar con el gateway. No puede hablar con otro sensor ni con un PLC. Los comandos a actuadores salen de otra zona, no del mismo tubo de telemetría.

**Dónde aplico las políticas (PEP).** El gateway IoT autentica certificados, limita tópicos MQTT y hace rate limit. Entre zonas hay un firewall que por defecto niega todo. El IoT Hub / API gateway controla a usuarios y servicios. Las decisiones las toma un motor de políticas; los PEP solo ejecutan. Para mantenimiento no se entra directo al PLC: se pasa por un jump host con PAM.

**Visibilidad.** Inventario de dispositivos (modelo, firmware, certificado), logs del gateway y del firewall, y un baseline por tipo de equipo. Un sensor de temperatura no debería abrir SSH ni cambiar de destino de un día para otro. Eso termina en un SIEM.

**Automatización.** Si el certificado es inválido o el firmware está viejo, el dispositivo queda en cuarentena (le corto salida y revoco acceso al hub). Si aparece tráfico raro este-oeste, se cierra el camino y se abre un ticket. Cuando doy de baja un equipo, se revoca solo.

## Reglas de acceso

### 1. Sensor de vibración → solo telemetría

- **Sujeto:** sensor `DEV-VIB-L2-014` con su certificado.
- **Recurso:** broker MQTT del gateway, tópico `factory/line2/vibration/DEV-VIB-L2-014/data`.
- **Acción:** permitir PUBLISH. Denegar subscribe, otros tópicos y cualquier gestión (SSH, HTTP).
- **Contexto:** solo desde la subred de sensores, MQTT/TLS con mTLS, firmware mínimo `1.4.2`, certificado vigente, máximo 1 mensaje por segundo.
- **Por qué es Zero Trust:** no le confío la red de planta. Verifico quién es y le doy un solo destino y una sola acción.

### 2. Técnico → configurar un actuador

- **Sujeto:** `ana.torres`, rol de mantenimiento de planta 2.
- **Recurso:** interfaz de configuración del actuador `ACT-ESTOP-L2-01`, vía jump host.
- **Acción:** leer estado y cambiar umbrales. No flash de firmware ni tocar lógica de seguridad sin un cambio aprobado.
- **Contexto:** MFA, sesión PAM de 30 min, red de mantenimiento o VPN con el PC en regla, horario 07:00–19:00, ticket ITSM aprobado.
- **Por qué es Zero Trust:** ser técnico no es un pase libre. Reviso identidad, horario, postura del equipo y el ticket. Un activo, un rato, pocas acciones.

### 3. App de analítica → leer datos, nunca mandar comandos

- **Sujeto:** service principal `sp-analytics-predictive`.
- **Recurso:** API `https://iot.empresa.com/api/v1/telemetry`.
- **Acción:** GET de lecturas. Denegar POST/PUT a comandos, config o device twin.
- **Contexto:** mTLS desde la red de analítica, scope `telemetry.read`, rate limit.
- **Por qué es Zero Trust:** que la app sea “interna” no la hace de confianza. Si se compromete el data lake, no quiero que mueva maquinaria.

### 4. Operador → ver el dashboard, no actuar

- **Sujeto:** usuario de turno, rol `Plant-Operator`.
- **Recurso:** dashboard de KPIs y alarmas.
- **Acción:** visualizar. Sin stop/start de línea, sin cambiar umbrales, sin exportar todo.
- **Contexto:** SSO + MFA, PC corporativo compliant, no desde Wi-Fi de invitados, reautenticación cada 8 h.
- **Por qué es Zero Trust:** el dashboard está adentro, pero eso no alcanza. Ver no es controlar.

### 5. Parar la línea (emergencia)

- **Sujeto:** servicio `cmd-orchestrator` más un supervisor que aprueba el mismo flujo.
- **Recurso:** comando `EmergencyStop` hacia `ACT-LINE2-STOP`.
- **Acción:** solo ese comando. Nada de `SetSpeed`, desactivar interlocks ni update de firmware por acá.
- **Contexto:** mTLS del servicio + MFA del supervisor, origen en la zona de control, comando firmado y con TTL de 60 s, auditoría. Si el equipo tiene una CVE grave sin parche, igual dejo el stop de seguridad y bloqueo el resto.
- **Por qué es Zero Trust:** el camino más peligroso no se abre “porque estamos en planta”. Cada comando se verifica, se limita y se registra.

En la práctica, encima de estas cinco, dejaría un deny all para sensor↔sensor y sensor↔PLC. Si no lo pongo explícito, tarde o temprano alguien conecta las zonas y se acaba el aislamiento.
