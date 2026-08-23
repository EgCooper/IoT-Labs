# -*- coding: utf-8 -*-
"""Genera el informe técnico PDF y las figuras de la Actividad 4."""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

OUT_DIR = Path(__file__).resolve().parent
IMG_DIR = OUT_DIR / "img"
PDF_PATH = OUT_DIR / "Informe_Tecnico_Nodo_Urbano_IoT.pdf"

NAVY = colors.HexColor("#0F2C59")
TEAL = colors.HexColor("#1A5F7A")
AMBER = colors.HexColor("#C97800")
RED = colors.HexColor("#B42318")
GREEN = colors.HexColor("#1B7A4E")
BLUE = colors.HexColor("#1D4ED8")
LIGHT = colors.HexColor("#F4F7FB")
LINE = colors.HexColor("#D0D7E2")


def ensure_dirs() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)


def draw_rounded_box(c, x, y, w, h, fill, stroke, title, lines, title_color=colors.white):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(title_color)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + w / 2, y + h - 16, title)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#1F2937") if fill == colors.white or fill == LIGHT else colors.white)
    text_y = y + h - 30
    for line in lines:
        c.drawCentredString(x + w / 2, text_y, line)
        text_y -= 11


def draw_arrow(c, x1, y1, x2, y2):
    c.setStrokeColor(NAVY)
    c.setFillColor(NAVY)
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    # simple arrow head
    c.circle(x2, y2, 2.2, fill=1, stroke=0)


def make_architecture_png() -> Path:
    path = IMG_DIR / "arquitectura.png"
    width, height = 1100, 520
    c = pdfcanvas.Canvas(str(path.with_suffix(".pdf")), pagesize=(width, height))
    # We'll render via reportlab canvas to PNG using a temp approach:
    # platypus Image needs raster. Use PIL if available; else keep PDF figure.
    try:
        from reportlab.graphics import renderPM  # noqa: F401
    except Exception:
        pass

    # Draw to a PDF first, then also a PNG via Pillow + reportlab render
    # Simpler: draw PNG with Pillow directly.
    c.save()
    try:
        path.with_suffix(".pdf").unlink(missing_ok=True)
    except Exception:
        pass

    from PIL import Image as PILImage, ImageDraw, ImageFont

    img = PILImage.new("RGB", (width, height), "#F4F7FB")
    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        names = (
            "arialbd.ttf" if bold else "arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        )
        for n in names:
            try:
                return ImageFont.truetype(n, size)
            except Exception:
                continue
        return ImageFont.load_default()

    f_title = font(22, True)
    f_h = font(14, True)
    f_b = font(13)
    d.text((40, 18), "Diagrama tecnico del nodo urbano IoT", fill="#0F2C59", font=f_title)

    boxes = [
        (40, 90, 250, 380, "#0F2C59", "ENTRADAS",
         ["LDR  (intensidad luz)", "DHT22 (T / humedad)", "HC-SR04 (distancia)", "", "Validacion de rango", "Timeout ultrasónico"]),
        (400, 90, 300, 380, "#1A5F7A", "PROCESAMIENTO  ESP32",
         ["sensorsRead()", "controlEvaluate()", "", "C1  luz<300 y T>30", "C2  dist < 30 cm", "C3  T>35 y H<40", "", "Histéresis + fail-safe", "config.h (umbrales)"]),
        (810, 90, 250, 380, "#1B7A4E", "SALIDAS",
         ["LED azul  ventilacion", "LED verde  paso", "LED rojo  semaforo", "Buzzer  alarma", "", "LCD 16x2 I2C", "Monitor serial"]),
    ]
    for x, y, w, h, col, title, lines in boxes:
        d.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=col)
        d.text((x + 16, y + 16), title, fill="white", font=f_h)
        ty = y + 56
        for line in lines:
            d.text((x + 16, ty), line, fill="#E8EEF6", font=f_b)
            ty += 28

    # arrows
    d.polygon([(300, 260), (390, 245), (390, 275)], fill="#0F2C59")
    d.polygon([(710, 260), (800, 245), (800, 275)], fill="#0F2C59")
    d.text((318, 210), "I -> P", fill="#0F2C59", font=f_h)
    d.text((728, 210), "P -> O", fill="#0F2C59", font=f_h)
    d.text((40, 488), "Principio: entrada -> decision -> actuacion, con observabilidad en LCD/Serial.", fill="#334155", font=f_b)
    img.save(path, "PNG")
    return path


