# 🛡️ IrsanAI SATA Secure Erase Tool

**Professional Grade Data Sanitization & Compliance Tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows/)

Ein fortschrittliches, Open-Source-Tool zur sicheren und unwiederbringlichen Löschung von Festplatten gemäß internationalen Standards (BSI, NIST, DoD). Entwickelt für IT-Profis, Administratoren und Datenschutzbeauftragte, die Transparenz und Compliance benötigen.

---

## 🚀 Features

### 🔐 Multi-Standard Löschung
Unterstützt die wichtigsten internationalen Löschstandards:
*   **BSI VS-A:** 3-Pass (0x00, 0xFF, Random) + Verifizierung. (Empfohlen für DSGVO-Konformität)
*   **NIST SP 800-88 Rev. 1 (Clear):** 1-Pass (0x00) + Verifizierung.
*   **DoD 5220.22-M:** 7-Pass (Komplexe Muster) + Verifizierung.

### 🎮 Immersive 3D Live-Visualisierung
Erleben Sie den Löschvorgang nicht nur als Ladebalken.
*   **Echtzeit-Daten:** Visualisiert den *tatsächlichen* Schreibfortschritt und I/O-Speed (via `psutil`).
*   **Head-Cam:** First-Person-View direkt vom virtuellen Schreibkopf.
*   **Live-Metriken:** Sektor-Tracking, Hex-Dump und Geschwindigkeits-Graph.

### 🛡️ Robust & Intelligent
*   **Smart Fallback:** Erkennt automatisch spezielle Hardware (z.B. verschlüsselte RAID-Controller), die direkten Low-Level-Zugriff verweigern, und wechselt nahtlos zu einer robusten Fallback-Methode (`diskpart`).
*   **Sicherheits-Checks:** Verhindert versehentliches Löschen der System-Festplatte.

### 📄 Audit-Ready Reporting
Generiert am Ende einen detaillierten HTML-Bericht:
*   **Compliance-Audit:** Ein integrierter Auditor prüft SOLL (Standard) vs. IST (Implementierung).
*   **Technische Details:** Genaue Auflistung aller durchgeführten Schritte, Zeiten und Muster.
*   **PDF-Export:** Professioneller Download für die Dokumentation.

---

## 🧠 Genesis & Development Philosophy: Powered by IrsanAI LRP

Dieses Projekt wurde nicht im luftleeren Raum entwickelt. Seine Entstehung wurde maßgeblich durch das **IrsanAI LRP (LLM Response Protocol)** beschleunigt und optimiert – ein Protokoll, das entwickelt wurde, um die Interaktion mit großen Sprachmodellen (LLMs) effizienter und zielgerichteter zu gestalten.

**Der Prozess:**
Anstatt mit einer allgemeinen Anfrage zu beginnen, wurde dem LLM zu Beginn ein reichhaltiger, voranalysierter Kontext über das Zielsystem zur Verfügung gestellt. Dies wurde durch das Skript `IrsanAI_OS_HW_Detector.py` (Teil dieses Repos) erreicht, das kritische Informationen über Betriebssystem, Hardware und verfügbare System-Tools sammelte.

**Die Vorteile dieses Ansatzes:**
*   **Höhere Effizienz:** Das LLM konnte von Anfang an präziseren und relevanteren Code generieren.
*   **Reduzierte Token-Nutzung:** Weniger Iterationen und Korrekturschleifen führten zu einem geringeren Gesamtverbrauch an Tokens.
*   **Nachweislich kleinerer CO2-Fußabdruck:** Durch die Reduzierung der Rechenlast auf Seiten des LLM-Anbieters wird der CO2-Fußabdruck des KI-gestützten Entwicklungsprozesses aktiv verringert.

Dieses Projekt ist somit ein praktisches Beispiel für die erfolgreiche Anwendung des IrsanAI LRP. Erfahren Sie mehr über das Protokoll:
*   **[IrsanAI LRP (Core Concept & v1.0)](https://github.com/pythonlover2023/IrsanAI-LRP)** - Die grundlegende Vision und erste Version.
*   **[IrsanAI LRP v1.3 (Advanced)](https://github.com/pythonlover2023/IrsanAI-LRP-v1.3)** - Die weiterentwickelte Version, die bei diesem Projekt zum Einsatz kam.

---

## 🛠️ Installation

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/pythonlover2023/Sata_Erase_Tool.git
    cd Sata_Erase_Tool
    ```

2.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Hauptsächlich `psutil` für die Live-I/O-Messung)*

---

## 💻 Nutzung

**WICHTIG:** Das Tool benötigt **Administrator-Rechte**, um direkten Zugriff auf die physischen Laufwerke zu erhalten.

1.  Starten Sie das Tool:
    ```bash
    python SATA_Secure_Erase_Tool_With_3D.py
    ```

2.  Folgen Sie den Anweisungen im Terminal:
    *   Wählen Sie die zu löschende Festplatte.
    *   Wählen Sie den gewünschten Lösch-Standard.
    *   Bestätigen Sie die Sicherheitsabfrage.
    *   Aktivieren Sie optional die 3D-Visualisierung.

3.  Nach Abschluss öffnet sich automatisch der detaillierte HTML-Report.

---

## 🗺️ Roadmap & Vision

Dieses Projekt befindet sich in aktiver Entwicklung. Unser Ziel ist es, das transparenteste und vertrauenswürdigste Open-Source-Löschtool zu schaffen.

### ✅ Implementiert (IST-Stand)
- [x] **Core Engine:** Eigene Python-Implementierung für direkten Sektor-Zugriff (`CoreWiper`).
- [x] **Multi-Pass:** Volle Unterstützung für BSI und DoD Muster.
- [x] **Verifizierung:** Byteweise Überprüfung der geschriebenen Daten.
- [x] **Visualisierung:** High-End 3D-Interface im Browser.
- [x] **Reporting:** Audit-Modul und PDF-Export.
- [x] **Robustheit:** Fallback-Logik für RAID/Spezial-Controller.

### 🚧 In Planung (SOLL-Stand)
- [ ] **ATA Secure Erase / NVMe Format:** Implementierung von nativen Firmware-Befehlen für SSDs (bisher wird "nur" überschrieben). Dies ist essenziell für das sichere Löschen moderner Flash-Speicher (NIST Purge).
- [ ] **Linux-Support:** Volle Portierung der Low-Level-Zugriffe für Linux-Systeme.
- [ ] **GUI:** Eine native grafische Oberfläche als Alternative zur Kommandozeile.
- [ ] **Zertifizierung:** Anstreben einer externen Prüfung (auch wenn aktuell "nur" technisch konform).

---

## ⚠️ Disclaimer

Dieses Tool wurde mit größter Sorgfalt entwickelt, um Daten sicher zu löschen.
*   **Haftung:** Die Nutzung erfolgt auf eigene Gefahr. Der Autor haftet nicht für Datenverlust (das ist ja der Zweck!) oder Schäden an Hardware.
*   **Zertifizierung:** Dieses Tool erstellt transparente Compliance-Reports, besitzt aber (noch) keine offizielle behördliche Zertifizierung (wie z.B. durch das BSI). Es setzt die technischen Anforderungen der Standards nach bestem Wissen und Gewissen um.

---

**Developed by IrsanAI**
*Open Source for a safer digital world.*
