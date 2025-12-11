"""Anwendungsschicht für das Studiengang-Dashboard.

Diese Datei definiert die Klasse StudienService, welche als zentrale
Steuerungseinheit der Anwendung fungiert. Sie koordiniert die Ausführung
von Anwendungsfällen, nutzt dafür die Infrastrukturschicht
(`DatenbankConnector`) und stellt Datenpakete für Präsentationsschichten
wie CLI und GUI bereit.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from database_connector import DatenbankConnector


@dataclass
class ProgressDaten:
    """
    Beschreibt den ECTS-Fortschritt eines Studiengangs in aggregierter Form.

    Diese Hilfsklasse wird in der Anwendungsschicht vom `StudienService`
    genutzt, um die für die Fortschrittsanzeige relevanten Kennzahlen
    (Ist-, Soll- und Gesamt-ECTS) zu bündeln. Sie wird anschließend als
    Teil von `DashboardDaten` an die Präsentationsschicht weitergereicht.
    """

    ist_ects: int
    soll_ects: int
    gesamt_ects: int


@dataclass
class PrognoseDaten:
    """
    Fasst die Einschätzung zur Zielerreichung eines Studiengangs zusammen.

    Die Klasse gehört zur Anwendungsschicht und wird vom `StudienService`
    befüllt, um abzubilden, ob Noten- und Zeitziele voraussichtlich
    erreicht werden. Sie ist Bestandteil des `DashboardDaten`-Pakets und
    dient der Präsentationsschicht als strukturierte Grundlage für die
    Prognose-KPI.
    """

    noten_ziel_erreicht: bool
    zeit_ziel_erreicht: bool
    regelstudienzeit_jahre: float


@dataclass
class DashboardDaten:
    """
    Aggregiertes Datenpaket für das Dashboard eines Studiengangs.

    Dieses Objekt wird vom StudienService aufgebaut und anschließend in
    der Präsentationsschicht (z. B. durch `DashboardMetrics` und
    `UIService`) verwendet. Es kapselt alle für die grafische Darstellung
    benötigten Informationen und trennt damit Anwendungslogik von der
    konkreten UI-Implementierung.
    """

    studiengang_name: str
    progress: ProgressDaten
    notendurchschnitt: Optional[float]
    tage_pro_modul_richtwert: float
    tage_pro_modul_text: str
    prognose: PrognoseDaten
    notenverlauf: List[float]
    zeitaufwand_history: List[Tuple[str, int]]


class StudienService:
    """
    Zentrales Steuerungselement der Anwendungsschicht.

    Die Klasse orchestriert alle Anwendungsfälle rund um Studiengang,
    Modul und Prüfungsleistung und verwaltet die Domänenobjekte
    `Studiengang` und `Modul`. Sie nutzt die Infrastrukturschicht
    (`DatenbankConnector`), um Objekte zu laden, zu speichern und zu
    löschen, stellt der Präsentationsschicht (CLI und GUI) fachlich
    aufbereitete Datenpakete bereit und enthält keine UI- oder
    Datenbankdetails. Im Sinne der Schichtenarchitektur ist sie das
    Bindeglied zwischen Präsentations- und Infrastrukturschicht.
    """

    def __init__(self, db_path: str = "dashboard.db") -> None:
        """Initialisiert den Service mit einem Datenbankpfad."""

        self._db_path = db_path
        self._connector = DatenbankConnector(db_path)

    def stelle_schema_sicher(self) -> None:
        """Stellt sicher, dass alle benötigten Tabellen existieren."""

        self._connector.ensure_schema()

    def reset_database(self) -> None:
        """
        Setzt die Datenbank vollständig zurück und legt das Schema neu an.

        Die Implementierung nutzt intern die Hilfsklasse `DashboardSetup`,
        damit die Logik zum Zurücksetzen zentral gekapselt ist.
        """

        from setup import DashboardSetup

        setup = DashboardSetup(self._db_path)
        setup.reset_database()

    def erstelle_studiengang(
        self,
        name: str,
        regelstudienzeit: int,
        ects_gesamt: int,
        startdatum: date,
    ) -> int:
        """Legt einen neuen Studiengang an und gibt die ID zurück."""

        return self._connector.create_studiengang(
            name=name,
            regelstudienzeit=regelstudienzeit,
            ects_gesamt=ects_gesamt,
            startdatum=startdatum,
        )

    def erstelle_modul(
        self,
        name: str,
        ects: int,
        startdatum: Optional[date] = None,
        studiengang_id: Optional[int] = None,
    ) -> int:
        """
        Legt ein Modul an und ordnet es optional einem Studiengang zu.

        Gibt die ID des neu angelegten Moduls zurück.
        """

        modul_id = self._connector.create_modul(name=name, ects=ects, startdatum=startdatum)
        if studiengang_id is not None:
            self.verknuepfe_modul(studiengang_id=studiengang_id, modul_id=modul_id)
        return modul_id

    def verknuepfe_modul(self, studiengang_id: int, modul_id: int) -> bool:
        """Verknüpft ein vorhandenes Modul mit einem Studiengang."""

        studiengang = self._connector.get_studiengang_by_id(studiengang_id)
        modul = self._connector.get_module_by_id(modul_id)
        if studiengang is None or modul is None:
            return False
        self._connector.assign_modul_to_studiengang(studiengang_id, modul_id)
        return True

    def erfasse_pruefungsleistung(
        self,
        modul_id: int,
        note: float,
        datum: date,
    ) -> Optional[int]:
        """
        Erfasst eine Prüfungsleistung zu einem Modul, sofern zulässig.

        Gibt die ID der neuen Prüfungsleistung zurück oder ``None``, wenn
        keine Anlage erfolgt ist (z. B. ungültige Note oder bereits vorhanden).
        """

        if note < 1.0 or note > 4.0:
            return None
        modul = self._connector.get_module_by_id(modul_id)
        if modul is None:
            return None
        vorhandene = self._connector.get_all_pruefungsleistungen(modul_id)
        if vorhandene:
            return None
        return self._connector.create_pruefungsleistung(modul_id, note, datum)

    def loesche_modul(self, modul_id: int) -> bool:
        """Löscht ein Modul inklusive zugehöriger Prüfungsleistungen."""

        return self._connector.delete_modul(modul_id)

    def loesche_pruefungsleistung(self, pruefung_id: int) -> bool:
        """Löscht eine Prüfungsleistung anhand ihrer ID."""

        return self._connector.delete_pruefung(pruefung_id)

    def loesche_studiengang(self, studiengang_id: int) -> bool:
        """Löscht einen Studiengang inklusive Zuordnungen."""

        return self._connector.delete_studiengang(studiengang_id)

    def setze_modul_startdatum(
        self,
        modul_id: int,
        startdatum: Optional[date],
        override: bool = False,
    ) -> bool:
        """
        Setzt oder aktualisiert das Startdatum eines Moduls.

        Bei nicht gesetztem Startdatum wird das heutige Datum verwendet.
        """

        modul = self._connector.get_module_by_id(modul_id)
        if modul is None:
            return False

        aktuelles_startdatum = modul.get("startdatum")
        if aktuelles_startdatum and not override:
            return False

        ziel_datum = startdatum or date.today()
        return self._connector.start_modul(modul_id, ziel_datum)

    def hole_studiengaenge(self) -> List[Dict]:
        """Liefert alle Studiengänge als Liste von Dictionaries."""

        return self._connector.get_all_studiengaenge()

    def hole_module(self, studiengang_id: Optional[int] = None) -> List[dict]:
        """Liefert Module optional gefiltert nach Studiengang."""

        if studiengang_id is not None:
            return self._connector.get_module_by_studiengang(studiengang_id)
        return self._connector.get_all_module()

    def hole_pruefungsleistungen(self, modul_id: Optional[int] = None) -> List[dict]:
        """Liefert Prüfungsleistungen optional gefiltert nach Modul."""

        return self._connector.get_all_pruefungsleistungen(modul_id)

    def hole_statistiken(self) -> dict:
        """Berechnet einfache Statistiken über den Datenbestand."""

        return self._connector.get_statistics()

    def lade_studiengang(self, studiengang_id: int):
        """Lädt einen Studiengang inklusive Module über den Connector."""

        return self._connector.get_studiengang_by_id(studiengang_id)

    # ------------------------------------------------------------------
    # Dashboard-Datenaufbereitung
    # ------------------------------------------------------------------

    def _berechne_enddatum(self, startdatum: date, regelstudienzeit_semester: int) -> date:
        """Berechnet das geplante Studienende anhand Startdatum und Regelstudienzeit."""

        monate = max(regelstudienzeit_semester * 6, 0)
        jahr = startdatum.year + (startdatum.month - 1 + monate) // 12
        monat = (startdatum.month - 1 + monate) % 12 + 1
        tag = min(startdatum.day, calendar.monthrange(jahr, monat)[1])
        return date(jahr, monat, tag)

    @staticmethod
    def _runde_zu_modul_ects(raw_value: float, gesamt_ects: int) -> int:
        """Rundet den Soll-ECTS-Wert auf ein Vielfaches von 5 und begrenzt ihn sinnvoll."""

        if gesamt_ects <= 0:
            return 0
        multiple_of_five = int(round(raw_value / 5.0) * 5)
        return max(0, min(multiple_of_five, gesamt_ects))

    def _berechne_progress_daten(self, studiengang) -> ProgressDaten:
        """Berechnet alle Kennzahlen für die Fortschrittsanzeige."""

        ist_ects = studiengang.berechneErreichteECTS()
        gesamt_ects = studiengang.ects_gesamt
        startdatum = studiengang.startdatum
        regelstudienzeit = studiengang.regelstudienzeit
        enddatum = self._berechne_enddatum(startdatum, regelstudienzeit)
        gesamt_tage = max((enddatum - startdatum).days, 0)
        heutedatum = min(date.today(), enddatum)
        verstrichene_tage = max((heutedatum - startdatum).days, 0)
        soll_anteil = (verstrichene_tage / gesamt_tage) if gesamt_tage > 0 else 0.0
        raw_soll_ects = gesamt_ects * min(soll_anteil, 1.0)
        soll_ects = self._runde_zu_modul_ects(raw_soll_ects, gesamt_ects)
        return ProgressDaten(ist_ects=ist_ects, soll_ects=soll_ects, gesamt_ects=gesamt_ects)

    def _berechne_prognose_daten(
        self,
        studiengang,
        progress: ProgressDaten,
        notendurchschnitt: Optional[float],
    ) -> PrognoseDaten:
        """Ermittelt die Prognose zur Zielerreichung auf Basis der Kennzahlen."""

        note_ziel = notendurchschnitt is not None and notendurchschnitt <= 1.9
        zeit_ziel = progress.ist_ects >= progress.soll_ects
        regelstudienzeit = studiengang.regelstudienzeit
        regelstudienzeit_jahre = regelstudienzeit / 2
        return PrognoseDaten(
            noten_ziel_erreicht=note_ziel,
            zeit_ziel_erreicht=zeit_ziel,
            regelstudienzeit_jahre=regelstudienzeit_jahre,
        )

    def _ermittle_zeitaufwand_history(self, studiengang) -> List[Tuple[str, int]]:
        """
        Erstellt eine zeitlich sortierte Liste von Modulen mit benötigten Tagen.

        Jedes Element besteht aus Modulname und benötigter Tagesanzahl.
        """

        daten: List[Tuple[str, int, date]] = []
        for modul in studiengang.module_list:
            pruefungsleistung = modul.pruefungsleistung
            if not pruefungsleistung:
                continue
            tage = modul.berechneBenoetigteTage()
            if tage is not None:
                daten.append((modul.name, tage, pruefungsleistung.datum))
        daten.sort(key=lambda eintrag: eintrag[2])
        return [(name, tage) for name, tage, _ in daten]

    def erzeuge_dashboard_daten(self, studiengang_id: int) -> Optional[DashboardDaten]:
        """
        Baut ein vollständiges Dashboard-Datenpaket für einen Studiengang auf.

        Gibt ein DashboardDaten-Objekt zurück oder ``None``, falls der
        Studiengang nicht existiert.
        """

        studiengang = self.lade_studiengang(studiengang_id)
        if studiengang is None:
            return None

        progress = self._berechne_progress_daten(studiengang)
        notendurchschnitt = studiengang.berechneNotendurchschnitt()
        richtwert = studiengang.berechneTageProModulRichtwert()
        tage_text = "∞" if richtwert >= 999.0 else f"{richtwert:.0f} Tage"
        prognose = self._berechne_prognose_daten(studiengang, progress, notendurchschnitt)
        notenverlauf = studiengang.berechneNotendurchschnittVerlauf()
        zeitaufwand_history = self._ermittle_zeitaufwand_history(studiengang)

        return DashboardDaten(
            studiengang_name=studiengang.name,
            progress=progress,
            notendurchschnitt=notendurchschnitt,
            tage_pro_modul_richtwert=richtwert,
            tage_pro_modul_text=tage_text,
            prognose=prognose,
            notenverlauf=notenverlauf,
            zeitaufwand_history=zeitaufwand_history,
        )

    def fuehre_standard_setup_aus(self) -> int:
        """
        Führt das vordefinierte Dashboard-Setup für den Studiengang "Angewandte Künstliche Intelligenz" aus.

        Diese Methode gehört zur Anwendungsschicht und nutzt die
        Hilfsklasse `DashboardSetup`, um das Tabellen-Schema sicher
        anzulegen und anschließend den Beispielstudiengang samt Modulen zu
        erstellen. Sie wird von der Präsentationsschicht (CLI) über den
        `CLIController` aufgerufen.
        """

        from setup import DashboardSetup, ensure_schema

        ensure_schema(self._db_path)
        setup = DashboardSetup(self._db_path)
        return setup.create_default_studiengang()