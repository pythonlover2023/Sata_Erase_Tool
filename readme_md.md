# 🔒 IrsanAI SATA Secure Erase Tool v1.0

**DSGVO-konformes Festplatten-Lösch-Tool mit professionellem HTML-Reporting**

## ✨ Features

- ✅ **DSGVO+ konforme Löschung** nach BSI VS-A, NIST 800-88, DoD 5220.22-M
- 📊 **Professionelles HTML-Reporting** mit vollständiger Dokumentation
- 🔐 **Compliance-Nachweis** für Art. 17 DSGVO (Recht auf Löschung)
- 💾 **Automatische Festplatten-Erkennung** (SATA über USB-Gehäuse)
- 📋 **Detaillierte Protokollierung** aller Löschschritte
- 🎯 **Windows-optimiert** (diskpart, cipher)

## 🎯 Lösch-Standards

### 1. BSI VS-A (Empfohlen für DSGVO+)
- **3 Durchgänge**: Nullen → Einsen → Zufallsdaten
- **Deutscher Standard** für VS-A eingestufte Daten
- **Empfohlen für**: DSGVO personenbezogene Daten

### 2. NIST SP 800-88 Rev. 1
- **1 Durchgang**: Nullen
- **US-Standard** für nicht-klassifizierte Daten
- **Ausreichend für**: DSGVO Mindestanforderung

### 3. DoD 5220.22-M (7-Pass)
- **7 Durchgänge**: Mehrfache Überschreibungen
- **US-Militärstandard** (veraltet, aber oft gefordert)
- **Höchste Sicherheit**: Für sensible Regierungsdaten

## 📋 Voraussetzungen

### System
- **Windows 10/11** (mit Administrator-Rechten)
- **Python 3.11+**
- **Externes USB-Gehäuse** für SATA-Festplatten

### Tools (automatisch geprüft)
- `diskpart` ✅ (Windows integriert)
- `cipher` ✅ (Windows integriert)

## 🚀 Installation

### Schritt 1: Pakete installieren
```bash
pip install -r requirements.txt
```

### Schritt 2: System-Check durchführen
```bash
python IrsanAI_OS_HW_Detector.py
```

**Erwartete Ausgabe:**
```
✅ Administrator-Rechte OK
✅ diskpart verfügbar
✅ cipher verfügbar
✅ psutil installiert
```

## 💻 Verwendung

### Schritt 1: PyCharm als Administrator starten

1. **PyCharm schließen**
2. **Rechtsklick** auf PyCharm-Icon
3. **"Als Administrator ausführen"** wählen
4. **Projekt öffnen**

### Schritt 2: Festplatte anschließen

1. SATA-Festplatte in **externes USB-Gehäuse** einbauen
2. USB-Gehäuse an Laptop **anschließen**
3. Einschalten und warten bis Windows die Festplatte erkennt

### Schritt 3: Tool ausführen

```bash
python SATA_Secure_Erase_Tool.py
```

### Schritt 4: Interaktive Auswahl

Das Tool führt dich durch folgende Schritte:

1. **📀 Festplatten-Auswahl**
   ```
   [1] \\.\PHYSICALDRIVE2
       Modell: Samsung SSD 860 EVO
       Größe: 500 GB
   ```

2. **📋 Standard-Auswahl**
   ```
   [1] BSI VS-A (empfohlen)
   [2] NIST 800-88
   [3] DoD 5220.22-M
   ```

3. **⚠️ Sicherheitsbestätigung**
   ```
   Tippe 'JA LÖSCHEN' zum Bestätigen
   ```

4. **🚀 Löschvorgang**
   - Automatische Ausführung
   - Live-Fortschrittsanzeige
   - Detaillierte Protokollierung

5. **📄 Report-Generierung**
   - HTML-Report: `Secure_Erase_Report_YYYYMMDD_HHMMSS.html`
   - JSON-Backup: `Secure_Erase_Report_YYYYMMDD_HHMMSS.json`

## 📊 HTML-Report Inhalt

Der generierte Report enthält:

- ✅ **Zusammenfassung** aller gelöschten Festplatten
- 📋 **Detailliertes Protokoll** jedes Löschschritts
- 🔐 **Compliance-Informationen** (DSGVO Art. 17)
- 📅 **Zeitstempel** (Start, Ende, Dauer)
- 🎯 **Verwendete Standards** mit Beschreibung
- ✅ **Status** jeder einzelnen Festplatte

**Beispiel-Report:**
```
🔒 SATA Secure Erase Report
Erstellt am: 18.12.2025 um 15:45:30 Uhr

📊 Zusammenfassung:
   Gelöschte Festplatten: 3
   Erfolgreiche Löschungen: 3
   Verwendete Standards: BSI_VS_A
   Gesamtdauer: 1247.3s
```

## 🔐 DSGVO-Compliance

### Rechtliche Grundlage

- **Art. 17 DSGVO**: Recht auf Löschung
- **Art. 5 Abs. 2 DSGVO**: Rechenschaftspflicht
- **BSI Richtlinien**: Verschlusssache-Allgemein

### Mindestanforderungen (Stand Dezember 2025)

| Datenart | Mindeststandard | Empfohlen |
|----------|----------------|-----------|
| Personenbezogen | NIST 800-88 (1-Pass) | BSI VS-A (3-Pass) |
| Hochsensibel | BSI VS-A (3-Pass) | DoD 5220.22-M (7-Pass) |
| Normal | NIST 800-88 (1-Pass) | BSI VS-A (3-Pass) |

