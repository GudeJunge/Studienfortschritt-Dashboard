"""Layout und Komponenten für das Studienfortschritt-Dashboard."""

import math
import os
import sys
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QFrame,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from metrics import DashboardMetrics, create_metrics_for_studiengang
from study_service import StudienService

Margins = tuple[int, int, int, int]


@dataclass(frozen=True)
class UIConfig:
    """
    Hält zentrale Konfigurationswerte für Layout und Styling des Dashboards.

    Die Klasse ist eine Hilfsklasse der Präsentationsschicht und wird von
    Layout-Komponenten wie `DashboardLayout`, `RoundedBox` oder den
    Section-Widgets verwendet, um Maße, Abstände und Farben konsistent zu
    halten. Sie interagiert ausschließlich mit UI-Klassen derselben
    Schicht und kennt keine Anwendungs- oder Domänendaten.
    """

    # Anwendungsgröße
    base_width: int = 1820
    base_height: int = 920

    # Layoutabstände
    main_margins: Margins = (24, 24, 24, 24)
    row_spacing: int = 24
    kpi_spacing: int = 40
    diagram_spacing: int = 40
    progress_spacing: int = 0
    progress_max_h: int = 90
    kpi_max_h: int = 240
    kpi_title_fs: int = 16
    diagram_min_h: int = 440
    notenverlauf_width: int = 8
    notenverlauf_height: int = 4
    zeitaufwand_width: int = 8
    zeitaufwand_height: int = 4
    box_margin: int = 0
    box_padding: int = 0
    box_radius: int = 12
    title_top_gap: int = 12

    # Farben
    color_bg: str = "#0f1720"
    color_box: str = "#30363a"
    color_text: str = "#ffffff"
    color_text_muted: str = "#9AAABB"
    color_ok: str = "#4CAF50"
    color_warn: str = "#F44336"
    color_info: str = "#2196F3"


CFG = UIConfig()


def _error_label(text: str = "Fehler: Keine Daten verfügbar") -> QLabel:
    """Erzeugt ein zentriertes Fehlermeldungslabel."""

    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("color: #FF6B6B; font-weight: bold; font-size: 14px;")
    return label


def embed_matplotlib_chart(
    box: "RoundedBox",
    chart_canvas: FigureCanvas,
    height: Optional[int] = None,
) -> None:
    """Fügt ein Matplotlib-Canvas in eine Box ein."""

    try:
        chart_canvas.setStyleSheet("background: transparent;")
        chart_canvas.setAttribute(Qt.WA_TranslucentBackground, True)
    except Exception:
        pass

    if height is not None:
        try:
            chart_canvas.setFixedHeight(int(height))
            chart_canvas.setMaximumHeight(int(height))
            chart_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass

    try:
        box.content_area.addWidget(chart_canvas, 0, Qt.AlignCenter)
    except TypeError:
        box.content_area.addWidget(chart_canvas)