def make_flow_png() -> Path:
    path = IMG_DIR / "logica_control.png"
    from PIL import Image as PILImage, ImageDraw, ImageFont

    width, height = 1100, 620
    img = PILImage.new("RGB", (width, height), "#FFFFFF")
    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        p = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            return ImageFont.load_default()

    f_title = font(20, True)
    f_b = font(13)
    f_h = font(13, True)
    d.text((36, 16), "Logica de control implementada", fill="#0F2C59", font=f_title)

    def box(x, y, w, h, fill, text, tc="white"):
        d.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=fill)
        d.text((x + 12, y + h / 2 - 8), text, fill=tc, font=f_b)

    box(40, 70, 1020, 48, "#0F2C59", "Leer sensores  |  validar rangos  |  si Serial 1/2/3: inyectar escenario")
    box(40, 160, 300, 70, "#1A5F7A", "C1  luz<300 AND T>30")
    box(400, 160, 300, 70, "#B42318", "C2  distancia < 30 cm")
    box(760, 160, 300, 70, "#C97800", "C3  T>35 AND H<40")
    box(40, 280, 300, 90, "#1D4ED8", "Azul + Verde  (VENT+PASO)")
    box(400, 280, 300, 90, "#B42318", "Rojo + buzzer continuo")
    box(760, 280, 300, 90, "#C97800", "3 LED + buzzer intermitente")
    box(40, 420, 1020, 80, "#1B7A4E", "Prioridad: C2 (colision)  >  C3 (emergencia climatica)  >  C1 (confort). Pueden coexistir.")
    box(40, 530, 1020, 60, "#334155", "LCD + Serial: valores, flags C1/C2/C3, salud LDR/DHT/US, etiqueta de estado")

    # connectors
    d.line((550, 118, 190, 160), fill="#64748B", width=3)
    d.line((550, 118, 550, 160), fill="#64748B", width=3)
    d.line((550, 118, 910, 160), fill="#64748B", width=3)
    d.line((190, 230, 190, 280), fill="#64748B", width=3)
    d.line((550, 230, 550, 280), fill="#64748B", width=3)
    d.line((910, 230, 910, 280), fill="#64748B", width=3)
    d.text((40, 140), "en paralelo", fill="#64748B", font=f_h)
    img.save(path, "PNG")
    return path


def make_circuit_png() -> Path:
    path = IMG_DIR / "circuito_bloque.png"
    from PIL import Image as PILImage, ImageDraw, ImageFont

    w, h = 1100, 640
    img = PILImage.new("RGB", (w, h), "#0B1220")
    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        p = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            return ImageFont.load_default()

    d.text((36, 20), "Circuito Wokwi — ESP32 DevKit C V4", fill="#E2E8F0", font=font(22, True))
    d.text((36, 54), "Sensores a la izquierda  |  MCU al centro  |  Actuadores y LCD a la derecha/abajo", fill="#94A3B8", font=font(13))

    nodes = [
        (50, 110, 220, 100, "#1E3A5F", "DHT22", "GPIO4  3V3"),
        (50, 240, 220, 100, "#3F2E15", "LDR modulo", "AO -> GPIO34"),
        (50, 370, 220, 100, "#14332A", "HC-SR04", "TRIG5  ECHO18  5V"),
        (420, 200, 260, 180, "#1A5F7A", "ESP32", "SDA21 SCL22"),
        (800, 110, 250, 70, "#7F1D1D", "LED rojo + 220R", "GPIO25 semaforo"),
        (800, 200, 250, 70, "#14532D", "LED verde + 220R", "GPIO26 paso"),
        (800, 290, 250, 70, "#1E3A8A", "LED azul + 220R", "GPIO27 ventilacion"),
        (800, 380, 250, 70, "#4C1D95", "Buzzer", "GPIO14"),
        (360, 470, 380, 100, "#1E293B", "LCD 1602 I2C  0x27", "VCC 5V   GND comun"),
    ]
    for x, y, bw, bh, col, t1, t2 in nodes:
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=12, fill=col, outline="#94A3B8")
        d.text((x + 14, y + 16), t1, fill="white", font=font(16, True))
        d.text((x + 14, y + 48), t2, fill="#CBD5E1", font=font(13))

    # wires
    def wire(a, b, col):
        d.line((a, b), fill=col, width=3)

    wire((270, 160), (420, 250), "#F59E0B")
    wire((270, 290), (420, 290), "#EAB308")
    wire((270, 420), (420, 340), "#22D3EE")
    wire((680, 260), (800, 145), "#EF4444")
    wire((680, 280), (800, 235), "#22C55E")
    wire((680, 300), (800, 325), "#3B82F6")
    wire((680, 340), (800, 415), "#A78BFA")
    wire((550, 380), (550, 470), "#38BDF8")

    d.text((36, 600), "En hardware real: divisor 1 k / 2 k en ECHO. En Wokwi el eco se cablea directo (el sim no modela el 5 V).", fill="#94A3B8", font=font(12))
    img.save(path, "PNG")
    return path