### Dokumentationspflicht

Der HTML-Report erfüllt die **Rechenschaftspflicht** gemäß Art. 5 Abs. 2 DSGVO:

- ✅ **Wann** wurde gelöscht (Zeitstempel)
- ✅ **Was** wurde gelöscht (Festplatten-ID)
- ✅ **Wie** wurde gelöscht (Standard, Durchgänge)
- ✅ **Status** der Löschung (erfolgreich/fehlgeschlagen)

## ⚠️ Wichtige Hinweise

### Limitierungen unter Windows

1. **Windows "clean all"** führt **1-Pass** durch (Nullen)
2. Für **Multi-Pass** (BSI 3x, DoD 7x) werden externe Tools benötigt:
   - **DBAN** (Darik's Boot and Nuke)
   - **Eraser** (Windows-GUI-Tool)
   - **shred/dd** (Linux Live-USB)

3. **Alternative**: Linux Live-USB mit `shred` oder `hdparm --security-erase`

### Was das Tool macht

✅ **Funktioniert:**
- Festplatten-Erkennung
- Admin-Rechte-Prüfung
- Windows "clean all" (1-Pass mit Nullen)
- Professionelles HTML-Reporting
- DSGVO-konforme Dokumentation

⚠️ **Limitation:**
- Multi-Pass (BSI 3x, DoD 7x) erfordert externe Tools
- Das Tool dokumentiert dies transparent im Report

### Empfehlung für höchste Sicherheit

Für **BSI VS-A (3-Pass)** oder **DoD (7-Pass)**:

1. **Option A**: Linux Live-USB verwenden
   ```bash
   # BSI 3-Pass mit shred
   sudo shred -vfz -n 3 /dev/sdX
   
   # DoD 7-Pass mit shred
   sudo shred -vfz -n 7 /dev/sdX
   ```

2. **Option B**: DBAN bootfähiger USB
   - Download: https://dban.org/
   - Bootet direkt von USB
   - Unterstützt alle Standards

3. **Option C**: Dieses Tool + manuelle Verifikation
   - Nutze dieses Tool für Reporting
   - Führe zusätzlich DBAN/Linux aus
   - Dokumentiere beide Vorgänge

## 🛠️ Troubleshooting

### "Keine Festplatten gefunden"

**Lösung:**
1. Überprüfe USB-Verbindung
2. Öffne **Datenträgerverwaltung** (diskmgmt.msc)
3. Prüfe ob Windows die Festplatte sieht
4. Stelle sicher, dass das USB-Gehäuse eingeschaltet ist

### "Administrator-Rechte erforderlich"

**Lösung:**
1. PyCharm **schließen**
2. **Rechtsklick** auf PyCharm → "Als Administrator ausführen"
3. Projekt neu öffnen
4. Script erneut ausführen

### "psutil fehlt"

**Lösung:**
```bash
pip install psutil
```

### "Disk not found in diskpart"

**Lösung:**
1. Disk-Nummer manuell prüfen: `diskpart → list disk`
2. Tool mit korrekter Disk-Nummer starten
3. Überprüfe ob Festplatte schreibgeschützt ist

## 📝 Beispiel-Workflow

```bash
# 1. System-Check
python IrsanAI_OS_HW_Detector.py

# 2. Hauptprogramm starten (als Admin!)
python SATA_Secure_Erase_Tool.py

# 3. Interaktive Auswahl
#    - Standard wählen: [1] BSI VS-A
#    - Festplatten wählen: 1,2,3
#    - Bestätigen: JA LÖSCHEN

# 4. Report öffnen
#    HTML-Report wird automatisch generiert
#    Optional: Automatisch im Browser öffnen

# 5. Festplatten übergeben
#    Mit HTML-Report als Compliance-Nachweis
```

## 📄 Dateien im Projekt

```
sata-erase/
├── IrsanAI_OS_HW_Detector.py       # System-Check
├── SATA_Secure_Erase_Tool.py       # Hauptprogramm
├── requirements.txt                 # Dependencies
├── README.md                        # Diese Datei
├── pyproject.toml                   # Projekt-Config
├── irsanai_detection.json          # System-Info (generiert)
└── Secure_Erase_Report_*.html      # Reports (generiert)
```

## 🔗 Standards-Referenzen

- **BSI**: https://www.bsi.bund.de/
- **NIST SP 800-88**: https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final
- **DSGVO**: https://dsgvo-gesetz.de/
- **DoD 5220.22-M**: (veraltet, durch NIST ersetzt)

## 💡 Best Practices

1. ✅ **Immer BSI VS-A** für personenbezogene Daten
2. ✅ **HTML-Report aufbewahren** (Rechenschaftspflicht)
3. ✅ **Festplatten vorher testen** (SMART-Status prüfen)
4. ✅ **Mehrere Festplatten gleichzeitig** verarbeiten
5. ✅ **JSON-Backup zusätzlich** speichern

## ⚖️ Rechtlicher Hinweis

Dieses Tool dient als **Compliance-Hilfe** für DSGVO Art. 17. Es ersetzt keine Rechtsberatung. Bei rechtlichen Fragen konsultiere einen Fachanwalt für IT-Recht.

---

**IrsanAI SATA Secure Erase Tool v1.0**  
Erstellt: 18.12.2025  
Lizenz: MIT  
Autor: IrsanAI