class RoundedBox(QFrame):
    """
    Wiederverwendbarer Container mit abgerundeten Ecken und optionalem Titel.

    Diese Hilfsklasse der Präsentationsschicht dient als Baustein für das
    Dashboard-Layout und wird von `ProgressSection`, `KPISection` und
    `DiagramSection` genutzt, um Inhalte optisch einheitlich zu
    gruppieren. Sie interagiert nur mit Qt-Widgets und erhält ihre
    Inhalte von den jeweiligen Section-Klassen, die wiederum vom
    `DashboardLayout` im Kontext des `UIService` verwendet werden.
    """

    def __init__(self, title: str = "", min_height: int = 150, full_width: bool = False) -> None:
        super().__init__()
        self.full_width = full_width
        self._init_style(min_height)
        self._init_layout(title)

    def _init_layout(self, title: str) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignTop)

        if title:
            if CFG.title_top_gap > 0:
                outer.addSpacing(CFG.title_top_gap)
            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", CFG.kpi_title_fs, QFont.Bold))
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet(f"color: {CFG.color_text}; margin-bottom: 0px;")
            outer.addWidget(title_label, 0, Qt.AlignTop)

        if self.full_width:
            self.content_area = QVBoxLayout()
            self.content_area.setContentsMargins(0, 0, 0, 0)
            self.content_area.setSpacing(0)
            self.content_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            outer.addLayout(self.content_area, 1)
            self.setLayout(outer)
            return

        self._center_container = QWidget()
        cc_layout = QVBoxLayout()
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.setSpacing(0)
        cc_layout.addStretch()

        self.content_area = QVBoxLayout()
        self.content_area.setContentsMargins(0, 0, 0, 0)
        self.content_area.setSpacing(0)
        self.content_area.setAlignment(Qt.AlignHCenter)

        holder = QWidget()
        holder.setLayout(self.content_area)
        cc_layout.addWidget(holder, 0, Qt.AlignHCenter)
        cc_layout.addStretch()
        self._center_container.setLayout(cc_layout)
        outer.addWidget(self._center_container, 1)

        self.setLayout(outer)

    def _init_style(self, min_height: int) -> None:
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CFG.color_box};
                border: none;
                border-radius: {CFG.box_radius}px;
                padding: {CFG.box_padding}px;
                margin: {CFG.box_margin}px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
                color: {CFG.color_text};
            }}
            """
        )
        self.setMinimumHeight(min_height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)


class EctsProgressBarWidget(QWidget):
    """
    Benutzerdefinierte Fortschrittsanzeige für den ECTS-Stand eines Studiengangs.

    Das Widget gehört zur Präsentationsschicht und ist eine Hilfsklasse,
    die von `ProgressSection` verwendet wird, um die vom `DashboardMetrics`
    bereitgestellten Fortschrittsdaten visuell darzustellen. Es kennt
    selbst keine Anwendungslogik, sondern arbeitet ausschließlich mit
    bereits berechneten numerischen Werten.
    """

    def __init__(self, ist_ects: int, gesamt_ects: int, soll_ects: int, parent=None) -> None:
        super().__init__(parent)
        self.ist_ects = max(0, ist_ects)
        self.gesamt_ects = gesamt_ects if gesamt_ects > 0 else 180
        self.soll_ects = max(0, min(soll_ects, self.gesamt_ects))
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding_x = 8
        draw_w = w - 2 * padding_x

        bg_color = QColor("#202428")
        progress_color = QColor(CFG.color_ok)
        text_color = QColor(CFG.color_text)
        marker_color = QColor("#555555")
        bar_height = 12
        bar_y = h - bar_height - 10

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(
            padding_x,
            bar_y,
            draw_w,
            bar_height,
            bar_height / 2,
            bar_height / 2,
        )

        progress_width = int((self.ist_ects / self.gesamt_ects) * draw_w)
        if progress_width > 0:
            painter.setBrush(QBrush(progress_color))
            draw_width = min(progress_width, draw_w)
            painter.drawRoundedRect(
                padding_x,
                bar_y,
                draw_width,
                bar_height,
                bar_height / 2,
                bar_height / 2,
            )

        if self.soll_ects > 0:
            soll_x = padding_x + int((self.soll_ects / self.gesamt_ects) * draw_w)
            soll_x = max(padding_x, min(soll_x, padding_x + draw_w))
            soll_pen = QPen(QColor("#E2E8F0"), 2, Qt.CustomDashLine)
            soll_pen.setDashPattern([2, 4])
            painter.setPen(soll_pen)
            painter.drawLine(soll_x, bar_y - 6, soll_x, bar_y + bar_height + 6)
            painter.setPen(QColor("#E2E8F0"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(QRectF(soll_x - 24, bar_y - 42, 48, 18), Qt.AlignCenter, "Soll")

        font = QFont("Arial", 10)
        painter.setFont(font)

        def draw_marker(value: int, label_text: str, align: Qt.AlignmentFlag = Qt.AlignCenter) -> None:
            x_pos = padding_x + int((value / self.gesamt_ects) * draw_w)
            x_pos = max(padding_x, min(x_pos, w - padding_x - 1))
            painter.setPen(QPen(marker_color, 1))
            painter.drawLine(x_pos, bar_y + bar_height + 2, x_pos, bar_y + bar_height + 6)
            painter.setPen(text_color)
            rect = QRectF(x_pos - 50, bar_y - 20, 100, 20)
            if align == Qt.AlignLeft:
                rect = QRectF(x_pos, bar_y - 20, 100, 20)
            elif align == Qt.AlignRight:
                rect = QRectF(x_pos - 100, bar_y - 20, 100, 20)

            painter.drawText(rect, align | Qt.AlignBottom, label_text)

        half_ects = self.gesamt_ects // 2
        draw_marker(half_ects, f"{half_ects}", Qt.AlignCenter)
        draw_marker(self.gesamt_ects, f"{self.gesamt_ects}", Qt.AlignRight)

        current_x = padding_x + int((self.ist_ects / self.gesamt_ects) * draw_w)
        current_x = max(padding_x, min(current_x, w - padding_x))
        painter.setPen(QColor(CFG.color_ok))
        font_bold = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font_bold)
        label = f"{self.ist_ects} ECTS"
        text_width = painter.fontMetrics().horizontalAdvance(label)

        text_x = max(padding_x, min(current_x - (text_width / 2), w - padding_x - text_width))
        painter.drawText(QRectF(text_x, bar_y - 25, text_width, 25), Qt.AlignCenter, label)


class GaugeWidget(QWidget):
    """
    Benutzerdefiniertes Tachometer-Widget zur Visualisierung des Notendurchschnitts.

    Diese Hilfsklasse der Präsentationsschicht wird innerhalb der
    `KPISection` eingesetzt, um den vom `DashboardMetrics` gelieferten
    Notendurchschnitt als Tachometer-Darstellung zu zeigen. Sie arbeitet
    ausschließlich mit einem numerischen Wert und interagiert nicht mit
    Anwendungs- oder Infrastrukturschicht.
    """

    def __init__(self, value: float, parent=None) -> None:
        super().__init__(parent)
        self.value = value
        self.setMinimumSize(280, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        center_x = w / 2
        center_y = h - 20
        radius = min(w / 2 - 50, h - 40)

        def get_angle(note: float) -> float:
            note = max(1.0, min(note, 4.0))
            ratio = (note - 1.0) / 3.0
            return 180 * (1.0 - ratio)

        painter.setPen(QPen(QColor("#444444"), 15, Qt.SolidLine, Qt.FlatCap))
        path_bg = QPainterPath()
        path_bg.arcMoveTo(center_x - radius, center_y - radius, 2 * radius, 2 * radius, 180)
        path_bg.arcTo(center_x - radius, center_y - radius, 2 * radius, 2 * radius, 180, -180)
        painter.drawPath(path_bg)

        painter.setPen(QPen(QColor(CFG.color_ok), 15, Qt.SolidLine, Qt.FlatCap))
        path_goal = QPainterPath()
        angle_1_9 = get_angle(1.9)
        path_goal.arcMoveTo(
            center_x - radius,
            center_y - radius,
            2 * radius,
            2 * radius,
            angle_1_9,
        )
        path_goal.arcTo(
            center_x - radius,
            center_y - radius,
            2 * radius,
            2 * radius,
            angle_1_9,
            180 - angle_1_9,
        )
        painter.drawPath(path_goal)

        font = QFont("Arial", 10)
        painter.setFont(font)

        for note_tick in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            ang_deg = get_angle(note_tick)
            ang_rad = math.radians(ang_deg)
            p_text_x = center_x + (radius + 35) * math.cos(ang_rad)
            p_text_y = center_y - (radius + 35) * math.sin(ang_rad)
            painter.setPen(QColor(CFG.color_text_muted))
            rect = QRectF(p_text_x - 20, p_text_y - 10, 40, 20)
            painter.drawText(rect, Qt.AlignCenter, f"{note_tick:.1f}")

        val_ang_deg = get_angle(self.value)
        val_ang_rad = math.radians(val_ang_deg)
        pointer_len = radius - 10
        p_tip_x = center_x + pointer_len * math.cos(val_ang_rad)
        p_tip_y = center_y - pointer_len * math.sin(val_ang_rad)
        painter.setPen(QPen(QColor(CFG.color_text), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(center_x, center_y), QPointF(p_tip_x, p_tip_y))
        painter.setBrush(QBrush(QColor(CFG.color_text)))
        painter.drawEllipse(QPointF(center_x, center_y), 5, 5)
        font_val = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font_val)
        color_val = CFG.color_ok if self.value <= 1.9 else (CFG.color_warn if self.value > 2.5 else CFG.color_info)
        painter.setPen(QColor(color_val))
        painter.drawText(QRectF(center_x - 50, center_y - 50, 100, 40), Qt.AlignCenter, f"{self.value:.2f}")


class ProgressSection(QWidget):
    """
    UI-Abschnitt für die Fortschrittsanzeige auf Basis der ECTS.

    Die Klasse ist Teil der Präsentationsschicht und wird vom
    `DashboardLayout` verwendet, um den Studienfortschritt eines
    Studiengangs in Zeile 1 des Dashboards anzuzeigen. Sie nutzt das
    Hilfsobjekt `DashboardMetrics`, das vom `UIService` bereitgestellt
    wird, und rendert daraus eine `EctsProgressBarWidget`-Instanz.
    """

    def __init__(self, metrics: Optional[DashboardMetrics] = None) -> None:
        super().__init__()
        self.metrics = metrics
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(CFG.progress_spacing)

        progress_container = RoundedBox("Studienfortschritt", min_height=60, full_width=True)

        data = self._progress_data()
        widget = EctsProgressBarWidget(data["ist_ects"], data["gesamt_ects"], data.get("soll_ects", 0))
        progress_container.content_area.addWidget(widget)

        layout.addWidget(progress_container)
        self.setLayout(layout)

    def _progress_data(self) -> dict[str, float]:
        if not self.metrics:
            return {"ist_ects": 0, "soll_ects": 0, "gesamt_ects": 180}
        return self.metrics.get_progress_data()


class KPISection(QWidget):
    """
    UI-Abschnitt für die Anzeige der wichtigsten Kennzahlen (KPI-Reihe).

    Diese Klasse gehört zur Präsentationsschicht und bildet Zeile 2 des
    Dashboards ab. Sie erhält ein `DashboardMetrics`-Objekt vom
    `UIService` bzw. `DashboardLayout` und stellt daraus Notendurchschnitt,
    Prognose und Tage-pro-Modul-Richtwert in drei Boxen dar. Sie ist eine
    Hilfsklasse des Layouts und enthält keine eigene Geschäftslogik.
    """

    def __init__(self, metrics: Optional[DashboardMetrics] = None) -> None:
        super().__init__()
        self.metrics = metrics
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(CFG.kpi_spacing)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(CFG.kpi_max_h)

        layout.addWidget(self._build_notendurchschnitt_box())
        layout.addWidget(self._build_prognose_box())
        layout.addWidget(self._build_tage_pro_modul_box())

        self.setLayout(layout)

    def _build_notendurchschnitt_box(self) -> RoundedBox:
        box = RoundedBox("Notendurchschnitt", 100)
        box.setMaximumHeight(CFG.kpi_max_h - 40)

        if not self.metrics:
            box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)
            return box

        note_val = self.metrics.get_notendurchschnitt_kpi().get("note", 0)
        if note_val and note_val > 0:
            box.content_area.addWidget(GaugeWidget(note_val))
        else:
            box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)
        return box

    def _build_prognose_box(self) -> RoundedBox:
        box = RoundedBox("Prognose", 100, full_width=True)
        box.setMaximumHeight(CFG.kpi_max_h - 40)

        if not self.metrics:
            box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)
            return box

        prog_data = self.metrics.get_prognose_kpi()
        jahre = prog_data.get("regelstudienzeit_jahre", 4.0)
        jahre_str = f"{int(jahre)}" if float(jahre).is_integer() else f"{jahre:0.1f}"
        noten_ok = prog_data.get("noten_ziel_erreicht", False)
        zeit_ok = prog_data.get("zeit_ziel_erreicht", False)

        layout = box.content_area
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        line1 = self._rich_label(
            "Notendurchschnitt max. 1,9",
            "erreicht." if noten_ok else "nicht erreicht.",
            CFG.color_info,
            CFG.color_ok if noten_ok else CFG.color_warn,
        )
        line2 = self._rich_label(
            f"Regelstudienzeit {jahre_str} Jahre",
            "erreicht." if zeit_ok else "nicht erreicht.",
            CFG.color_info,
            CFG.color_ok if zeit_ok else CFG.color_warn,
        )

        layout.addStretch()
        layout.addWidget(line1)
        layout.addWidget(line2)
        layout.addStretch()
        return box

    def _build_tage_pro_modul_box(self) -> RoundedBox:
        box = RoundedBox("Tage pro Modul-Richtwert*", 100)
        box.setMaximumHeight(CFG.kpi_max_h - 40)

        if not self.metrics:
            box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)
            return box

        t_kpi = self.metrics.get_tage_pro_modul_kpi()
        value_label = QLabel(t_kpi["richtwert_text"])
        value_label.setFont(QFont("Arial", 42, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {CFG.color_text};")
        box.content_area.addWidget(value_label)
        return box

    @staticmethod
    def _rich_label(title: str, status_text: str, title_color: str, status_color: str) -> QLabel:
        html = (
            "<div style='font-family: Arial; font-size: 22px; color: {fg}; text-align: center;'>"
            "Das Ziel <span style='color: {title_color}; font-weight: bold;'>{title}</span> wird "
            "voraussichtlich <span style='color: {status_color}; font-weight: bold;'>{status}</span>"
            "</div>"
        ).format(
            fg=CFG.color_text,
            title=title,
            title_color=title_color,
            status=status_text,
            status_color=status_color,
        )
        label = QLabel(html)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        return label


class DiagramSection(QWidget):
    """
    UI-Abschnitt für die Diagramme zu Notenverlauf und Zeitaufwand.

    Die Klasse ist Teil der Präsentationsschicht und wird vom
    `DashboardLayout` als dritte Zeile des Dashboards verwendet. Sie nutzt
    das `DashboardMetrics`-Objekt, um den Verlauf des Notendurchschnitts
    und die Historie des Zeitaufwands pro Modul als Matplotlib-Diagramme
    darzustellen. Sie interagiert damit indirekt mit dem `StudienService`,
    der die zugrunde liegenden Dashboard-Daten liefert.
    """

    def __init__(self, metrics: Optional[DashboardMetrics] = None) -> None:
        super().__init__()
        self.metrics = metrics
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(CFG.diagram_spacing)

        notenverlauf_box = RoundedBox("Notendurchschnitt - Verlauf", max(CFG.diagram_min_h, 360))
        if self.metrics and self.metrics.has_notenverlauf():
            chart = self.metrics.create_notenverlauf_chart(
                width=CFG.notenverlauf_width,
                height=CFG.notenverlauf_height,
            )
            embed_matplotlib_chart(notenverlauf_box, chart)
        else:
            notenverlauf_box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)

        zeitaufwand_box = RoundedBox("Tage pro Modul - Historie", max(CFG.diagram_min_h, 360))
        has_completed = bool(self.metrics and self.metrics.has_zeitaufwand_history())
        if self.metrics and has_completed:
            chart = self.metrics.create_zeitaufwand_chart(
                width=CFG.zeitaufwand_width,
                height=CFG.zeitaufwand_height,
            )
            embed_matplotlib_chart(zeitaufwand_box, chart)
        else:
            zeitaufwand_box.content_area.addWidget(_error_label(), 0, Qt.AlignCenter)

        layout.addWidget(notenverlauf_box)
        layout.addWidget(zeitaufwand_box)

        self.setLayout(layout)


class DashboardLayout(QMainWindow):
    """
    Hauptfenster der grafischen Oberfläche mit dreizeiligem Dashboard-Layout.

    Die Klasse gehört zur Präsentationsschicht und strukturiert die UI in
    Fortschrittsanzeige, KPI-Reihe und Diagrammbereich. Sie wird durch
    die Funktion `create_dashboard_app` instanziiert, welche vom
    `UIService` genutzt wird. `DashboardLayout` arbeitet mit einem
    `DashboardMetrics`-Objekt, das aus dem `StudienService` stammt, kennt
    aber weder die Datenbank noch die Domänenschicht direkt.
    """

    def __init__(self, studiengang_name: str, metrics: Optional[DashboardMetrics] = None) -> None:
        super().__init__()
        self.studiengang_name = studiengang_name
        self.metrics = metrics
        self._init_window()
        self._build()

    def _init_window(self) -> None:
        """Initialisiert Fenstergröße und Stil."""
        self.setWindowTitle(f"Dashboard - {self.studiengang_name}")
        self.setFixedSize(CFG.base_width, CFG.base_height)
        self._center()
        self.setStyleSheet(
            f"""
            QMainWindow {{ background-color: {CFG.color_bg}; }}
            """
        )

    def _center(self) -> None:
        """Zentriert das Fenster auf dem aktiven Bildschirm."""
        screen = QApplication.primaryScreen().geometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())

    def _build(self) -> None:
        """Erzeugt das Hauptlayout und fügt die Bereiche ein."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        l, t, r, b = CFG.main_margins
        main_layout.setContentsMargins(l, t, r, b)
        main_layout.setSpacing(0)

        progress_section = ProgressSection(self.metrics)
        progress_section.setFixedHeight(CFG.progress_max_h)
        progress_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        kpi_section = KPISection(self.metrics)
        kpi_section.setFixedHeight(CFG.kpi_max_h)
        kpi_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        diagram_section = DiagramSection(self.metrics)
        diagram_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(progress_section)
        self._apply_row_gap(main_layout, CFG.row_spacing)
        main_layout.addWidget(kpi_section)
        self._apply_row_gap(main_layout, CFG.row_spacing)
        main_layout.addWidget(diagram_section)

        try:
            prog_kpi = self.metrics.get_prognose_kpi() if self.metrics else {}
            regelstudienzeit_jahre = prog_kpi.get("regelstudienzeit_jahre", 4.0)
            display_years = int(regelstudienzeit_jahre) if float(regelstudienzeit_jahre).is_integer() else regelstudienzeit_jahre
        except Exception:
            display_years = 4
        footer = QLabel(
            (
                "*Dieser Richtwert ermittelt sich anhand der verbleibenden Tage bis zum Erreichen der Regelstudienzeit "
                "und den verbleibenden ECTS zum Abschließen des Studiums. Der Richtwert gibt den durchschnittlichen "
                "Zeitaufwand an, welcher für ein Modul mit 5 ECTS maximal aufgewendet werden kann, um das Studium "
                f"innerhalb der Regelstudienzeit von {display_years} Jahren zu absolvieren. Dieser Richtwert ist nicht "
                "repräsentativ für Module wie die Bachelorarbeit (10 ECTS). Es wird ein Urlaub von 6 Wochen pro Jahr berücksichtigt."
            )
        )
        footer.setStyleSheet("color: #cbd5e1; font-size: 12px; padding-top: 6px;")
        footer.setWordWrap(True)
        main_layout.addWidget(footer)

        central_widget.setLayout(main_layout)
        self._set_fixed_diagram_height(diagram_section, footer)

    def _apply_row_gap(self, container_layout: QVBoxLayout, gap: int) -> None:
        """Erzeugt den vertikalen Abstand zwischen zwei Bereichen."""

        if gap > 0:
            container_layout.addSpacing(gap)

    def _set_fixed_diagram_height(self, diagram_section: QWidget, footer: QLabel) -> None:
        """Berechnet die Zielhöhe für den Diagrammbereich."""

        l, top_margin, r, bottom_margin = CFG.main_margins
        footer_height = footer.sizeHint().height()
        spacing_total = max(0, CFG.row_spacing) * 2
        available_inner = CFG.base_height - top_margin - bottom_margin
        remainder = available_inner - (
            CFG.progress_max_h + CFG.kpi_max_h + footer_height + spacing_total
        )
        target = max(CFG.diagram_min_h, remainder)
        diagram_section.setFixedHeight(target)


