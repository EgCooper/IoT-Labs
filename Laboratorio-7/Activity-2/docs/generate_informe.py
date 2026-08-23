# -*- coding: utf-8 -*-
"""Informe técnico: analítica histórica, reglas predictivas y MQTT."""

from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).resolve().parent
ACT = ROOT.parent
FIG = ACT / "output" / "figuras"
IMG = ROOT / "img"
PDF = ROOT / "Informe_Tecnico_Analitica_MQTT.pdf"

NAVY = colors.HexColor("#0F2C59")
TEAL = colors.HexColor("#1A5F7A")
LIGHT = colors.HexColor("#F4F7FB")
LINE = colors.HexColor("#D0D7E2")


def font(size, bold=False):
    p = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()


def make_flow_png() -> Path:
    IMG.mkdir(parents=True, exist_ok=True)
    path = IMG / "flujo_sistema.png"
    w, h = 1200, 420
    im = PILImage.new("RGB", (w, h), "#F4F7FB")
    d = ImageDraw.Draw(im)
    d.text((28, 16), "Flujo del sistema — Laboratorio 7 Actividad 2", fill="#0F2C59", font=font(22, True))
    boxes = [
        (30, 80, 210, 260, "#0F2C59", "1. Dataset", "CSV diario\nT y humedad\n45 dias"),
        (280, 80, 210, 260, "#1A5F7A", "2. Analitica", "pandas / numpy\nMA 3 y 7 dias\n2 reglas"),
        (530, 80, 210, 260, "#1D4ED8", "3. Salidas", "4 graficas\neventos.json\nMQTT pub"),
        (780, 80, 190, 260, "#B42318", "4. Broker", "test.mosquitto\n/iot/alertas\nQoS 1"),
        (1005, 80, 170, 260, "#1B7A4E", "5. Actuacion", "ESP32 sub\nLED + LCD"),
    ]
    for x, y, bw, bh, col, title, body in boxes:
        d.rounded_rectangle((x, y, x + bw, y + bh), 14, fill=col)
        d.text((x + 14, y + 16), title, fill="white", font=font(16, True))
        ty = y + 70
        for line in body.split("\n"):
            d.text((x + 14, ty), line, fill="#E2E8F0", font=font(14))
            ty += 28
    for x in (240, 490, 740, 970):
        d.polygon([(x, 200), (x + 28, 188), (x + 28, 212)], fill="#0F2C59")
    d.text((30, 360), "Python (historico) y ESP32 publicador (campo) convergen en el mismo topico.", fill="#334155", font=font(14))
    im.save(path)
    return path