def make_serial_png(name: str, title: str, body: list[str], accent: str) -> Path:
    path = IMG_DIR / name
    from PIL import Image as PILImage, ImageDraw, ImageFont

    w, h = 920, 420
    img = PILImage.new("RGB", (w, h), "#0B1020")
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 16)
        ft = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 16)
    except Exception:
        f = ImageFont.load_default()
        ft = f
    d.rounded_rectangle((16, 16, w - 16, h - 16), radius=12, outline=accent, width=3)
    d.rectangle((16, 16, w - 16, 56), fill=accent)
    d.text((32, 28), title, fill="white", font=ft)
    y = 80
    for line in body:
        d.text((36, y), line, fill="#D1FAE5" if "ON" in line else "#E2E8F0", font=f)
        y += 28
    img.save(path, "PNG")
    return path


def build_serial_figures() -> dict[str, Path]:
    s1 = make_serial_png(
        "escenario1_serial.png",
        "Escenario 1 — Anochecer caluroso (Serial 1)",
        [
            "Modo     : S1 Anochecer caluroso",
            "Luz      : 180 / 1023  (ADC raw 0)  LDR=OK",
            "Clima    : 32.5 C   humedad 55.0 %   DHT=OK",
            "Distancia: 150.0 cm   US=OK",
            "C1 VENT+PASO     : ON",
            "C2 PROXIMIDAD    : off",
            "C3 ALERTA COMB.  : off",
            "Actuadores: R=0 G=1 B=1  Buzzer=0  blink=0",
            "Estado   : VENT+PASO",
            "LCD:  T32.5 H55 L180   |   D150 VENT+PASO",
        ],
        "#1D4ED8",
    )
    s2 = make_serial_png(
        "escenario2_serial.png",
        "Escenario 2 — Proximidad en cruce (Serial 2)",
        [
            "Modo     : S2 Proximidad en cruce",
            "Luz      : 700 / 1023  (ADC raw 0)  LDR=OK",
            "Clima    : 24.0 C   humedad 60.0 %   DHT=OK",
            "Distancia: 18.0 cm   US=OK",
            "C1 VENT+PASO     : off",
            "C2 PROXIMIDAD    : ON",
            "C3 ALERTA COMB.  : off",
            "Actuadores: R=1 G=0 B=0  Buzzer=1  blink=0",
            "Estado   : PROX ALARMA",
            "LCD:  T24.0 H60 L700   |   D018 PROX ALARMA",
        ],
        "#B42318",
    )
    s3 = make_serial_png(
        "escenario3_serial.png",
        "Escenario 3 — Ola de calor seca (Serial 3)",
        [
            "Modo     : S3 Ola de calor seca",
            "Luz      : 650 / 1023  (ADC raw 0)  LDR=OK",
            "Clima    : 37.2 C   humedad 28.0 %   DHT=OK",
            "Distancia: 200.0 cm   US=OK",
            "C1 VENT+PASO     : off",
            "C2 PROXIMIDAD    : off",
            "C3 ALERTA COMB.  : ON",
            "Actuadores: R=1 G=1 B=1  Buzzer=1  blink=1",
            "Estado   : ALERTA COMB.",
            "LCD:  T37.2 H28 L650   |   D200 ALERTA COMB.",
        ],
        "#C97800",
    )
    return {"s1": s1, "s2": s2, "s3": s3}


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decor(page_count)
            super().showPage()
        super().save()

    def _draw_page_decor(self, page_count):
        page = self._pageNumber
        self.setFillColor(NAVY)
        self.rect(0, A4[1] - 16, A4[0], 16, fill=1, stroke=0)
        self.rect(0, 0, A4[0], 22, fill=1, stroke=0)
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 8)
        self.drawString(18 * mm, A4[1] - 11, "Actividad 4  ·  Nodo urbano IoT  ·  ESP32 / Wokwi / PlatformIO")
        self.drawRightString(A4[0] - 18 * mm, 8, f"Pagina {page} / {page_count}")


def styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="CoverTitle", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8))
    ss.add(ParagraphStyle(name="CoverSub", fontName="Helvetica", fontSize=12, leading=16, textColor=TEAL, spaceAfter=6))
    ss.add(ParagraphStyle(name="H1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=8))
    ss.add(ParagraphStyle(name="H2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=4))
    ss.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_JUSTIFY, textColor=colors.HexColor("#1E293B"), spaceAfter=6))
    ss.add(ParagraphStyle(name="Small", fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569"), alignment=TA_LEFT))
    ss.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#1E293B")))
    ss.add(ParagraphStyle(name="CellB", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=NAVY))
    ss.add(ParagraphStyle(name="Caption", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER, spaceBefore=3, spaceAfter=10))
    return ss


def p(text, style):
    return Paragraph(text, style)


def table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
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


def img(path: Path, width=17 * cm):
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        w, h = im.size
    height = width * h / w
    return Image(str(path), width=width, height=height)


def build_pdf(figures: dict[str, Path]) -> None:
    ss = styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=16 * mm,
        title="Informe tecnico — Nodo urbano IoT",
        author="IoT Labs",
    )
    story = []
    c = ss["Cell"]
    cb = ss["CellB"]

    story.append(p("Informe técnico", ss["CoverSub"]))
    story.append(p("Nodo urbano embebido: sensores ambientales, lógica segura y actuación automatizada", ss["CoverTitle"]))
    story.append(p("Plataforma de simulación Wokwi · Microcontrolador ESP32 · Firmware PlatformIO (Arduino)", ss["CoverSub"]))
    story.append(p("Actividad 4 — Internet of Things · Repositorio IoT-Labs", ss["Small"]))
    story.append(Spacer(1, 8))

    story.append(p("1. Objetivo y alcance", ss["H1"]))
    story.append(p(
        "Se diseñó un sistema embebido que interpreta condiciones ambientales simuladas "
        "(luz, temperatura, humedad y distancia) y activa respuestas urbanas automáticas "
        "con visualización en LCD 16x2 y monitor serial. El diseño sigue el flujo "
        "<b>entrada → procesamiento → salida</b>, con umbrales centralizados, histéresis, "
        "validación de lecturas y separación en módulos para poder escalar a más cruces o sensores.",
        ss["Body"],
    ))
    story.append(p(
        "El firmware se desarrolla y compila con <b>PlatformIO</b> (`pio run`). La simulación "
        "usa Wokwi (extensión de VS Code/Cursor o wokwi.com) sobre el `diagram.json` del repositorio. "
        "Tras guardar el proyecto en Wokwi se obtiene el enlace público `https://wokwi.com/projects/…`.",
        ss["Body"],
    ))

    story.append(p("2. Diagrama técnico del sistema", ss["H1"]))
    story.append(img(figures["arch"]))
    story.append(p("Figura 1. Arquitectura lógica: sensores, motor de reglas en el ESP32 y actuadores/displays.", ss["Caption"]))
    story.append(img(figures["circ"], width=16.5 * cm))
    story.append(p("Figura 2. Bloques del circuito en Wokwi y mapa GPIO. Resistencias de 220 Ω en cada LED.", ss["Caption"]))

    story.append(p("Mapa de conexiones", ss["H2"]))
    story.append(
        table(
            [
                [p("<b>Señal</b>", cb), p("<b>Componente</b>", cb), p("<b>GPIO / alimentación</b>", cb), p("<b>Motivo de diseño</b>", cb)],
                [p("Datos DHT22", c), p("DHT22", c), p("GPIO4 · 3,3 V", c), p("Pin digital bidireccional; biblioteca DHTesp (Wokwi/ESP32).", c)],
                [p("AO LDR", c), p("Módulo fotorresistencia", c), p("GPIO34 · 3,3 V", c), p("ADC1, solo entrada: no se usa como salida.", c)],
                [p("TRIG / ECHO", c), p("HC-SR04", c), p("GPIO5 / GPIO18 · 5 V", c), p("El módulo clásico requiere 5 V. ECHO a 5 V en hardware real va con divisor 1 kΩ/2 kΩ.", c)],
                [p("Semaforo", c), p("LED rojo + 220 Ω", c), p("GPIO25", c), p("Limitación de corriente; color de detención.", c)],
                [p("Paso peatonal", c), p("LED verde + 220 Ω", c), p("GPIO26", c), p("Señal de cruce habilitado.", c)],
                [p("Ventilación", c), p("LED azul + 220 Ω", c), p("GPIO27", c), p("Actuador climático (en campo sería un relé/ventilador).", c)],
                [p("Alarma", c), p("Buzzer piezo", c), p("GPIO14", c), p("Tono 2 kHz; intermitente solo en C3.", c)],
                [p("Visualización", c), p("LCD 1602 I2C", c), p("SDA 21 · SCL 22 · 0x27", c), p("Bus I2C nativo; libera GPIO frente a LCD paralelo.", c)],
            ],
            [3.2 * cm, 3.6 * cm, 4.2 * cm, 6.0 * cm],
        )
    )

    story.append(p("3. Lógica de control implementada", ss["H1"]))
    story.append(p(
        "El lazo principal es cooperativo (`millis`): cada 200 ms se leen LDR y ultrasónico y se evalúan las reglas; "
        "el DHT22 se refresca cada 2 s (límite del sensor); LCD y Serial cada 400 ms; el patrón de parpadeo cada 250 ms. "
        "No hay `delay()` en el loop, salvo los 10 µs del pulso TRIG. Así la alarma de proximidad no espera al DHT.",
        ss["Body"],
    ))
    story.append(img(figures["flow"]))
    story.append(p("Figura 3. Flujo de decisión. Las tres reglas se evalúan en cada ciclo; la prioridad solo cambia el patrón (continuo vs intermitente).", ss["Caption"]))
    story.append(p(
        "La intensidad de luz se expresa en 0–1023 (<b>mayor valor = más luz</b>). El módulo LDR de Wokwi "
        "aumenta el voltaje en oscuridad; `sensors.cpp` invierte el ADC de 12 bit para que el umbral "
        "«intensidad &lt; 300» signifique anochecer o zona mal iluminada, no mediodía.",
        ss["Body"],
    ))
    story.append(p(
        "<b>Fail-safe.</b> Si el DHT22 falla, C1 y C3 se inhiben (no se ventila ni se declara emergencia climática con datos inventados). "
        "Si el ultrasónico hace timeout, C2 se inhibe para no dejar una sirena permanente. "
        "La histéresis (luz +50, distancia +5 cm) evita chattering cuando la magnitud oscila en el umbral.",
        ss["Body"],
    ))

    story.append(p("4. Tabla de condiciones y respuestas", ss["H1"]))
    story.append(
        table(
            [
                [p("<b>ID</b>", cb), p("<b>Condición</b>", cb), p("<b>Respuesta</b>", cb), p("<b>Prioridad / notas</b>", cb)],
                [p("C1", c), p("Luz &lt; 300 <b>y</b> T &gt; 30 °C", c), p("LED azul (ventilación) + LED verde (paso peatonal). Estado <b>VENT+PASO</b>.", c), p("Confort y movilidad nocturna. Requiere LDR y DHT válidos.", c)],
                [p("C2", c), p("Distancia &lt; 30 cm", c), p("LED rojo (semáforo) + buzzer continuo. Estado <b>PROX ALARMA</b>.", c), p("Seguridad inmediata. Sale a 35 cm (histéresis). Domina el patrón si coincide con C3.", c)],
                [p("C3", c), p("T &gt; 35 °C <b>y</b> H &lt; 40 %", c), p("Los tres LED + buzzer en patrón intermitente. Estado <b>ALERTA COMB.</b>", c), p("Emergencia climática (calor seco). Si hay C2, rojo y tono pasan a continuo.", c)],
                [p("—", c), p("Ninguna / sensores OK", c), p("Actuadores apagados. Estado <b>OK NORMAL</b>.", c), p("Estado seguro por defecto.", c)],
                [p("F", c), p("Lectura fuera de rango o timeout", c), p("Regla asociada OFF. Serial/LCD: DHT FAULT o US FAULT.", c), p("No se actúa sobre datos no confiables.", c)],
            ],
            [1.4 * cm, 4.4 * cm, 5.6 * cm, 5.6 * cm],
        )
    )

    story.append(p("5. Requisitos funcionales y no funcionales", ss["H1"]))
    story.append(p("Se dedujeron a partir del enunciado (sensores, reglas, visualización, Wokwi/ESP32) y de principios de diseño seguro y escalable.", ss["Body"]))
    story.append(p("5.1 Funcionales", ss["H2"]))
    story.append(
        table(
            [
                [p("<b>ID</b>", cb), p("<b>Requisito</b>", cb)],
                [p("RF-01", c), p("Muestrear periódicamente LDR, DHT22 y HC-SR04.", c)],
                [p("RF-02", c), p("Activar ventilación y paso peatonal si luz &lt; 300 y T &gt; 30 °C.", c)],
                [p("RF-03", c), p("Activar semáforo rojo y alarma si distancia &lt; 30 cm.", c)],
                [p("RF-04", c), p("Activar alerta combinada si T &gt; 35 °C y H &lt; 40 %.", c)],
                [p("RF-05", c), p("Mostrar valores y estado en LCD 16x2 y en el monitor serial.", c)],
                [p("RF-06", c), p("Inhibir la regla cuyo sensor esté inválido (fail-safe).", c)],
                [p("RF-07", c), p("Permitir validar tres escenarios urbanos (Serial 1/2/3 o sliders Wokwi).", c)],
            ],
            [2.2 * cm, 14.8 * cm],
        )
    )
    story.append(Spacer(1, 6))
    story.append(p("5.2 No funcionales", ss["H2"]))
    story.append(
        table(
            [
                [p("<b>ID</b>", cb), p("<b>Tipo</b>", cb), p("<b>Requisito</b>", cb)],
                [p("RNF-01", c), p("Latencia", c), p("Control ≤ 250 ms para luz y proximidad; DHT cada 2 s.", c)],
                [p("RNF-02", c), p("Escalabilidad", c), p("Pines y umbrales solo en config.h; módulos con una responsabilidad.", c)],
                [p("RNF-03", c), p("Robustez", c), p("Histéresis de luz (+50) y distancia (+5 cm).", c)],
                [p("RNF-04", c), p("Seguridad eléctrica", c), p("220 Ω en LED; 5 V solo en HC-SR04/LCD; ECHO con divisor en hardware real.", c)],
                [p("RNF-05", c), p("Mantenibilidad", c), p("Código comentado en sensores, control, actuadores y display.", c)],
                [p("RNF-06", c), p("Observabilidad", c), p("Serial 115200 con flags C1/C2/C3 y salud de sensores.", c)],
                [p("RNF-07", c), p("Portabilidad", c), p("PlatformIO env esp32dev + Wokwi (wokwi.toml + diagram.json).", c)],
                [p("RNF-08", c), p("Disponibilidad", c), p("Timeout 30 ms en pulseIn; loop no bloqueante.", c)],
            ],
            [2.2 * cm, 3.3 * cm, 11.5 * cm],
        )
    )

    story.append(p("6. Historias de usuario y criterios de aceptación", ss["H1"]))
    story.append(p("<b>HU-01 — Ventilación y paso en anochecer caluroso.</b> Como operador de movilidad y confort urbano, quiero que el nodo encienda ventilación y habilite el paso cuando oscurece y hace calor, para reducir el estrés térmico y señalar que se puede cruzar.", ss["Body"]))
    story.append(p(
        "<b>Criterios:</b> (1) Luz 180 y T 32,5 °C ⇒ LED azul y verde ON, estado VENT+PASO. "
        "(2) Luz 500 o T 28 °C ⇒ C1 off. (3) DHT en fallo ⇒ C1 inhibida. "
        "(4) Oscilación 290–320 no debe hacer parpadear C1 (histéresis).",
        ss["Body"],
    ))
    story.append(p("<b>HU-02 — Semáforo y alarma por proximidad.</b> Como peatón o conductor, quiero semáforo rojo y alarma si un objeto está a menos de 30 cm, para detener el avance y reducir atropellos o colisiones.", ss["Body"]))
    story.append(p(
        "<b>Criterios:</b> (1) D = 18 cm ⇒ rojo + buzzer, PROX ALARMA. (2) D = 40 cm ⇒ C2 off. "
        "(3) Si C2 está activa, D = 32 cm aún mantiene alarma; a 36 cm se apaga. "
        "(4) Timeout US ⇒ C2 off y US FAULT (sin sirena indefinida). "
        "(5) C2+C3 ⇒ rojo y tono continuos (prioridad de seguridad).",
        ss["Body"],
    ))
    story.append(p("<b>HU-03 — Alerta combinada por ola de calor seca.</b> Como gestor de emergencias urbanas, quiero una alerta visible y audible si hay calor extremo y aire seco, para señalar riesgo de estrés térmico o incendio de vegetación/residuos.", ss["Body"]))
    story.append(p(
        "<b>Criterios:</b> (1) T 37,2 °C y H 28 % ⇒ tres LED + buzzer intermitentes, ALERTA COMB. "
        "(2) T 34 °C o H 45 % ⇒ C3 off. (3) DHT en fallo ⇒ C3 inhibida. "
        "(4) LCD y Serial muestran valores y C3 = ON.",
        ss["Body"],
    ))
    story.append(
        table(
            [
                [p("<b>Historia</b>", cb), p("<b>RF</b>", cb), p("<b>Prueba</b>", cb)],
                [p("HU-01", c), p("RF-02, RF-05, RF-06, RF-07", c), p("Serial 1 / sliders anochecer", c)],
                [p("HU-02", c), p("RF-03, RF-05, RF-06, RF-07", c), p("Serial 2 / distancia &lt; 30 cm", c)],
                [p("HU-03", c), p("RF-04, RF-05, RF-06, RF-07", c), p("Serial 3 / calor seco", c)],
            ],
            [3.5 * cm, 7.5 * cm, 6.0 * cm],
        )
    )

    story.append(p("7. Validación: tres escenarios urbanos", ss["H1"]))
    story.append(p(
        "Los escenarios se pueden forzar enviando <b>1</b>, <b>2</b> o <b>3</b> por el monitor serial "
        "(útil para capturas repetibles) o ajustando los sliders de Wokwi en modo <b>0</b> (live).",
        ss["Body"],
    ))
    story.append(
        table(
            [
                [p("<b>Escenario</b>", cb), p("<b>Contexto urbano</b>", cb), p("<b>Valores</b>", cb), p("<b>Esperado</b>", cb)],
                [p("S1 · tecla 1", c), p("Cruce al anochecer en ola de calor: poca luz, T alta, peatones, sin obstáculo cercano.", c), p("L=180 · T=32,5 °C · H=55 % · D=150 cm", c), p("C1 ON. Azul+verde. Sin alarma.", c)],
                [p("S2 · tecla 2", c), p("Vehículo o peatón en la zona de detención del sensor de cruce (&lt; 30 cm).", c), p("L=700 · T=24 °C · H=60 % · D=18 cm", c), p("C2 ON. Rojo + buzzer continuo.", c)],
                [p("S3 · tecla 3", c), p("Ola de calor seca: riesgo de estrés térmico e incendio de residuos/vegetación.", c), p("L=650 · T=37,2 °C · H=28 % · D=200 cm", c), p("C3 ON. Tres LED + buzzer intermitentes.", c)],
            ],
            [3.0 * cm, 5.2 * cm, 4.6 * cm, 4.2 * cm],
        )
    )
    story.append(Spacer(1, 8))
    story.append(img(figures["s1"], width=16 * cm))
    story.append(p("Figura 4. Resultado del escenario 1 (valores y actuadores esperados en Serial/LCD).", ss["Caption"]))
    story.append(img(figures["s2"], width=16 * cm))
    story.append(p("Figura 5. Resultado del escenario 2.", ss["Caption"]))
    story.append(img(figures["s3"], width=16 * cm))
    story.append(p("Figura 6. Resultado del escenario 3.", ss["Caption"]))
    story.append(p(
        "En Wokwi, modo live: DHT22 (T/H), fotorresistencia (lux) y HC-SR04 (distancia) tienen sliders al hacer clic. "
        "Para C1 baje el lux y suba T por encima de 30 °C; para C2 acerque el ultrasónico a menos de 30 cm; "
        "para C3 suba T por encima de 35 °C y baje la humedad por debajo de 40 %.",
        ss["Body"],
    ))

    story.append(p("8. Consideraciones de seguridad física", ss["H1"]))
    story.append(p(
        "Aunque la práctica es simulada, el diseño se documenta para un despliegue en poste o isleta. "
        "La seguridad física cubre a las personas, al hardware y a la integridad del nodo.",
        ss["Body"],
    ))
    bullets = [
        "<b>Niveles lógicos.</b> El ESP32 no es tolerante a 5 V en GPIO. El HC-SR04 clásico alimentado a 5 V exige un divisor (1 kΩ serie + 2 kΩ a GND) en ECHO. En Wokwi el eco se conecta directo porque el simulador no inyecta 5 V reales.",
        "<b>Limitación de corriente.</b> Cada LED lleva 220 Ω. Un GPIO del ESP32 no debe superar ~12 mA de diseño (máx. absoluto ~40 mA). Un ventilador o semáforo real se conmuta con MOSFET/relé, no con el LED de protoboard.",
        "<b>Alimentación.</b> 3,3 V para lógica y DHT/LDR; 5 V solo para ultrasónico y LCD. Tierra común. Fusible o limiter en el 5 V del poste.",
        "<b>Ubicación.</b> El HC-SR04 a ~80–100 cm del suelo mira la zona de detención, no el tráfico a 50 km/h (evitar falsos positivos). El DHT22 a la sombra, lejos del asfalto y del propio LED/buzzer. El LDR sin farola directa encima.",
        "<b>Gabinete.</b> IP54 o superior, prensaestopas, drenaje inferior. El buzzer no debe superar niveles que dañen oído a 1 m en acera escolar; en campo se usa un tono acotado o un beacon luminoso.",
        "<b>Antimanipulación.</b> Tornillos de seguridad, sensor de apertura (futuro) que lleve el nodo a estado seguro (rojo intermitente, sin verde de paso). No exponer pines de boot (GPIO0) en un conector público.",
        "<b>Fail-safe de actuación.</b> Ante DHT o US inválido no se habilita el paso ni la emergencia climática con datos viejos indefinidos. El verde de peatón no debe quedar ON si el nodo se resetea a mitad de ciclo (setup apaga salidas).",
        "<b>Ciber-físico (escala siguiente).</b> Si más adelante se añade Wi-Fi/MQTT, el comando remoto de un actuador de vía pública requiere autenticación e integridad; este laboratorio no abre sockets, de modo que la superficie remota es nula.",
    ]
    story.append(
        ListFlowable(
            [ListItem(p(b, ss["Body"]), leftIndent=8) for b in bullets],
            bulletType="bullet",
            start="•",
        )
    )

    story.append(p("9. Estructura del firmware (PlatformIO)", ss["H1"]))
    story.append(p(
        "El proyecto se compila con `platform = espressif32@6.9.0`, `board = esp32dev` y framework Arduino. "
        "Dependencias: <i>DHT sensor library for ESPx</i> (recomendada por Wokwi en ESP32) y <i>LiquidCrystal_I2C</i>. "
        "Desde la raíz del repo: `pio run`. Simulación: generar `firmware.bin` y <b>Wokwi: Start Simulator</b>.",
        ss["Body"],
    ))
    story.append(
        table(
            [
                [p("<b>Módulo</b>", cb), p("<b>Responsabilidad</b>", cb)],
                [p("config.h", c), p("Pines, umbrales, histéresis, timeouts. Único lugar para reconfigurar un cruce distinto.", c)],
                [p("sensors.cpp", c), p("ADC invertido del LDR, pulso HC-SR04 con timeout, DHT cada 2 s, validación de rango, escenarios de demo.", c)],
                [p("control.cpp", c), p("C1/C2/C3, histéresis, fail-safe e mapeo a LED/buzzer/parpadeo.", c)],
                [p("actuators.cpp", c), p("GPIO de LED y tone()/noTone() del buzzer.", c)],
                [p("display.cpp", c), p("LCD 16x2 (valores + etiqueta) y volcado Serial de diagnóstico.", c)],
                [p("main.cpp", c), p("Orquestación por millis y comandos 0/1/2/3.", c)],
            ],
            [3.5 * cm, 13.5 * cm],
        )
    )

    story.append(p("10. Reflexión sobre aplicaciones reales", ss["H1"]))
    story.append(p(
        "El laboratorio resume, a escala de protoboard, tres familias de sistemas que ya existen en ciudad: "
        "<b>mobiliario climático</b> (ventiladores o nebulizadores en paradas), "
        "<b>pasos peatonales inteligentes</b> (verde peatonal + rojo vehicular según presencia) y "
        "<b>alertas de calor extremo</b> (AEMET/servicios municipales cuando T es alta y el aire es seco). "
        "La distancia corta (30 cm) en el enunciado no modela un carril entero: es más bien un sensor de "
        "«zona de detención» o de obstáculo en isleta. En calle se usarían radares, cámaras o lazos, "
        "pero la lógica (umbral → semáforo + alarma) es la misma.",
        ss["Body"],
    ))
    story.append(p(
        "Un despliegue real exigiría más capas que este nodo: redundancia de sensores (dos DHT o un SHT + un backup), "
        "reloj y registro local si cae la red, supervisión (watchdog ya disponible en ESP32), "
        "y una política de privacidad si se añade visión. También cambiaría el actuador azul: no un LED, "
        "sino un contactor con enclavamiento térmico. El valor de esta práctica es fijar el contrato "
        "entrada-regla-salida y las reglas de seguridad (no actuar con datos malos, no mezclar 5 V en un pin de 3,3 V, "
        "no bloquear el loop cuando hay una alarma de proximidad).",
        ss["Body"],
    ))
    story.append(p(
        "La escalabilidad se pensó como <b>configuración, no copia</b>: otro cruce clona el firmware, "
        "cambia umbrales en `config.h` (luz urbana vs parque) y, si crece la flota, el siguiente paso natural "
        "es un topic MQTT por nodo. Ese paso no se implementó a propósito: primero un control local determinista "
        "y observable, después la nube.",
        ss["Body"],
    ))

    story.append(p("11. Cómo reproducir el laboratorio", ss["H1"]))
    story.append(p(
        "1. Instalar PlatformIO y la extensión Wokwi. 2. En la raíz de IoT-Labs: <b>pio run</b>. "
        "3. Paleta de comandos → Wokwi: Start Simulator (requiere `diagram.json` y `wokwi.toml`). "
        "4. Monitor serial 115200: teclas 1, 2 y 3. 5. Guardar en wokwi.com para el enlace de entrega. "
        "El código fuente está en <b>Activity-4/</b>; el informe en <b>Activity-4/docs/</b>.",
        ss["Body"],
    ))

    story.append(p("12. Conclusión", ss["H1"]))
    story.append(p(
        "El nodo cumple las tres reglas del enunciado, visualiza datos y estado, y está estructurado "
        "para crecer sin reescribir el loop. Las decisiones de seguridad (divisor de ECHO en campo, "
        "fail-safe, histéresis, GPIO correctos) y las tres historias de usuario cubren confort, "
        "proximidad y emergencia climática —el núcleo de un cruce urbano mínimo pero defendible.",
        ss["Body"],
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF: {PDF_PATH}")


def main() -> None:
    ensure_dirs()
    arch = make_architecture_png()
    flow = make_flow_png()
    circ = make_circuit_png()
    serials = build_serial_figures()
    figures = {"arch": arch, "flow": flow, "circ": circ, **serials}
    build_pdf(figures)


if __name__ == "__main__":
    main()
