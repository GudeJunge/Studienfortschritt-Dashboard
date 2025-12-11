# Studienfortschritt-Dashboard

Dieses lokale Dashboard dient zur einfachen Überwachung des Studienfortschritts und verfolgt zwei konkrete Ziele:

- Das Studium soll mit einem Notendurchschnitt von maximal 1,9 abgeschlossen werden.
- Das Studium soll innerhalb der Regelstudienzeit abgeschlossen 
werden.

**Hinweis:** Das Dashboard kann mehrere benutzerdefinierte Studiengänge unterstützen und kann frei von anderen Personen genutzt werden. Eine Anpassung der Ziele ist jedoch nicht ohne Code-Anpassungen möglich.

## Installation
Für eine ausführliche Schritt-für-Schritt-Anleitung siehe [`installation_instructions.md`](installation_instructions.md).

## Dateiübersicht
- `commands.py` — Enthält den `CLIController` (Präsentationsschicht) und die Definition der verfügbaren Konsolenbefehle (z. B. `init`, `setup`, `show`, `list`, `stats`). Der `CLIController` nimmt ausschließlich Benutzereingaben über die Konsole entgegen und leitet gültige Befehle an den `StudienService` bzw. `UIService` weiter (siehe Abschnitt [Befehlsübersicht](#befehlsübersicht)).
- `study_service.py` — Enthält die Klasse `StudienService` (Anwendungsschicht). Sie verarbeitet alle Befehle aus der CLI, erstellt bzw. ändert Studiengänge, Module und Prüfungsleistungen, führt `init`, `reset`, `setup` aus und stellt Dashboard-Daten für die Präsentationsschicht bereit.
- `database_connector.py` — Enthält die Klasse `DatenbankConnector` (Infrastrukturschicht), die die Verbindung zur SQLite-Datenbank herstellt und alle Lese- und Schreiboperationen auf den Tabellen `studiengang`, `modul` und `pruefungsleistung` kapselt.
- `layout.py` — Definiert die grafische Benutzeroberfläche des Dashboards. Enthält das Hauptfenster `DashboardLayout`, mehrere UI-Hilfsklassen (z. B. `RoundedBox`, `EctsProgressBarWidget`, `KPISection`, `DiagramSection`) sowie den `UIService` (Präsentationsschicht), der das Dashboard-Fenster startet und die vom `StudienService` gelieferten Metriken in die UI einbindet.
- `metrics.py` — Enthält die Hilfsklasse `DashboardMetrics`, welche die vom `StudienService` bereitgestellten Dashboard-Daten in Kennzahlen und Diagramme für die grafische Oberfläche umrechnet.
- `models.py` — Definiert die Domänenklassen `Studiengang`, `Modul` und `Pruefungsleistung` inklusive Methoden zur Berechnung von Notendurchschnitt, ECTS-Fortschritt und Zeitaufwand.
- `setup.py` — Personalisiertes Setup-Skript zur Anlage aller zugehörigen Daten des Studiengangs "B.Sc. Angewandte Künstliche Intelligenz" und Initialisierung der Datenbank.
## Befehlsübersicht

**Hinweis:** Für detaillierte Hilfe zu allen Befehlen verwenden Sie `python .\commands.py --help` oder
`python .\commands.py <befehl> --help` für den jeweiligen Befehl.

- `add-pruefung` — Fügt eine Prüfungsleistung zu einem spezifischen Modul hinzu.
	- Parameter: modul_id (int), note (float 1.0–4.0), datum (YYYY-MM-DD).
- `assign-modul` — Ordnet ein vorhandenes Modul einem Studiengang zu.
	- Parameter: studiengang_id (int), modul_id (int).
- `create-modul` — Erstellt ein neues Modul.
	- Parameter: name (string), ects (int), optional `--startdatum` (YYYY-MM-DD), optional `--studiengang-id` (int).
- `create-studiengang` — Erstellt einen neuen Studiengang.
	- Parameter: Name (string), Regelstudienzeit (Semester, int), Gesamt-ECTS (int), Startdatum (YYYY-MM-DD).
- `delete-modul` — Löscht ein Modul und die zugehörige Prüfungsleistung (falls vorhanden).
	- Parameter: modul_id (int).
- `delete-pruefung` — Löscht eine Prüfungsleistung.
	- Parameter: pruefung_id (int).
- `delete-studiengang` — Löscht einen Studiengang und entfernt Zuordnungen; Module bleiben erhalten.
	- Parameter: studiengang_id (int).
- `init` — Legt die Datenbankstruktur in `dashboard.db` an (Tabellen), ohne Daten zu befüllen.
	- Parameter: Keine.
- `list` — Zeigt alle Studiengänge mit Basis-Informationen (ID, Name, Startdatum, ECTS).
	- Parameter: Keine.
- `list-modul` — Zeigt alle Module (ID, Name, ECTS, Startdatum, Status).
	- Parameter: optional `--studiengang-id` (int).
- `list-pruefung` — Listet Prüfungsleistungen; optional nach Modul filtern.
	- Parameter: optional `--modul-id` (int).
- `reset` — Löscht alle Daten und erstellt die Tabellen neu (Vorsicht: unwiderruflich).
	- Parameter: Keine.
- `show <studiengang_id>` — Öffnet die grafische Oberfläche des Dashboards für den angegebenen Studiengang.
	- Parameter: studiengang_id (int).
- `start-modul` — Setzt das Startdatum für ein Modul.
	- Parameter: modul_id (int), optional startdatum (YYYY-MM-DD; Standard: heute), optional `-o/--override` zum Überschreiben eines vorhandenen Startdatums.
- `stats` — Zeigt Systemstatistiken (Anzahl Studiengänge, Module, Prüfungsleistungen, Module ohne Startdatum).
	- Parameter: Keine.

Beispiel: `python .\commands.py show 1` öffnet das Dashboard für Studiengang mit ID 1.

## Weitere Hinweise
Sollten Sie das Dashboard, wie in der [Installationsanleitung](installation_instructions.md) empfohlen, in einer virtuellen Umgebung nutzen, vergessen Sie nicht diese vor Aufruf eines Befehls zu aktivieren.
- `.\venv\Scripts\Activate.ps1`