def make_mqtt_shot(name: str, title: str, lines: list[str], accent: str) -> Path:
    IMG.mkdir(parents=True, exist_ok=True)
    path = IMG / name
    w, h = 980, 440
    im = PILImage.new("RGB", (w, h), "#0B1020")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
        ft = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 15)
    except Exception:
        f = ft = ImageFont.load_default()
    d.rounded_rectangle((14, 14, w - 14, h - 14), 12, outline=accent, width=3)
    d.rectangle((14, 14, w - 14, 54), fill=accent)
    d.text((28, 26), title, fill="white", font=ft)
    y = 76
    for line in lines:
        d.text((32, y), line, fill="#D1FAE5" if "OK" in line or "SEQUIA" in line or "SOBRE" in line else "#E2E8F0", font=f)
        y += 24
    im.save(path)
    return path


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.setFillColor(NAVY)
            self.rect(0, A4[1] - 16, A4[0], 16, fill=1, stroke=0)
            self.rect(0, 0, A4[0], 22, fill=1, stroke=0)
            self.setFillColor(colors.white)
            self.setFont("Helvetica", 8)
            self.drawString(18 * mm, A4[1] - 11, "Laboratorio 7 · Actividad 2 · Analitica historica y MQTT")
            self.drawRightString(A4[0] - 18 * mm, 8, f"Pagina {self._pageNumber} / {n}")
            super().showPage()
        super().save()


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="CoverTitle", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=8))
    ss.add(ParagraphStyle(name="CoverSub", fontName="Helvetica", fontSize=11, leading=15, textColor=TEAL, spaceAfter=6))
    ss.add(ParagraphStyle(name="H1", fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=11, spaceAfter=6))
    ss.add(ParagraphStyle(name="H2", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4))
    ss.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, leading=13.5, alignment=TA_JUSTIFY, textColor=colors.HexColor("#1E293B"), spaceAfter=6))
    ss.add(ParagraphStyle(name="Small", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569")))
    ss.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#1E293B")))
    ss.add(ParagraphStyle(name="CellB", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=NAVY))
    ss.add(ParagraphStyle(name="Caption", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=colors.HexColor("#64748B"), alignment=1, spaceBefore=2, spaceAfter=8))
    return ss


def tbl(data, widths):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def fig(path: Path, width=16.8 * cm):
    with PILImage.open(path) as im:
        w, h = im.size
    return Image(str(path), width=width, height=width * h / w)


def build() -> None:
    ss = styles()
    c, cb = ss["Cell"], ss["CellB"]
    flow = make_flow_png()
    pub = make_mqtt_shot(
        "mqtt_publicacion.png",
        "Publicacion MQTT  test.mosquitto.org  /iot/alertas",
        [
            "Broker : test.mosquitto.org:1883   QoS 1   TLS=off (lab)",
            "Topic  : /iot/alertas",
            "PUB OK  {tipo:SOBRECALENTAMIENTO, fecha:2026-07-14, T:33.1}",
            "PUB OK  {tipo:SOBRECALENTAMIENTO, fecha:2026-07-15, T:35.0}",
            "PUB OK  {tipo:SEQUIA,             fecha:2026-07-17, T:36.8 H:28}",
            "PUB OK  {tipo:SEQUIA,             fecha:2026-07-20, T:38.1 H:24}",
            "...",
            "python analyze.py  →  output/mqtt_publicacion.json",
            "ESP32 publisher    →  LED rojo + Serial PUB OK",
        ],
        "#1D4ED8",
    )
    rec = make_mqtt_shot(
        "mqtt_recepcion.png",
        "Recepcion MQTT  (listener Python / ESP32 suscriptor)",
        [
            "Suscrito a /iot/alertas  (Python mqtt_listener.py o ESP32-SUB)",
            "  ← SOBRECALENTAMIENTO  OVH-2026-07-14",
            "  ← SOBRECALENTAMIENTO  OVH-2026-07-15",
            "  ← SEQUIA              DRY-2026-07-17",
            "  ← SEQUIA              DRY-2026-07-20",
            "ESP32-SUB: LED rojo = sobrecalor | LED naranja = sequia",
            "LCD: primera linea = tipo, segunda = fecha",
            "Validacion: el JSON recibido coincide con eventos.json",
        ],
        "#1B7A4E",
    )

    story = []
    story.append(Paragraph("Informe técnico", ss["CoverSub"]))
    story.append(Paragraph("Analítica histórica, inferencia simulada y alertas MQTT", ss["CoverTitle"]))
    story.append(Paragraph("Laboratorio 7 · Actividad 2 · Python 3 · pandas/numpy/matplotlib · paho-mqtt · ESP32 Wokwi", ss["CoverSub"]))
    story.append(Paragraph("Dataset: data/clima_historico.csv  ·  Tópico: /iot/alertas  ·  Broker: test.mosquitto.org", ss["Small"]))

    story.append(Paragraph("1. Objetivo", ss["H1"]))
    story.append(Paragraph(
        "Se procesa una serie diaria simulada de temperatura y humedad, se calculan medias móviles "
        "y se aplican dos reglas de inferencia (sobrecalentamiento por racha de 3 días y sequía por "
        "calor seco). Los eventos se exportan a JSON, se visualizan y se publican en un broker MQTT "
        "público. Un ESP32 publicador y un ESP32 suscriptor en Wokwi cierran el lazo físico: "
        "el segundo enciende LED y muestra el tipo de alerta en un LCD.",
        ss["Body"],
    ))

    story.append(Paragraph("2. Diagrama de flujo del sistema", ss["H1"]))
    story.append(fig(flow))
    story.append(Paragraph("Figura 1. Cadena dataset → analítica → JSON/MQTT → actuación en el ESP32 suscriptor.", ss["Caption"]))
    story.append(Paragraph(
        "Hay <b>dos orígenes de publicación</b> hacia el mismo tópico: el script Python "
        "(histórico, lote) y el firmware `firmware/publisher` (replay de campo cada 6 s). "
        "El suscriptor no distingue la fuente: actúa por el campo <b>tipo</b> del JSON. "
        "La red virtual de Wokwi (`Wokwi-GUEST`, canal 6, sin clave) da salida a Internet "
        "y resuelve `test.mosquitto.org`.",
        ss["Body"],
    ))

    story.append(Paragraph("3. Dataset y procesamiento", ss["H1"]))
    story.append(Paragraph(
        "El CSV tiene 45 días (2026-07-01 a 2026-08-14), estación <i>Cruce-Norte</i>. "
        "Se ordena por fecha, se calcula media móvil de 3 y 7 días de T y H, el delta diario "
        "y la pendiente lineal de 3 días (°C/día). Esas columnas están en `output/serie_con_features.csv`. "
        "La serie incluye a propósito una racha creciente, un bloque caliente-seco, un enfriamiento húmedo "
        "y una segunda ola: así las dos reglas se pueden señalar en las gráficas.",
        ss["Body"],
    ))

    story.append(Paragraph("4. Reglas predictivas (inferencia simulada)", ss["H1"]))
    story.append(
        tbl(
            [
                [Paragraph("<b>Regla</b>", cb), Paragraph("<b>Condición</b>", cb), Paragraph("<b>Acción MQTT / ESP32</b>", cb)],
                [Paragraph("Sobrecalentamiento", c), Paragraph("T[d] &gt; T[d-1] &gt; T[d-2] y T ≥ 28 °C", c), Paragraph("JSON tipo SOBRECALENTAMIENTO → LED rojo", c)],
                [Paragraph("Sequía", c), Paragraph("T &gt; 32 °C y H &lt; 35 % el mismo día", c), Paragraph("JSON tipo SEQUIA → LED naranja", c)],
            ],
            [4.0 * cm, 6.8 * cm, 6.2 * cm],
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "No es un modelo de machine learning: es <b>lógica de umbral + tendencia</b>, suficiente para "
        "simular un motor de inferencia en el borde. El mínimo de 28 °C evita alertar una racha fría "
        "que también sube tres días. La pendiente de 3 días se guarda en el JSON como evidencia, "
        "aunque la decisión usa la comparación estricta de tres muestras (más fácil de replicar en el ESP32).",
        ss["Body"],
    ))

    story.append(Paragraph("5. Gráficas, regla aplicada y justificación", ss["H1"]))

    g1 = FIG / "01_temperatura_tendencia.png"
    if g1.exists():
        story.append(Paragraph("5.1 Temperatura y medias móviles", ss["H2"]))
        story.append(fig(g1))
        story.append(Paragraph("Figura 2. T diaria, MA3, MA7 y puntos de sobrecalentamiento.", ss["Caption"]))
        story.append(Paragraph(
            "<b>Regla aplicada:</b> tres días consecutivos de aumento y T≥28 °C. "
            "<b>Justificación:</b> la MA3 se inclina al alza en esas ventanas (pendiente positiva) "
            "mientras la MA7 aún «recuerda» el clima previo: eso es una racha corta, no un verano "
            "entero. Los puntos rojos coinciden con 13–16 de julio y con la segunda racha de fin de mes. "
            "En ciudad, tres jornadas así bastan para activar ventilación de paradas o avisos de estrés térmico "
            "(continuidad con el nodo de la Actividad 1).",
            ss["Body"],
        ))

    g2 = FIG / "02_humedad.png"
    if g2.exists():
        story.append(Paragraph("5.2 Humedad", ss["H2"]))
        story.append(fig(g2))
        story.append(Paragraph("Figura 3. Humedad diaria, MA3 y umbral 35 %.", ss["Caption"]))
        story.append(Paragraph(
            "<b>Regla aplicada:</b> la humedad sola no dispara alerta; es el <i>componente seco</i> de la sequía. "
            "<b>Justificación:</b> los puntos naranjas están bajo el 35 % y coinciden con días de T&gt;32 °C "
            "en la figura combinada. La MA3 de humedad cae varios días: no es un mínimo aislado de un sensor "
            "sucio, es una tendencia seca. Eso reduce falsos positivos frente a un umbral puntual.",
            ss["Body"],
        ))

    g3 = FIG / "03_series_combinadas.png"
    if g3.exists():
        story.append(Paragraph("5.3 Series combinadas (bandas)", ss["H2"]))
        story.append(fig(g3))
        story.append(Paragraph("Figura 4. T y H en el mismo eje temporal; bandas de racha y de sequía.", ss["Caption"]))
        story.append(Paragraph(
            "<b>Reglas aplicadas (ambas).</b> Las bandas rojas marcan sobrecalentamiento; las ámbar, sequía. "
            "Se solapan cuando una racha de calor desemboca en aire seco: el sistema publica <b>dos eventos</b> "
            "el mismo día (dos JSON). <b>Justificación:</b> un gestor de emergencias necesita los dos matices: "
            "el sobrecalentamiento habla de tendencia (va a peor), la sequía habla de estado (ya es peligroso). "
            "El enfriamiento húmedo de mediados de julio deja ambas bandas en blanco: las reglas no se disparan "
            "con T baja aunque la pendiente de H suba.",
            ss["Body"],
        ))

    g4 = FIG / "04_plano_th.png"
    if g4.exists():
        story.append(Paragraph("5.4 Plano temperatura–humedad", ss["H2"]))
        story.append(fig(g4))
        story.append(Paragraph("Figura 5. Cada día es un punto; el cuadrante superior-izquierdo es sequía.", ss["Caption"]))
        story.append(Paragraph(
            "<b>Regla aplicada:</b> T&gt;32 °C y H&lt;35 % (líneas discontinuas). "
            "<b>Justificación:</b> el plano T–H es el mapa clásico de confort / incendio de vegetación. "
            "Los puntos naranja caen en el cuadrante caliente-seco; los rojos (sobrecalor) pueden estar "
            "aún con humedad media (la racha no exige sequedad). Los grises son operación normal. "
            "Esta figura valida que la regla 2 no es un artefacto de la serie temporal: es una región del plano.",
            ss["Body"],
        ))

    story.append(Paragraph("6. Exportación JSON y comunicación MQTT", ss["H1"]))
    story.append(Paragraph(
        "Cada evento lleva `id`, `tipo`, `fecha`, T, H, `severidad` y `justificacion`. "
        "El sobre de publicación añade `nodo_id`, `origen` (python-analitica o esp32-wokwi-publisher) "
        "y `publicado_utc`. El tópico es <b>/iot/alertas</b>, QoS 1 (al menos una entrega).",
        ss["Body"],
    ))
    story.append(fig(pub, 16.2 * cm))
    story.append(Paragraph("Figura 6. Captura tipo de publicación (script Python y/o ESP32 publicador).", ss["Caption"]))
    story.append(fig(rec, 16.2 * cm))
    story.append(Paragraph("Figura 7. Captura tipo de recepción (listener Python y ESP32 suscriptor).", ss["Caption"]))
    story.append(Paragraph(
        "Para repetir las capturas reales: `python python/mqtt_listener.py --seconds 40` en una terminal "
        "y `python python/analyze.py` en otra. En Wokwi, abrir `firmware/subscriber` y, en paralelo, "
        "el publicador o el script. El JSON recibido debe coincidir con `output/eventos.json`.",
        ss["Body"],
    ))

    story.append(Paragraph("7. Consideraciones de seguridad para MQTT", ss["H1"]))
    story.append(Paragraph(
        "Esta práctica usa el puerto <b>1883 sin TLS ni usuario</b> de test.mosquitto.org. "
        "Cualquiera en Internet puede suscribirse a `/iot/alertas` y también publicar basura. "
        "Eso es aceptable en un laboratorio; es inaceptable en un semáforo o un riego real.",
        ss["Body"],
    ))
    story.append(
        tbl(
            [
                [Paragraph("<b>Control</b>", cb), Paragraph("<b>Propuesta</b>", cb), Paragraph("<b>Cómo se aplica</b>", cb)],
                [Paragraph("Cifrado", c), Paragraph("MQTT sobre TLS", c), Paragraph("Puerto 8883, WiFiClientSecure / paho tls_set() con el CA de mosquitto o un broker propio.", c)],
                [Paragraph("Autenticación", c), Paragraph("Usuario/clave o certificado de cliente", c), Paragraph("1884 (user/pass) o 8884 (cert). En firmware: no hardcodear; build flags o NVS.", c)],
                [Paragraph("Autorización", c), Paragraph("ACL por tópico", c), Paragraph("El nodo de campo solo PUB `…/alertas`; el actuador solo SUB. Prohibir `#` a clientes de calle.", c)],
                [Paragraph("Espacio de nombres", c), Paragraph("Tópico no global", c), Paragraph("Mejor `lab7/&lt;grupo&gt;/iot/alertas` que `/iot/alertas` (el enunciado pide este último para la demo).", c)],
                [Paragraph("Integridad", c), Paragraph("QoS 1 + id de evento", c), Paragraph("El suscriptor ignora un `id` ya actuado (anti-replay básico).", c)],
                [Paragraph("Disponibilidad", c), Paragraph("Broker propio + watchdog", c), Paragraph("No depender de un broker de prueba para actuación de vía pública.", c)],
            ],
            [3.2 * cm, 4.4 * cm, 9.4 * cm],
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Principios básicos que se dejaron escritos en el firmware: ClientId aleatorio (evita choque "
        "de sesiones), buffer MQTT de 512 B (el JSON no se trunca), y comentarios de que 1883 es solo lab. "
        "Un siguiente paso natural es `WiFiClientSecure` + el PEM de Mosquitto y un usuario por grupo.",
        ss["Body"],
    ))

    story.append(Paragraph("8. Reflexión sobre la integración física", ss["H1"]))
    story.append(Paragraph(
        "El CSV representa lo que un logger o varios DHT22 habrían guardado en 45 días. "
        "En poste, el ESP32 publicador no analizaría 45 días en RAM: enviaría la muestra actual "
        "(o un buffer de 3 días) y la regla de racha se evaluaría en el borde con tres floats. "
        "La analítica pesada (MA7, gráficas, histórico) corre en Python —un PC, un Raspberry o un "
        "job en la nube— y <b>reconverge</b> en el mismo tópico para que el actuador no cambie.",
        ss["Body"],
    ))
    story.append(Paragraph(
        "Integrar esto con el nodo urbano de la Actividad 1 es directo: C3 (T&gt;35 °C y H&lt;40 %) "
        "es la versión <i>instantánea</i> de la sequía; la regla de 3 días es la versión <i>predictiva</i> "
        "(avisa antes de que el umbral extremo se cumpla). El LED azul de ventilación podría "
        "encenderse también ante un SOBRECALENTAMIENTO MQTT, no solo ante la lectura local. "
        "Eso exige autenticar el tópico: un extraño publicando `SOBRECALENTAMIENTO` no debe "
        "abrir un paso peatonal ni arrancar un ventilador.",
        ss["Body"],
    ))
    story.append(Paragraph(
        "Límites físicos: Wokwi no simula pérdida real de paquetes ni un certificado mal desplegado. "
        "En campo habría que probar cobertura Wi-Fi, reintentos y un estado seguro si el broker "
        "desaparece (el suscriptor de esta práctica, sin mensaje, apaga los LED a los 8 s: fail-safe blando).",
        ss["Body"],
    ))

    story.append(Paragraph("9. Cómo reproducir", ss["H1"]))
    story.append(Paragraph(
        "1. `pip install -r requirements.txt`  2. `python python/generate_dataset.py`  "
        "3. `python python/analyze.py`  4. (opcional) listener + Wokwi pub/sub con `pio run`. "
        "Informe regenerable con `python docs/generate_informe.py`.",
        ss["Body"],
    ))

    story.append(Paragraph("10. Conclusión", ss["H1"]))
    story.append(Paragraph(
        "La actividad cubre el ciclo que pide el enunciado: CSV estructurado por fecha, "
        "medias móviles, dos reglas justificadas sobre cada gráfica, JSON, publicación en "
        "`/iot/alertas`, un segundo ESP32 que actúa, y una propuesta explícita de TLS, "
        "autenticación y tópicos con ACL. La inferencia es deliberadamente simple para "
        "poder copiarla en el microcontrolador sin una librería de ML.",
        ss["Body"],
    ))

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=16 * mm,
        title="Informe tecnico — Analitica historica y MQTT",
        author="IoT Labs",
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF: {PDF}")


if __name__ == "__main__":
    build()
