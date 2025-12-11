from datetime import date, timedelta, datetime, timezone
from typing import Optional, List, Dict

class Pruefungsleistung:
    """
    Diese Klasse repräsentiert eine Prüfungsleistung mit den Attributen Note und Datum.
    Es ist die tiefste Ebene im Datenmodell und hat keine Unterklassen.
    Die Prüfungsleistung ist genau einem Modul zugeordnet.
    """
    def __init__(self, note: float, datum: date):
        """Initialisiert die Klasse Pruefungsleistung und definiert die Attribute."""
        # Attribute
        self.__note: float = note
        self.__datum: date = datum

    @property
    def note(self) -> float:
        """Gibt die Note der Prüfungsleistung zurück."""
        return self.__note

    @property
    def datum(self) -> date:
        """Gibt das Datum der Prüfungsleistung zurück."""
        return self.__datum

class Modul:
    """
    Diese Klasse repräsentiert ein Modul mit den Attributen Name, ECTS und Startdatum.
    Es ist die zweite Ebene im Datenmodell und hat die Klasse Pruefungsleistung als Unterklasse.
    Ein Modul kann genau eine Prüfungsleistung erzeugen und verwalten.
    """
    def __init__(self, name: str, ects: int, startdatum: Optional[date] = None):
        """Initialisiert die Klasse Modul und legt die kompositionsgebundene Prüfungsleistung an."""
        # Attribute
        self.__name: str = name
        self.__ects: int = ects
        self.__startdatum: Optional[date] = startdatum

        # Komposition
        self.__pruefungsleistung: Optional[Pruefungsleistung] = None

    @property
    def name(self) -> str:
        """Gibt den Namen des Moduls zurück."""
        return self.__name

    @property
    def ects(self) -> int:
        """Gibt die ECTS-Credits des Moduls zurück."""
        return self.__ects

    @property
    def startdatum(self) -> Optional[date]:
        """Gibt das Startdatum des Moduls zurück."""
        return self.__startdatum

    def setPruefungsleistung(self, note: float, datum: date) -> None:
        """
        Erstellt und weist die Prüfungsleistung zu einem bestehenden Modul zu.
        Diese Methode hat keinen Rückgabewert.
        """
        self.__pruefungsleistung = Pruefungsleistung(note, datum)

    def removePruefungsleistung(self) -> None:
        """Entfernt die Prüfungsleistung und gibt die Kompositionsressource frei."""
        self.__pruefungsleistung = None

    def hasPruefungsleistung(self) -> bool:
        """Prüft, ob das Modul eine Prüfungsleistung besitzt."""
        return self.__pruefungsleistung is not None

    @property
    def pruefungsleistung(self) -> Optional[Pruefungsleistung]:
        """Gibt die zugehörige Prüfungsleistung zurück."""
        return self.__pruefungsleistung

    def berechneBenoetigteTage(self) -> Optional[int]:
        """
        Berechnet die Zeitdauer in Tagen, welche für das erfolgreiche Abschließen des Moduls benötigt wurde.
        """
        pruefungsleistung = self.__pruefungsleistung

        if pruefungsleistung is None or self.__startdatum is None:
            return None

        if pruefungsleistung.datum < self.__startdatum:
            return None

        time_delta: timedelta = pruefungsleistung.datum - self.__startdatum

        return time_delta.days

