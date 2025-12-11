"""Datenbankzugriffsschicht für das Studiengang-Dashboard."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Any, Iterator, List, Optional

from models import Modul, Studiengang

LOGGER = logging.getLogger(__name__)

Params = tuple[Any, ...]
RowDict = dict[str, Any]


class DatenbankConnector:
    """
    Verwaltet die SQLite-Anbindung der Dashboard-Anwendung.

    Diese Klasse gehört zur Infrastrukturschicht und kapselt alle direkten
    Zugriffe auf die SQLite-Datenbank. Sie stellt der Anwendungsschicht
    (`StudienService`) und Hilfsklassen wie `DashboardSetup` CRUD-
    Operationen für die Domänenobjekte zur Verfügung, ohne dass diese die
    konkreten SQL-Statements kennen müssen. Eine direkte Verwendung in
    der Präsentationsschicht ist nicht vorgesehen.
    """

    def __init__(self, db_path: str = "dashboard.db") -> None:
        """Initialisiert den Connector und stellt das Schema sicher.

        Args:
            db_path: Pfad zur SQLite-Datei.
        """

        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Stellt eine Datenbankverbindung mit bereinigtem Fehlerfall bereit.

        Yields:
            Eine offene SQLite-Verbindung.
        """

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as exc:  # pragma: no cover - Laufzeitfehler
            conn.rollback()
            LOGGER.error("Datenbankfehler: %s", exc)
            raise
        finally:
            conn.close()

    def ensure_schema(self) -> None:
        """Erzeugt fehlende Tabellen erneut."""

        self._create_tables()

    def create_studiengang(
        self,
        name: str,
        regelstudienzeit: int,
        ects_gesamt: int,
        startdatum: date,
    ) -> int:
        """Legt einen Studiengang an.

        Args:
            name: Studiengangbezeichnung.
            regelstudienzeit: Anzahl Semester.
            ects_gesamt: Ziel-ECTS.
            startdatum: Startdatum des Studiums.

        Returns:
            Primärschlüssel des neuen Datensatzes.
        """

        query = (
            "INSERT INTO studiengang (name, regelstudienzeit, ects_gesamt, startdatum) "
            "VALUES (?, ?, ?, ?)"
        )
        return self._run_write(
            query,
            (name, regelstudienzeit, ects_gesamt, startdatum.isoformat()),
            return_lastrowid=True,
        )

    def create_modul(self, name: str, ects: int, startdatum: Optional[date] = None) -> int:
        """Legt ein Modul an und liefert die ID zurück.

        Args:
            name: Modulname.
            ects: Vergebene ECTS.
            startdatum: Optionales Startdatum.

        Returns:
            Primärschlüssel des neuen Datensatzes.
        """

        query = "INSERT INTO modul (name, ects, startdatum) VALUES (?, ?, ?)"
        start_value = startdatum.isoformat() if startdatum else None
        return self._run_write(query, (name, ects, start_value), return_lastrowid=True)

    def create_pruefungsleistung(self, modul_id: int, note: float, datum: date) -> int:
        """Speichert eine Prüfungsleistung zu einem Modul.

        Args:
            modul_id: Zugeordnetes Modul.
            note: Erzielte Note.
            datum: Prüfungsdatum.

        Returns:
            Primärschlüssel des neuen Datensatzes.
        """

        query = "INSERT INTO pruefungsleistung (modul_id, note, datum) VALUES (?, ?, ?)"
        return self._run_write(query, (modul_id, note, datum.isoformat()), return_lastrowid=True)

    def assign_modul_to_studiengang(self, studiengang_id: int, modul_id: int) -> None:
        """Verknüpft ein Modul mit einem Studiengang."""

        query = (
            "INSERT OR IGNORE INTO studiengang_modul (studiengang_id, modul_id) VALUES (?, ?)"
        )
        self._run_write(query, (studiengang_id, modul_id))

    def get_studiengang_by_id(self, studiengang_id: int) -> Optional[Studiengang]:
        """Lädt einen Studiengang inklusive Modulen.

        Args:
            studiengang_id: Primärschlüssel des gewünschten Studiengangs.

        Returns:
            Studiengang-Objekt oder ``None`` wenn nicht vorhanden.
        """

        studiengang_row = self._run_query_one(
            "SELECT * FROM studiengang WHERE id = ?",
            (studiengang_id,),
        )
        if studiengang_row is None:
            return None

        studiengang = Studiengang(
            name=studiengang_row["name"],
            regelstudienzeit=studiengang_row["regelstudienzeit"],
            ects_gesamt=studiengang_row["ects_gesamt"],
            startdatum=date.fromisoformat(studiengang_row["startdatum"]),
        )

        module = self._run_query_all(
            """
            SELECT m.*, p.note, p.datum AS pruefung_datum
            FROM modul m
            JOIN studiengang_modul sm ON m.id = sm.modul_id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            WHERE sm.studiengang_id = ?
            ORDER BY m.startdatum
            """,
            (studiengang_id,),
        )

        for modul_row in module:
            modul_start = (
                date.fromisoformat(modul_row["startdatum"])
                if modul_row["startdatum"]
                else None
            )
            modul = Modul(
                name=modul_row["name"],
                ects=modul_row["ects"],
                startdatum=modul_start,
            )
            if modul_row["note"] is not None:
                modul.setPruefungsleistung(
                    note=modul_row["note"],
                    datum=date.fromisoformat(modul_row["pruefung_datum"]),
                )
            studiengang.addModul(modul)

        return studiengang

    def get_all_studiengaenge(self) -> List[RowDict]:
        """Listet alle Studiengänge auf."""

        query = "SELECT id, name, regelstudienzeit, ects_gesamt, startdatum FROM studiengang"
        return self._run_query_all(query)

    def get_module_by_studiengang(self, studiengang_id: int) -> List[RowDict]:
        """Liefert alle Module eines Studiengangs.

        Args:
            studiengang_id: Primärschlüssel des Studiengangs.

        Returns:
            Liste der Modul-Datensätze.
        """

        query = """
            SELECT m.id, m.name, m.ects, m.startdatum,
                   p.note, p.datum AS pruefung_datum
            FROM modul m
            JOIN studiengang_modul sm ON m.id = sm.modul_id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            WHERE sm.studiengang_id = ?
            ORDER BY m.startdatum
        """
        return self._run_query_all(query, (studiengang_id,))

    def update_studiengang(
        self,
        studiengang_id: int,
        name: Optional[str] = None,
        regelstudienzeit: Optional[int] = None,
        ects_gesamt: Optional[int] = None,
    ) -> bool:
        """Aktualisiert Stammdaten eines Studiengangs.

        Args:
            studiengang_id: Primärschlüssel des Datensatzes.
            name: Optional neuer Name.
            regelstudienzeit: Neue Semesterzahl.
            ects_gesamt: Neue Gesamt-ECTS.

        Returns:
            ``True`` bei Erfolg, sonst ``False``.
        """

        updates: List[str] = []
        params: List[Any] = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if regelstudienzeit is not None:
            updates.append("regelstudienzeit = ?")
            params.append(regelstudienzeit)
        if ects_gesamt is not None:
            updates.append("ects_gesamt = ?")
            params.append(ects_gesamt)
        if not updates:
            return False

        params.append(studiengang_id)
        query = f"UPDATE studiengang SET {', '.join(updates)} WHERE id = ?"
        return self._run_write(query, tuple(params)) > 0

    def delete_studiengang(self, studiengang_id: int) -> bool:
        """Entfernt einen Studiengang dauerhaft."""

        query = "DELETE FROM studiengang WHERE id = ?"
        return self._run_write(query, (studiengang_id,)) > 0

    def delete_modul(self, modul_id: int) -> bool:
        """Löscht ein Modul inklusive Prüfungen."""

        query = "DELETE FROM modul WHERE id = ?"
        return self._run_write(query, (modul_id,)) > 0

    def delete_pruefung(self, pruefung_id: int) -> bool:
        """Entfernt eine Prüfungsleistung."""

        query = "DELETE FROM pruefungsleistung WHERE id = ?"
        return self._run_write(query, (pruefung_id,)) > 0

    def remove_modul_from_studiengang(self, studiengang_id: int, modul_id: int) -> bool:
        """Löst die Zuordnung eines Moduls zum Studiengang."""

        query = (
            "DELETE FROM studiengang_modul WHERE studiengang_id = ? AND modul_id = ?"
        )
        return self._run_write(query, (studiengang_id, modul_id)) > 0

    def start_modul(self, modul_id: int, startdatum: date) -> bool:
        """Hinterlegt ein Startdatum für ein Modul."""

        query = "UPDATE modul SET startdatum = ? WHERE id = ?"
        return self._run_write(query, (startdatum.isoformat(), modul_id)) > 0

    def get_all_module(self) -> List[RowDict]:
        """Listet alle Module sortiert nach ihrer ID."""

        query = "SELECT id, name, ects, startdatum FROM modul ORDER BY id"
        return self._run_query_all(query)

    def get_module_by_id(self, modul_id: int) -> Optional[RowDict]:
        """Lädt ein Modul anhand der ID."""

        query = "SELECT id, name, ects, startdatum FROM modul WHERE id = ?"
        return self._run_query_one(query, (modul_id,))

    def get_all_pruefungsleistungen(
        self, modul_id: Optional[int] = None
    ) -> List[RowDict]:
        """Ermittelt Prüfungsleistungen optional gefiltert nach Modul."""

        if modul_id is not None:
            query = (
                "SELECT id, modul_id, note, datum FROM pruefungsleistung "
                "WHERE modul_id = ? ORDER BY datum"
            )
            return self._run_query_all(query, (modul_id,))
        query = "SELECT id, modul_id, note, datum FROM pruefungsleistung ORDER BY datum"
        return self._run_query_all(query)

    def reset_database(self) -> None:
        """Setzt die Datenbank vollständig zurück."""

        script = """
            DROP TABLE IF EXISTS studiengang_modul;
            DROP TABLE IF EXISTS pruefungsleistung;
            DROP TABLE IF EXISTS modul;
            DROP TABLE IF EXISTS studiengang;
        """
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()
        self._create_tables()

    def get_statistics(self) -> RowDict:
        """Berechnet einfache Statistiken über den Datenbestand."""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM studiengang")
            studiengaenge = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM modul")
            module = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM pruefungsleistung")
            pruefungen = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM modul WHERE startdatum IS NULL")
            ohne_start = cursor.fetchone()[0]
        return {
            "studiengaenge": studiengaenge,
            "module": module,
            "module_ohne_startdatum": ohne_start,
            "pruefungsleistungen": pruefungen,
        }

    def _create_tables(self) -> None:
        """Legt alle benötigten Tabellen inklusive Relationen an."""

        schema = """
            CREATE TABLE IF NOT EXISTS studiengang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                regelstudienzeit INTEGER NOT NULL,
                ects_gesamt INTEGER NOT NULL,
                startdatum DATE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS modul (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                ects INTEGER NOT NULL,
                startdatum DATE
            );

            CREATE TABLE IF NOT EXISTS pruefungsleistung (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modul_id INTEGER NOT NULL UNIQUE,
                note REAL NOT NULL,
                datum DATE NOT NULL,
                FOREIGN KEY (modul_id) REFERENCES modul (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS studiengang_modul (
                studiengang_id INTEGER NOT NULL,
                modul_id INTEGER NOT NULL,
                PRIMARY KEY (studiengang_id, modul_id),
                FOREIGN KEY (studiengang_id) REFERENCES studiengang (id) ON DELETE CASCADE,
                FOREIGN KEY (modul_id) REFERENCES modul (id) ON DELETE CASCADE
            );
        """
        with self.get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    def _run_write(
        self, query: str, params: Params = (), *, return_lastrowid: bool = False
    ) -> int:
        """Führt schreibende Statements aus und liefert Statusinformationen."""

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid if return_lastrowid else cursor.rowcount

    def _run_query_one(self, query: str, params: Params = ()) -> Optional[RowDict]:
        """Holt einen einzelnen Datensatz."""

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
        return dict(row) if row else None

    def _run_query_all(self, query: str, params: Params = ()) -> List[RowDict]:
        """Holt mehrere Datensätze als Liste."""

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        return [dict(row) for row in rows]
