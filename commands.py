#!/usr/bin/env python3
"""CLI-Entrypoint für das Studienfortschritt-Dashboard."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from typing import List, Optional

from study_service import StudienService
from layout import UIService


DB_PATH = "dashboard.db"


def _print_section(title: str) -> None:
    """Gibt einen formatierten Abschnittstitel aus."""

    print(f"\n{title}")


def _parse_date(value: str) -> datetime:
    """Hilfsfunktion für argparse zur Datumsvalidierung."""

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Ungültiges Datum '{value}'. Erwartetes Format: YYYY-MM-DD"
        ) from exc


class CLIController:
    """
    Steuert die Kommandozeilenoberfläche des Studiengang-Dashboards.

    Die Klasse gehört zur Präsentationsschicht und ist die einzige Stelle,
    an der externe Benutzereingaben über die CLI entgegengenommen werden.
    Sie parst und validiert Kommandozeilenargumente, ruft zur Ausführung
    der Anwendungsfälle Methoden des `StudienService` auf und startet bei
    Bedarf über den `UIService` die grafische Oberfläche. Damit fungiert
    sie als dünne Fassade vor der Anwendungsschicht, ohne eigene
    Geschäftslogik zu enthalten.
    """

    def __init__(self) -> None:
        self.service = StudienService(DB_PATH)
        self.ui_service = UIService(self.service)

    def show_dashboard(self, studiengang_id: int) -> None:
        """Startet die GUI für den angegebenen Studiengang."""

        success = self.ui_service.zeige_dashboard(studiengang_id)
        if not success:
            print(f"FEHLER: Studiengang mit ID {studiengang_id} nicht gefunden oder keine Metriken verfügbar.")
            self.list_studiengaenge()

    def list_studiengaenge(self) -> None:
        """Listet verfügbare Studiengänge samt Basisdaten."""

        _print_section("Verfügbare Studiengänge:")
        studiengaenge = self.service.hole_studiengaenge()
        if not studiengaenge:
            print("Keine Studiengänge gefunden. Nutzen Sie 'python commands.py setup'.")
            return

        for eintrag in studiengaenge:
            print(f"ID: {eintrag['id']:2} | {eintrag['name']}")
            print(f"  Start: {eintrag['startdatum']}")
            print(f"  {eintrag['regelstudienzeit']} Semester | {eintrag['ects_gesamt']} ECTS")

    def list_module(self, studiengang_id: Optional[int] = None) -> None:
        """Listet Module optional gefiltert nach Studiengang."""

        if studiengang_id is not None:
            module = self.service.hole_module(studiengang_id)
            _print_section(f"Module für Studiengang {studiengang_id}:")
        else:
            module = self.service.hole_module()
            _print_section("Verfügbare Module:")

        if not module:
            print("Keine Module gefunden.")
            return

        for eintrag in module:
            startdatum = eintrag.get("startdatum")
            status_parts: List[str] = []
            if startdatum:
                status_parts.append(f"Start: {startdatum}")
            note = eintrag.get("note")
            if note is not None:
                status_parts.append(f"Note: {note}")
            pruefung = eintrag.get("pruefung_datum")
            if pruefung:
                status_parts.append(f"Prüfung: {pruefung}")

            status = f" ({', '.join(status_parts)})" if status_parts else ""
            print(f"ID: {eintrag['id']:3} | {eintrag['name']} [{eintrag['ects']} ECTS]{status}")

    def show_statistics(self) -> None:
        """Gibt Basisstatistiken zur Datenbank aus."""

        stats = self.service.hole_statistiken()
        _print_section("Systemstatistiken:")
        print(f"Studiengänge: {stats['studiengaenge']}")
        print(f"Module: {stats['module']}")
        print(f"Module ohne Startdatum: {stats['module_ohne_startdatum']}")
        print(f"Prüfungsleistungen: {stats['pruefungsleistungen']}")

    def setup_database(self) -> None:
        """Richtet Schema sowie Seed-Daten ein."""

        try:
            studiengang_id = self.service.fuehre_standard_setup_aus()
            if studiengang_id:
                print(f"Setup abgeschlossen (ID: {studiengang_id})")
            else:
                print("FEHLER: Setup fehlgeschlagen")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def create_studiengang(self, name: str, regelstudienzeit: int, ects: int, startdatum: datetime) -> None:
        """Legt einen neuen Studiengang an und gibt die ID aus."""

        try:
            studiengang_id = self.service.erstelle_studiengang(
                name,
                regelstudienzeit,
                ects,
                startdatum.date(),
            )
            print(f"Studiengang angelegt (ID: {studiengang_id})")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def create_modul(
        self,
        name: str,
        ects: int,
        startdatum: Optional[datetime],
        studiengang_id: Optional[int] = None,
    ) -> None:
        """Legt ein Modul an und ordnet es optional einem Studiengang zu."""

        try:
            modul_id = self.service.erstelle_modul(
                name,
                ects,
                startdatum.date() if startdatum else None,
                studiengang_id,
            )
            print(f"Modul angelegt (ID: {modul_id})")
            if studiengang_id is not None:
                print(f"Modul {modul_id} dem Studiengang {studiengang_id} zugeordnet")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def assign_modul(self, studiengang_id: int, modul_id: int) -> None:
        """Verknüpft ein Modul mit einem Studiengang."""

        try:
            if not self.service.verknuepfe_modul(studiengang_id, modul_id):
                print("FEHLER: Studiengang oder Modul wurde nicht gefunden.")
                return
            print(f"Modul {modul_id} dem Studiengang {studiengang_id} zugeordnet")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def add_pruefung(self, modul_id: int, note: float, datum: datetime) -> None:
        """Erfasst eine Prüfungsleistung zu einem Modul."""

        try:
            pruefung_id = self.service.erfasse_pruefungsleistung(modul_id, note, datum.date())
            if pruefung_id is None:
                print(
                    "FEHLER: Prüfungsleistung konnte nicht erfasst werden "
                    "(ungültige Note, Modul nicht gefunden oder bereits vorhanden)."
                )
                return
            print(f"Prüfungsleistung erfasst (ID: {pruefung_id}).")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def delete_modul(self, modul_id: int) -> None:
        """Entfernt ein Modul dauerhaft."""

        try:
            deleted = self.service.loesche_modul(modul_id)
            if deleted:
                print(f"Modul {modul_id} gelöscht.")
            else:
                print(f"HINWEIS: Modul {modul_id} wurde nicht gefunden.")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def delete_pruefung(self, pruefung_id: int) -> None:
        """Löscht eine Prüfungsleistung."""

        try:
            deleted = self.service.loesche_pruefungsleistung(pruefung_id)
            if deleted:
                print(f"Prüfungsleistung {pruefung_id} gelöscht.")
            else:
                print(f"HINWEIS: Prüfungsleistung {pruefung_id} wurde nicht gefunden.")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def delete_studiengang(self, studiengang_id: int) -> None:
        """Entfernt einen Studiengang inklusive Zuordnungen."""

        try:
            deleted = self.service.loesche_studiengang(studiengang_id)
            if deleted:
                print(f"Studiengang {studiengang_id} gelöscht.")
            else:
                print(f"HINWEIS: Studiengang {studiengang_id} wurde nicht gefunden.")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def list_pruefungen(self, modul_id: Optional[int] = None) -> None:
        """Listet Prüfungsleistungen optional gefiltert nach Modul."""

        if modul_id is not None:
            _print_section(f"Prüfungsleistungen für Modul {modul_id}:")
        else:
            _print_section("Alle Prüfungsleistungen:")

        pruefungen = self.service.hole_pruefungsleistungen(modul_id)
        if not pruefungen:
            print("Keine Prüfungsleistungen hinterlegt.")
            return

        for eintrag in pruefungen:
            print(
                "ID: {id:3} | Modul: {modul_id:3} | Note: {note:.1f} | Datum: {datum}".format(
                    **eintrag
                )
            )

    def start_modul(self, modul_id: int, startdatum: Optional[datetime], override: bool) -> None:
        """Setzt oder aktualisiert das Startdatum eines Moduls."""

        ziel_datum = startdatum.date() if startdatum else date.today()
        try:
            aktualisiert = self.service.setze_modul_startdatum(modul_id, ziel_datum, override)
            if not aktualisiert:
                print(
                    "FEHLER: Startdatum konnte nicht gesetzt werden. "
                    "Prüfen Sie, ob das Modul existiert oder bereits ein Startdatum besitzt."
                )
                return
            print(f"Startdatum für Modul {modul_id} gesetzt auf {ziel_datum}.")
        except Exception as exc:
            print(f"FEHLER: {exc}")

    def init_environment(self) -> None:
        """Legt ausschließlich das Datenbankschema an."""

        _print_section("Datenbankstruktur anlegen:")
        try:
            self.service.stelle_schema_sicher()
            print("Datenbankstruktur angelegt oder bereits vorhanden.")
        except Exception as exc:
            print(f"FEHLER beim Anlegen der Struktur: {exc}")

    def reset_database(self) -> None:
        """Setzt die Datenbank nach Rückfrage zurück."""

        confirm = input("Wirklich zurücksetzen? (ja/nein): ").lower()
        if confirm != "ja":
            print("Abgebrochen")
            return
        try:
            self.service.reset_database()
            print("Datenbank zurückgesetzt.")
        except Exception as exc:
            print(f"FEHLER: {exc}")


def cli_entrypoint(argv: Optional[List[str]] = None) -> None:
    """Parst Argumente und führt das gewünschte Kommando aus."""

    args = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Studiengang-Dashboard - CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Legt die Tabellenstruktur an.")
    subparsers.add_parser("setup", help="Erstellt Schema und Seed-Daten.")
    subparsers.add_parser("reset", help="Setzt die Datenbank zurück.")

    p_create_studiengang = subparsers.add_parser(
        "create-studiengang",
        help="Legt einen neuen Studiengang an.",
    )
    p_create_studiengang.add_argument("name", help="Name des Studiengangs")
    p_create_studiengang.add_argument("regelstudienzeit", type=int, help="Regelstudienzeit in Semestern")
    p_create_studiengang.add_argument("ects_gesamt", type=int, help="Gesamt-ECTS")
    p_create_studiengang.add_argument("startdatum",type=_parse_date,help="Startdatum im Format YYYY-MM-DD")

    p_create_modul = subparsers.add_parser(
        "create-modul",
        help="Legt ein neues Modul an.",
    )
    p_create_modul.add_argument("name", help="Name des Moduls")
    p_create_modul.add_argument("ects", type=int, help="ECTS des Moduls")
    p_create_modul.add_argument(
        "--startdatum",
        type=_parse_date,
        default=None,
        help="Optionales Startdatum (YYYY-MM-DD)",
    )
    p_create_modul.add_argument(
        "--studiengang-id",
        type=int,
        default=None,
        help="Ordnet das Modul direkt diesem Studiengang zu",
    )

    p_assign_modul = subparsers.add_parser(
        "assign-modul",
        help="Ordnet ein vorhandenes Modul einem Studiengang zu.",
    )
    p_assign_modul.add_argument("studiengang_id", type=int, help="ID des Studiengangs")
    p_assign_modul.add_argument("modul_id", type=int, help="ID des Moduls")

    p_add_pruefung = subparsers.add_parser(
        "add-pruefung",
        help="Erfasst eine Prüfungsleistung zu einem Modul.",
    )
    p_add_pruefung.add_argument("modul_id", type=int, help="ID des Moduls")
    p_add_pruefung.add_argument("note", type=float, help="Note zwischen 1.0 und 4.0")
    p_add_pruefung.add_argument(
        "datum",
        type=_parse_date,
        help="Datum der Prüfungsleistung (YYYY-MM-DD)",
    )

    p_delete_modul = subparsers.add_parser(
        "delete-modul",
        help="Löscht ein Modul inklusive Zuordnungen.",
    )
    p_delete_modul.add_argument("modul_id", type=int, help="ID des Moduls")

    p_delete_pruefung = subparsers.add_parser(
        "delete-pruefung",
        help="Löscht eine Prüfungsleistung.",
    )
    p_delete_pruefung.add_argument("pruefung_id", type=int, help="ID der Prüfungsleistung")

    p_delete_studiengang = subparsers.add_parser(
        "delete-studiengang",
        help="Löscht einen Studiengang inklusive Zuordnungen.",
    )
    p_delete_studiengang.add_argument("studiengang_id", type=int, help="ID des Studiengangs")

    p_list_modul = subparsers.add_parser(
        "list-modul",
        help="Listet alle Module optional gefiltert nach Studiengang auf.",
    )
    p_list_modul.add_argument(
        "--studiengang-id",
        dest="studiengang_id",
        type=int,
        default=None,
        help="Filtert die Ausgabe auf die Module des angegebenen Studiengangs",
    )

    p_list_pruefung = subparsers.add_parser(
        "list-pruefung",
        help="Listet Prüfungsleistungen auf.",
    )
    p_list_pruefung.add_argument(
        "--modul-id",
        dest="modul_id",
        type=int,
        default=None,
        help="Filtert die Ausgabe auf das angegebene Modul",
    )

    p_show = subparsers.add_parser("show", help="Öffnet das Dashboard für einen Studiengang.")
    p_show.add_argument("studiengang_id", type=int, help="Studiengang-ID")

    subparsers.add_parser("list", help="Listet alle Studiengänge auf.")
    subparsers.add_parser("stats", help="Zeigt Systemstatistiken.")

    p_start_modul = subparsers.add_parser(
        "start-modul",
        help="Setzt das Startdatum für ein Modul.",
    )
    p_start_modul.add_argument("modul_id", type=int, help="ID des Moduls")
    p_start_modul.add_argument(
        "startdatum",
        nargs="?",
        type=_parse_date,
        default=None,
        help="Startdatum (YYYY-MM-DD). Standard: heutiges Datum",
    )
    p_start_modul.add_argument(
        "-o",
        "--override",
        action="store_true",
        help="Überschreibt ein bereits gesetztes Startdatum",
    )

    if not args:
        parser.print_help()
        return

    parsed = parser.parse_args(args)
    cli = CLIController()

    try:
        if parsed.command == "show":
            cli.show_dashboard(parsed.studiengang_id)
        elif parsed.command == "list":
            cli.list_studiengaenge()
        elif parsed.command == "stats":
            cli.show_statistics()
        elif parsed.command == "setup":
            cli.setup_database()
        elif parsed.command == "reset":
            cli.reset_database()
        elif parsed.command == "init":
            cli.init_environment()
        elif parsed.command == "create-studiengang":
            cli.create_studiengang(
                parsed.name,
                parsed.regelstudienzeit,
                parsed.ects_gesamt,
                parsed.startdatum,
            )
        elif parsed.command == "create-modul":
            cli.create_modul(
                parsed.name,
                parsed.ects,
                parsed.startdatum,
                parsed.studiengang_id,
            )
        elif parsed.command == "assign-modul":
            cli.assign_modul(parsed.studiengang_id, parsed.modul_id)
        elif parsed.command == "add-pruefung":
            cli.add_pruefung(parsed.modul_id, parsed.note, parsed.datum)
        elif parsed.command == "delete-modul":
            cli.delete_modul(parsed.modul_id)
        elif parsed.command == "delete-pruefung":
            cli.delete_pruefung(parsed.pruefung_id)
        elif parsed.command == "delete-studiengang":
            cli.delete_studiengang(parsed.studiengang_id)
        elif parsed.command == "list-modul":
            cli.list_module(parsed.studiengang_id)
        elif parsed.command == "list-pruefung":
            cli.list_pruefungen(parsed.modul_id)
        elif parsed.command == "start-modul":
            cli.start_modul(parsed.modul_id, parsed.startdatum, parsed.override)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer")
    except Exception as exc:
        print(f"FEHLER: {exc}")


if __name__ == "__main__":
    cli_entrypoint()
