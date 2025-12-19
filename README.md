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

Dieses Projekt ist somit ein praktisches Beispiel für die erfolgreiche Anwendung des IrsanAI LRP. Erfahren Sie mehr über das Protokoll und testen Sie es live:
*   **IrsanAI LRP (Core Concept & v1.0):**
    *   [View on GitHub](https://github.com/pythonlover2023/IrsanAI-LRP)
    *   [🚀 Use IrsanAI LRP v1.0 - LIVE](https://pythonlover2023.github.io/IrsanAI-LRP/)
*   **IrsanAI LRP v1.3 (Advanced):**
    *   [View on GitHub](https://github.com/pythonlover2023/IrsanAI-LRP-v1.3)
    *   [🚀 Use IrsanAI LRP v1.3 - LIVE](https://pythonlover2023.github.io/IrsanAI-LRP-v1.3/)

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

Dieses Projekt befindet sich in aktiver Entwicklung mit dem Ziel, das transparenteste und vertrauenswürdigste Open-Source-Löschtool zu schaffen. Der Fokus liegt auf technischer Exzellenz und nachvollziehbarer Sicherheit.

### 🚧 In Planung (Nächste Schritte)
- [ ] **Priorität 1: SSD-spezifische Löschmethoden:** Implementierung von nativen Firmware-Befehlen wie **ATA Secure Erase** und **NVMe Sanitize**. Dies ist die von Herstellern und Standards (NIST Purge) empfohlene Methode für das sichere Löschen von SSDs und umgeht Probleme wie Wear-Leveling.
- [ ] **Erweiterung der Plattform-Unterstützung:** Vollständige Portierung und Testung der Low-Level-Zugriffe für **Linux** und **macOS**.
- [ ] **Erweiterte Test-Suite:** Aufbau einer automatisierten Test-Suite, die verschiedene Löschszenarien in Simulations-Modi durchspielt, um die Korrektheit der Implementierung kontinuierlich zu validieren.
- [ ] **Native GUI:** Entwicklung einer einfachen, plattformunabhängigen grafischen Benutzeroberfläche (z.B. mit Tkinter oder PyQt) als Alternative zur Kommandozeile.
- [ ] **Verbesserte Report-Sicherheit:** Integration von Hash-Ketten oder digitalen Signaturen in den Compliance-Report, um dessen Integrität nachträglich überprüfbar zu machen.

---

## ⚠️ Disclaimer

Dieses Tool wurde mit größter Sorgfalt entwickelt, um Daten sicher und nachvollziehbar zu löschen. Dennoch gelten folgende Hinweise:

*   **Haftung:** Die Nutzung erfolgt auf eigene Gefahr. Der Autor haftet nicht für Datenverlust oder mögliche Schäden an Hardware.
*   **Zertifizierung & Garantie:** Dieses Tool ist **nicht offiziell durch eine Behörde** (wie das BSI oder den TÜV) zertifiziert. Es wurde entwickelt, um die technischen Spezifikationen der genannten Standards nach bestem Wissen und Gewissen umzusetzen. Der generierte Report dient als technisches Protokoll und nicht als rechtsgültiges Zertifikat. Für Audits, bei denen eine formale Zertifizierung der Software zwingend vorgeschrieben ist, wird der Einsatz kommerzieller, zertifizierter Lösungen empfohlen.
*   **Vertrauen durch Transparenz:** Der Wert dieses Projekts liegt in seinem Open-Source-Charakter. Jeder kann den Code einsehen, prüfen und verbessern. Vertrauen wird hier durch maximale Transparenz geschaffen, nicht durch ein teures Zertifikat.

---

**Developed by IrsanAI**
*Open Source for a safer digital world.*
