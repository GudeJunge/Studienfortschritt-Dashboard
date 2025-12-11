"""Initialisiert die Dashboard-Datenbank mit einem Beispielstudiengang."""

from datetime import date
from typing import List

from database_connector import DatenbankConnector


class DashboardSetup:
    """
    Hilfsklasse zum Anlegen eines Beispielstudiengangs und seiner Module.

    Die Klasse ist der Infrastrukturschicht zugeordnet und nutzt den
    `DatenbankConnector`, um ein vordefiniertes Dashboard-Setup zu
    erzeugen oder die Datenbank vollständig zurückzusetzen. Sie wird
    über das Modul `setup.py` von der CLI bzw. vom `CLIController`
    indirekt aufgerufen und enthält keine eigene Domänenlogik.
    """

    def __init__(self, db_path: str = "dashboard.db") -> None:
        """Öffnet eine Verbindung zur Dashboard-Datenbank."""

        self._db = DatenbankConnector(db_path)

    def create_default_studiengang(self) -> int:
        """Erstellt den KI-Studiengang sowie alle Module."""

        studiengang_id = self._db.create_studiengang(
            name="B.Sc. Angewandte Künstliche Intelligenz",
            regelstudienzeit=8,
            ects_gesamt=180,
            startdatum=date(2025, 9, 1),
        )
        for modul in self._module_definitions():
            modul_id = self._db.create_modul(modul["name"], modul["ects"])
            self._db.assign_modul_to_studiengang(studiengang_id, modul_id)
        return studiengang_id

    def reset_database(self) -> None:
        """Setzt die Datenbanktabellen vollständig zurück."""

        self._db.reset_database()

    def _module_definitions(self) -> List[dict[str, int]]:
        """Liefert alle Module, die das Dashboard nutzt."""

        return [
            {"name": "Artificial Intelligence", "ects": 5},
            {"name": "Einführung in die Programmierung mit Python", "ects": 5},
            {"name": "Mathematik: Analysis", "ects": 5},
            {"name": "Einführung in das wissenschaftliche Arbeiten für IT und Technik", "ects": 5},
            {"name": "Projekt: Objektorientierte und funktionale Programmierung mit Python","ects": 5},
            {"name": "Mathematik: Lineare Algebra", "ects": 5},
            {"name": "Statistik - Wahrscheinlichkeit und deskriptive Statistik", "ects": 5},
            {"name": "Statistik - Induktive Statistik", "ects": 5},
            {"name": "Cloud Computing", "ects": 5},
            {"name": "Projekt: Cloud Programming", "ects": 5},
            {"name": "Maschinelles Lernen - Supervised Learning", "ects": 5},
            {"name": "Maschinelles Lernen - Unsupervised Learning und Feature Engineering", "ects": 5},
            {"name": "Neuronale Netze und Deep Learning", "ects": 5},
            {"name": "Einführung in Computer Vision", "ects": 5},
            {"name": "Projekt: Computer Vision", "ects": 5},
            {"name": "Einführung in das Reinforcement Learning", "ects": 5},
            {"name": "Einführung in Datenschutz und IT-Sicherheit", "ects": 5},
            {"name": "Ethische und rechtliche Aspekte in der KI", "ects": 5},
            {"name": "Einführung in NLP", "ects": 5},
            {"name": "Projekt: NLP", "ects": 5},
            {"name": "Seminar: Ethische Innovation", "ects": 5},
            {"name": "Projekt: Edge AI", "ects": 5},
            {"name": "Model Engineering", "ects": 5},
            {"name": "Bachelorarbeit", "ects": 9},
            {"name": "Kolloquium", "ects": 1},
            # Wahlpflichtbereich A
            {"name": "Mobile Robotik", "ects": 5},
            {"name": "Projekt: Angewandte Robotik mit Robotik-Plattformen", "ects": 5},
            {"name": "Automatisierung und Robotics", "ects": 5},
            {"name": "Self-Driving Vehicles**", "ects": 5},
            {"name": "Digitale Signalverarbeitung", "ects": 5},
            {"name": "Seminar: Current Topics and Trends in Self-Driving Technology**", "ects": 5},
            {"name": "Einführung in die Robotik", "ects": 5},
            {"name": "Sensorik", "ects": 5},
            {"name": "Mechanik - Kinematik", "ects": 5},
            # Wahlpflichtbereich B
            {"name": "Embedded Systems", "ects": 5},
            {"name": "Seminar: Mensch-Maschinen-Interaktion", "ects": 5},
            {"name": "Projekt: X-Reality Einführung in Motion Capturing und Tracking", "ects": 5},
            {"name": "User Experience", "ects": 5},
            {"name": "Projekt: AI in XR", "ects": 5},
            {"name": "Human-Computer Interaction", "ects": 5},
            {"name": "Augmented, Mixed und Virtual Reality", "ects": 5},
            {"name": "UX-Projekt", "ects": 5},
            {"name": "Seminar: Ethische und gesellschaftliche Aspekte von XR", "ects": 5},
            {"name": "Projekt: Generative KI im Unternehmenskontext", "ects": 5},
            # Wahlpflichtbereich C
            {"name": "Project: AWS - Cloud Essentials**", "ects": 5},
            {"name": "Data Science Software Engineering", "ects": 5},
            {"name": "Project: AWS - Cloud Advanced**", "ects": 5},
            {"name": "Projekt: Vom Modell zum Produktivsystem", "ects": 5},
            {"name": "Data Engineering**", "ects": 5},
            {"name": "Digitale Business-Modelle", "ects": 5},
            {"name": "Data Quality and Data Wrangling**", "ects": 5},
            {"name": "Business Intelligence", "ects": 5},
            {"name": "Advanced Data Analysis", "ects": 5},
            {"name": "Projekt: Business Intelligence", "ects": 5},
            {"name": "Projekt: Datenanalyse", "ects": 5},
            {"name": "Datenmodellierung und Datenbanksysteme", "ects": 5},
            {"name": "Big-Data-Technologien", "ects": 5},
            {"name": "Projekt: Digitale Business-Modelle", "ects": 5},
            # Wahlpflichtbereich D
            {"name": "Experience Psychology", "ects": 5},
            {"name": "Interkulturelle und ethische Handlungskompetenzen", "ects": 5},
            {"name": "Ethik und Nachhaltigkeit in der IT", "ects": 5},
            {"name": "Projekt: KI-Exzellenz mit kreativen Prompt-Techniken", "ects": 5},
            {"name": "Kollaboratives Arbeiten", "ects": 5},
            {"name": "IT-Architekturmanagement", "ects": 5},
            {"name": "Personal Skills", "ects": 5},
            {"name": "Studium Generale I", "ects": 5},
            {"name": "Studium Generale II", "ects": 5},
            # Praktikum
            {"name": "Praktikum: Bachelor Data Science und KI", "ects": 30},
        ]


def ensure_schema(db_path: str = "dashboard.db") -> None:
    """Stellt sicher, dass alle benötigten Tabellen existieren."""

    DatenbankConnector(db_path).ensure_schema()


def run_setup(db_path: str = "dashboard.db") -> int:
    """Legt das Dashboard-Startsetup an und gibt die Studiengang-ID zurück."""

    ensure_schema(db_path)
    setup = DashboardSetup(db_path)
    return setup.create_default_studiengang()


def run_reset(db_path: str = "dashboard.db") -> None:
    """Setzt die Datenbank vollständig zurück."""

    DashboardSetup(db_path).reset_database()


if __name__ == "__main__":
    studiengang_id = run_setup()
    print(f"Dashboard-Setup abgeschlossen (Studiengang-ID: {studiengang_id})")