class UIService:
    """
    Stellt die grafische Benutzeroberfläche für das Dashboard bereit.

    Die Klasse gehört zur Präsentationsschicht und fungiert als Bindeglied
    zwischen `StudienService` und den Layout-Klassen des Dashboards. Sie
    ruft beim `StudienService` aggregierte `DashboardDaten` ab, wandelt
    diese mit Hilfe von `DashboardMetrics` in darstellbare Kennzahlen und
    Diagrammdaten um und öffnet anschließend über `create_dashboard_app`
    das `DashboardLayout`. UI-spezifische Fehler werden hier behandelt,
    fachliche Validierung verbleibt im `StudienService`.
    """

    def __init__(self, studien_service: StudienService) -> None:
        """Initialisiert den UIService mit einem StudienService."""

        self._studien_service = studien_service

    def zeige_dashboard(self, studiengang_id: int) -> bool:
        """
        Öffnet das Dashboard-Fenster für den angegebenen Studiengang.

        Gibt ``True`` zurück, wenn das Dashboard gestartet werden konnte,
        andernfalls ``False`` (z. B. wenn der Studiengang nicht existiert).
        """

        daten = self._studien_service.erzeuge_dashboard_daten(studiengang_id)
        metrics = create_metrics_for_studiengang(daten)
        if metrics is None:
            return False
        studiengang_name = daten.studiengang_name

        try:
            app, _ = create_dashboard_app(studiengang_name, metrics)
            print("Dashboard geöffnet. Fenster schließen zum Beenden.")
            app.exec()
            return True
        except ImportError as exc:
            print(f"FEHLER: GUI-Abhängigkeiten fehlen: {exc}")
            print("TIPP: pip install -r requirements.txt")
        except Exception as exc:
            print(f"FEHLER: {exc}")
        return False


def create_dashboard_app(
    studiengang_name: str,
    metrics: Optional[DashboardMetrics] = None,
) -> tuple[QApplication, DashboardLayout]:
    """Erzeugt Anwendung und Fenster für das Dashboard.

    Args:
        studiengang_name: Anzeigename des Studiengangs im Fenstertitel.
        metrics: KPI-Datenquelle; bei ``None`` startet das UI ohne Daten.

    Returns:
        Tuple aus aktiver QApplication und dem Dashboard-Fenster.
    """

    app = QApplication(sys.argv)
    app.setApplicationName("Studienfortschritt Dashboard")
    app.setApplicationVersion("1.0.0")

    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    app_icon: QIcon | None = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    dashboard = DashboardLayout(studiengang_name, metrics)
    if app_icon is not None:
        dashboard.setWindowIcon(app_icon)
    dashboard.show()

    return app, dashboard
