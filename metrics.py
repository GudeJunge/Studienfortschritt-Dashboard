"""Metriken und Visualisierungen für das Studiengang-Dashboard."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from study_service import DashboardDaten


class DashboardMetrics:
    """
    Berechnet Kennzahlen und erstellt Diagramme für das Dashboard.

    Die Klasse gehört zur Präsentationsschicht und ist eine Hilfsklasse
    des `UIService` bzw. `DashboardLayout`. Sie arbeitet ausschließlich
    auf einem vom `StudienService` bereitgestellten `DashboardDaten`-
    Objekt und erzeugt daraus KPI-Werte und Matplotlib-Diagramme. Sie
    kennt weder Datenbankzugriffe noch die Domänenschicht direkt.
    """

    _STYLE_INITIALIZED = False

    def __init__(self, daten: DashboardDaten) -> None:
        """Speichert das Dashboard-Datenpaket und stellt Matplotlib ein."""

        self._daten = daten
        self._ensure_matplotlib_style()

    @classmethod
    def _ensure_matplotlib_style(cls) -> None:
        """Initialisiert einmalig die Matplotlib-Konfiguration."""
        if cls._STYLE_INITIALIZED:
            return
        plt.style.use("default")
        plt.rcParams.update(
            {
                "font.size": 10,
                "font.family": "Arial",
                "axes.titlesize": 12,
                "axes.labelsize": 10,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "legend.fontsize": 9,
                "figure.titlesize": 14,
                "axes.grid": True,
                "grid.alpha": 0.3,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "text.color": "#FFFFFF",
                "axes.labelcolor": "#FFFFFF",
                "xtick.color": "#FFFFFF",
                "ytick.color": "#FFFFFF",
                "axes.edgecolor": "#777777",
                "figure.facecolor": "none",
            }
        )
        cls._STYLE_INITIALIZED = True

    def get_progress_data(self) -> dict[str, int]:
        """Berechnet die für die Fortschrittsanzeige benötigten Werte."""
        return {
            "ist_ects": self._daten.progress.ist_ects,
            "soll_ects": self._daten.progress.soll_ects,
            "gesamt_ects": self._daten.progress.gesamt_ects,
        }

    def get_notendurchschnitt_kpi(self) -> dict[str, float | None]:
        """Gibt den aktuellen Notendurchschnitt zurück."""
        return {"note": self._daten.notendurchschnitt}

    def get_tage_pro_modul_kpi(self) -> dict[str, str]:
        """Bereitet den Richtwert-Text für das Dashboard auf."""
        return {"richtwert_text": self._daten.tage_pro_modul_text}

    def get_prognose_kpi(self) -> dict[str, bool | float]:
        """Bewertet, ob die Noten- und Zeitziele voraussichtlich erreicht werden."""
        return {
            "noten_ziel_erreicht": self._daten.prognose.noten_ziel_erreicht,
            "zeit_ziel_erreicht": self._daten.prognose.zeit_ziel_erreicht,
            "regelstudienzeit_jahre": self._daten.prognose.regelstudienzeit_jahre,
        }

    def has_notenverlauf(self) -> bool:
        """Gibt zurück, ob Verlaufsdaten für den Notendurchschnitt vorliegen."""

        return bool(self._daten.notenverlauf)

    def has_zeitaufwand_history(self) -> bool:
        """Gibt zurück, ob eine Historie des Zeitaufwands pro Modul vorliegt."""

        return bool(self._daten.zeitaufwand_history)

    def create_notenverlauf_chart(self, width: int = 6, height: int = 4) -> FigureCanvas:
        """Erstellt die Verlaufsdarstellung des Notendurchschnitts."""
        fig = Figure(figsize=(width, height), dpi=100)
        fig.patch.set_facecolor("none")
        ax = fig.add_subplot(111)
        ax.set_facecolor("none")

        werte = self._daten.notenverlauf
        if not werte:
            self._draw_placeholder(ax)
            fig.tight_layout()
            return FigureCanvas(fig)

        x_positionen = range(1, len(werte) + 1)
        farbe = "#156082"
        ax.plot(
            list(x_positionen),
            werte,
            "o-",
            color=farbe,
            linewidth=2.0,
            markersize=5,
            markerfacecolor="#FFFFFF",
            markeredgewidth=1,
            markeredgecolor=farbe,
        )
        ax.axhspan(1.0, 1.9, alpha=0.2, color="#4CAF50", label="Zielbereich ≤ 1,9")
        ax.set_xlabel("Abgeschlossene Module")
        ax.set_ylabel("Notendurchschnitt")
        ax.set_ylim(1.0, 4.0)
        ax.set_xlim(0.5, len(werte) + 0.5)
        ax.set_xticks(list(x_positionen))
        ax.grid(True, color="#555555", linestyle="-", linewidth=0.5, alpha=0.3)
        ax.legend(loc="upper right", frameon=False)
        fig.tight_layout()
        return FigureCanvas(fig)

    def create_zeitaufwand_chart(self, width: int = 6, height: int = 4) -> FigureCanvas:
        """Zeigt den Zeitaufwand pro Modul als Balkendiagramm."""
        fig = Figure(figsize=(width, height), dpi=100)
        fig.patch.set_facecolor("none")
        ax = fig.add_subplot(111)
        ax.set_facecolor("none")

        namen = [name for name, _ in self._daten.zeitaufwand_history]
        tage = [tage for _, tage in self._daten.zeitaufwand_history]

        if not namen:
            self._draw_placeholder(ax)
            fig.tight_layout()
            return FigureCanvas(fig)
        namen = [self._format_module_label(name) for name in namen]
        positionen = np.arange(len(namen))

        ax.bar(positionen, tage, color="#156082", width=0.6, edgecolor="#156082")
        durchschnitt = float(np.mean(tage)) if tage else 0.0
        if tage:
            ax.axhline(
                durchschnitt,
                color="#FFFFFF",
                linestyle="--",
                linewidth=1.5,
                label="Durchschnittlicher Zeitaufwand",
            )

        ax.set_xlabel("Module")
        ax.set_ylabel("Benötigte Tage")
        ax.set_xticks(positionen)
        ax.set_xticklabels(namen, rotation=0, ha="center")

        if tage:
            max_tage = max(tage)
            y_top = max(7, ((int(max_tage) + 6) // 7) * 7)
            ax.set_ylim(0, y_top)
            ax.set_yticks(np.arange(0, y_top + 1, 7))

        ax.set_axisbelow(True)
        ax.yaxis.grid(True, alpha=0.3)
        ax.xaxis.grid(False)

        if ax.get_legend_handles_labels()[1]:
            ax.legend(loc="upper right", frameon=False)

        fig.tight_layout()
        return FigureCanvas(fig)

    @staticmethod
    def _draw_placeholder(ax: Axes, message: str = "Keine Daten verfügbar") -> None:
        ax.clear()
        ax.set_facecolor("none")
        ax.axis("off")
        ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, color="#FFFFFF", fontsize=12)

    @staticmethod
    def _format_module_label(name: str, max_length: int = 18) -> str:
        if len(name) <= max_length:
            return name
        return f"{name[: max_length - 3]}..."

def create_metrics_for_studiengang(daten: Optional[DashboardDaten]) -> Optional[DashboardMetrics]:
    """
    Erzeugt ein DashboardMetrics-Objekt aus einem Dashboard-Datenpaket.

    Diese Hilfsfunktion akzeptiert ein bereits vollständig aufgebautes
    DashboardDaten-Objekt aus der Anwendungsschicht.
    """

    if daten is None:
        return None
    return DashboardMetrics(daten)
