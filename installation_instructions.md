# Installationsanleitung

Diese Schritt-für-Schritt Anleitung behandelt die Installation, Initialisierung und Einrichtung, sowie Nutzung des Dashboards.

> **Hinweis:** Alle Befehle sind für Windows PowerShell angegeben. Bei Nutzung der Eingabeaufforderung (CMD) können einzelne Befehle leicht abweichen.

## 📋 Voraussetzungen
- Windows 10 oder 11
- Python 3.11 oder neuer; prüfen Sie die Installation mit `python --version`
- Git ist installiert und im `PATH` verfügbar; prüfen Sie die Installation mit `git --version`. Download: [Git für Windows](https://git-scm.com/download/win)
- PowerShell ExecutionPolicy erlaubt die Ausführung von lokalen Skripten; empfohlen: `RemoteSigned`

## ⚙️ Installation
1. In den Zielordner wechseln, in dem das Dashboard installiert werden soll (Beispiel anpassen):
	```powershell
	Set-Location C:\Users\<IhrBenutzer>\GitHub
	```
2. Repository klonen:
	```powershell
	git clone https://github.com/GudeJunge/Studienfortschritt-Dashboard
	cd Studienfortschritt-Dashboard
	```
3. Virtuelle Umgebung erstellen:
	```powershell
	python -m venv venv
	```
4. Virtuelle Umgebung aktivieren:
	```powershell
	.\venv\Scripts\Activate.ps1
	```
5. Abhängigkeiten installieren:
	```powershell
	pip install -r requirements.txt
	```

## ⌨️ Initialisierung und Einrichtung
Wählen Sie eine der folgenden Optionen, um das Dashboard einzurichten.

### Option A: Schnellstart (vordefinierter Studiengang)
Legt alle Tabellen an und befüllt sie mit dem Studiengang „B.Sc. Angewandte Künstliche Intelligenz“ inklusive vollständiger Modulliste.

```powershell
python .\commands.py setup
```

Der Befehl meldet die erzeugte Studiengang-ID (standardmäßig `1`).

### Option B: Benutzerdefinierte Konfiguration
Manuelle Anlage eigener Studiengänge und Module über die CLI.

1. Tabellenstruktur ohne Seed-Daten erstellen:
	```powershell
	python .\commands.py init
	```
2. Eigenen Studiengang anlegen (Name, Regelstudienzeit in Semestern, Gesamt-ECTS, Startdatum anpassen):
	```powershell
	python .\commands.py create-studiengang "Beispielstudiengang" 8 180 2025-10-01
	```
	Die ausgegebene ID merken (z. B. `1`).
3. Modul(e) anlegen und unmittelbar mit dem Studiengang verknüpfen (Name, ECTS und Studiengang-ID anpassen):
	```powershell
	python .\commands.py create-modul "Mein erstes Modul" 5 --studiengang-id 1
	```
	Der Parameter `--studiengang-id` sollte stets gesetzt werden, damit das Modul direkt zugeordnet wird. Wiederholen Sie diesen Schritt solange, bis alle gewollten Module angelegt sind.

## 💻 Nutzung des Dashboards

### Modulstart erfassen
Hinterlegen Sie ein Startdatum für ein Modul, sobald Sie damit beginnen (IDs und Datum anpassen):

```powershell
python .\commands.py start-modul 1 2025-10-01
```

> Tipp: Falls Sie die Modul-ID nicht kennen, listen Sie alle Module mit `python .\commands.py list-modul` auf.

### Modulabschluss dokumentieren
Tragen Sie nach Abschluss die Prüfungsleistung ein (IDs, Note und Datum anpassen):

```powershell
python .\commands.py add-pruefung 1 1.3 2025-10-29
```

### Dashboard anzeigen
Starten Sie die grafische Oberfläche mit der passenden Studiengang-ID (z. B. `1`):

```powershell
python .\commands.py show 1
```

> Hinweis: Mit `python .\commands.py list` behalten Sie alle verfügbaren Studiengänge und IDs im Blick.

## 🪧 Weitere Hinweise
Sollten Sie das Dashboard, wie empfohlen, in einer virtuellen Umgebung nutzen, vergessen Sie nicht diese vor Aufruf eines Befehls zu aktivieren.
- `.\venv\Scripts\Activate.ps1`