class Studiengang:
    """
    Diese Klasse repräsentiert einen Studiengang mit den Attributen Name, Regelstudienzeit und Gesamt-ECTS.
    Es ist die höchste Ebene im Datenmodell und hat die Klasse Modul als Unterklasse.
    Ein Studiengang kann mehrere Module beinhalten.
    """
    def __init__(self, name: str, regelstudienzeit: int, ects_gesamt: int, startdatum: date):
        """Initialisiert die Klasse Studiengang und definiert die Attribute."""
        # Attribute
        self.__name: str = name
        self.__regelstudienzeit: int = regelstudienzeit
        self.__ects_gesamt: int = ects_gesamt
        self.__startdatum: date = startdatum

        # Assoziation
        self._module_list: List[Modul] = []
    
    @property
    def name(self) -> str:
        """Gibt den Namen des Studiengangs zurück."""
        return self.__name

    @property
    def ects_gesamt(self) -> int:
        """Gibt die Gesamt-ECTS des Studiengangs zurück."""
        return self.__ects_gesamt
    @property
    def regelstudienzeit(self) -> int:
        """Gibt die Regelstudienzeit in Semestern zurück."""
        return self.__regelstudienzeit

    @property
    def startdatum(self) -> date:
        """Gibt das Startdatum des Studiengangs zurück."""
        return self.__startdatum

    @property
    def module_list(self) -> List[Modul]:
        """Gibt die Liste der Module des Studiengangs zurück."""
        return self._module_list

    def addModul(self, modul: Modul) -> None:
        """Fügt ein Modul zum Studiengang hinzu.
        Diese Methode hat keinen Rückgabewert.
        """
        self._module_list.append(modul)

    def berechneErreichteECTS(self) -> int:
        """
        Berechnet die erreichten ECTS-Credits des Studiengangs.
        Ein Prüfungsleistung-Objekt existiert nur, wenn das Modul erfolgreich abgeschlossen wurde, daher muss keine Prüfung der Note stattfinden.
        """
        erreichte__ects: int = 0
        # Iteriere über alle Module des Studiengangs und addiere die ECTS-Credits der erfolgreich abgeschlossenen Module.
        for modul in self._module_list:
            if modul.hasPruefungsleistung():
                erreichte__ects += modul.ects
        return erreichte__ects

    def berechneTageProModulRichtwert(self, datum: date = datetime.now(timezone.utc).date()) -> float:
        """
        Berechnet den dynamischen Tage-pro-Modul-Richtwert, welcher auf Basis der verbleibenden Tage bis zum Erreichen der Regelstudienzeit und den verbleibenden
        ECTS-Credits zum Abschließen des Studiums ermittelt, wie viele Tage durchschnittlich pro Modul
        aufgewendet werden können, um das Studium in der Regelstudienzeit abzuschließen.

        Die Berechnung berücksichtigt folgende Variablen und Parameter:
        - Regelstudienzeit (z.B. 8 Semester)
        - ECTS-Zielwert (z.B. 180 ECTS)
        - Eingeplanter Urlaub (z.B. 6 Wochen pro Jahr)
        - Aktuelles Datum
        """
        TAGE_PRO_JAHR = 365.25
        SEMESTER_PRO_JAHR = 2
        URLAUBSTAGE_PRO_JAHR = 6 * 7
        ECTS_CREDITS_PRO_MODUL_BEZUGSWERT = 5

        # Schritt 1: Netto-Studientage über gesamte Studienlaufzeit ermitteln
        gesamt_studium_tag = (self.__regelstudienzeit * (TAGE_PRO_JAHR / SEMESTER_PRO_JAHR))
        gesamt_urlaub_tage = (self.__regelstudienzeit * (URLAUBSTAGE_PRO_JAHR / SEMESTER_PRO_JAHR))
        gesamt_netto_tage = gesamt_studium_tag - gesamt_urlaub_tage
        
        
        # Schritt 2: Verbleibende Tage und verbleibende ECTS ermitteln
        # A: Verbleibende Tage
        verstrichene_dauer: timedelta = datum - self.__startdatum
        verstrichene_tage = verstrichene_dauer.days
        
        verbleibende_tage = gesamt_netto_tage - verstrichene_tage
        
        # B: Austehende ECTS-Credits
        erreichte__ects = self.berechneErreichteECTS()
        ausstehende__ects = self.__ects_gesamt - erreichte__ects
        
        
        # Schritt 3: Logiküberprüfung
        # A: Ziel bereits erreicht
        if ausstehende__ects <= 0:
            return 0.0
        # B: Keine verbleibende Zeit mehr
        if verbleibende_tage <= 0:
            return 999.0
            
        # Schritt 4: Berechnung des Richtwert pro 1-ECTS-Credit
        richtwert_pro__ects = verbleibende_tage / ausstehende__ects
        
        # Schritt 5: Normalisierung auf den ECTS-Credits Bezugswert
        richtwert_bezugswert = richtwert_pro__ects * ECTS_CREDITS_PRO_MODUL_BEZUGSWERT
        
        return round(richtwert_bezugswert, 2)


    def berechneNotendurchschnitt(self) -> Optional[float]:
        """
        Berechnet den aktuellen, nach ECTS gewichteten Notendurchschnitt über alle abgeschlossenen Module eines Studiengangs.
        """
        ects_kumuliert: float = 0.0
        gewichtete__notensumme_kumuliert: float = 0.0

        for modul in self._module_list:
            # Prüfen, ob das Modul abgeschlossen ist (Prüfungsleistung existiert)
            pruefungsleistung = modul.pruefungsleistung
            if pruefungsleistung:
                note = pruefungsleistung.note
                ects = modul.ects
                # Kumuliere die Gesamtanzahl an ECTS-Credits und gewichteter Notensumme
                ects_kumuliert += ects
                gewichtete__notensumme_kumuliert += note * ects

        if ects_kumuliert == 0:
            return None

        # Die über alle Module hinweg kumulierten Endwerte zu einem aktuellen, gewichteten Notendurchschnitt berechnen
        notendurchschnitt = gewichtete__notensumme_kumuliert / ects_kumuliert
        
        return round(notendurchschnitt, 2)

    
    def berechneNotendurchschnittVerlauf(self) -> List[float]:
        """
        Berechnet den Verlauf des Notendurchschnitts eines Studiengangs.
        Gibt eine Liste mit den nach ECTS gewichteten Notendurchschnitten je Anzahl abgeschlossener Module zurück.
        Beispiel: Der Studierende hat bereits drei 5-ECTS Module mit den Noten 1.0, 2.0 und 3.0 abgeschlossen. Die Datumsreihenfolge der Prüfungsleistungen ist dabei v.l.n.r.
        Die Funktion berechnet nun den Notendurchschnitt pro abgeschlossener Klausur, d.h. drei Werte und gibt jeweils pro Wert den Durchschnitt aus.  
        Output: [1.0, 1.5, 2.0]
        """
        # Schritt 1: Abgeschlossene Module ermitteln und Datenaufbereitung
        abgeschlossene_module: List[Dict] = []

        for modul in self._module_list:
            pruefungsleistung = modul.pruefungsleistung
            if pruefungsleistung:
                abgeschlossene_module.append({
                    'abschlussdatum': pruefungsleistung.datum,
                    'note': pruefungsleistung.note,
                    'ects': modul.ects,
                })
        
        if not abgeschlossene_module:
            return []
        # Ältestes Abschlussdatum zuerst - Aufsteigend sortieren
        abgeschlossene_module.sort(key=lambda m: m['abschlussdatum'])

        # Schritt 2: Kumulative Berechnung
        notendurchschnitt_verlauf: List[float] = []
        notendurchschnitt_kumuliert: float = 0.0
        ects_kumuliert: float = 0.0
        gewichtete__notensumme_kumuliert: float = 0.0

        for modul in abgeschlossene_module:
            note = modul['note']
            ects = modul['ects']

            ects_kumuliert += ects
            gewichtete__notensumme_kumuliert += note * ects
            notendurchschnitt_kumuliert = gewichtete__notensumme_kumuliert / ects_kumuliert

            notendurchschnitt_verlauf.append(round(notendurchschnitt_kumuliert,2))
        
        return notendurchschnitt_verlauf

        