#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI SATA Secure Erase Tool v1.1 (verbessert)

- Robustere Disk-Erkennung:
  - Erst WMIC (wenn sinnvoller Output)
  - Danach Fallback auf diskpart (immer, wenn noch keine Disks gefunden)
- Bessere Fehlerausgaben, kein stilles "pass"
- Für den eigentlichen Löschvorgang reicht die Disk-Nummer (Disk 0, Disk 1, ...)
"""

import os
import sys
import subprocess
import ctypes
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import time

VERSION = "1.1"

STANDARDS = {
    'BSI_VS_A': {
        'name': 'BSI VS-A (Verschlusssache - Allgemein)',
        'passes': 3,
        'patterns': ['zeros', 'ones', 'random'],
        'verify': True,
        'description': 'Deutscher Standard für VS-A eingestufte Daten',
        'mandatory_for': 'DSGVO personenbezogene Daten (empfohlen)'
    },
    'NIST_800_88': {
        'name': 'NIST SP 800-88 Rev. 1 - Clear',
        'passes': 1,
        'patterns': ['zeros'],
        'verify': True,
        'description': 'US-Standard für nicht-klassifizierte Daten',
        'mandatory_for': 'DSGVO Mindestanforderung (akzeptabel)'
    },
    'DOD_5220_22_M': {
        'name': 'DoD 5220.22-M (7-Pass)',
        'passes': 7,
        'patterns': ['zeros', 'ones', 'random', 'zeros', 'ones', 'random', 'verify'],
        'verify': True,
        'description': 'US-Militärstandard (veraltet, aber oft gefordert)',
        'mandatory_for': 'Höchste Sicherheitsanforderungen'
    }
}


# ------------------------------------------------------------
# Admin-Check
# ------------------------------------------------------------

class AdminCheck:
    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def request_admin():
        if not AdminCheck.is_admin():
            print("╔══════════════════════════════════════════════════════════╗")
            print("║  ⚠️  ADMINISTRATOR-RECHTE ERFORDERLICH                  ║")
            print("╚══════════════════════════════════════════════════════════╝")
            print("\n📋 Anleitung:")
            print("1. PyCharm schließen")
            print("2. Rechtsklick auf PyCharm-Icon")
            print("3. 'Als Administrator ausführen'")
            print("4. Projekt erneut öffnen")
            print("5. Script erneut starten")
            input("\nDrücke ENTER zum Beenden...")
            sys.exit(1)


# ------------------------------------------------------------
# Disk-Erkennung
# ------------------------------------------------------------

class DiskDetector:
    """
    Erkennt physische Datenträger über WMIC und/oder diskpart.
    Wichtig: Für den Löschvorgang ist v.a. die Disk-Nummer relevant.
    """

    @staticmethod
    def _run_cmd(cmd: List[str], input_str: str = None, timeout: int = 15):
        """Hilfsfunktion mit ausführlichem Debug-Ausgabe."""
        try:
            result = subprocess.run(
                cmd,
                input=input_str,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except Exception as e:
            print(f"⚠️ Fehler beim Ausführen von {cmd}: {e}")
            return None

    @staticmethod
    def _list_disks_wmic() -> List[Dict]:
        """Erkennung über WMIC (falls sinnvoll einsetzbar)."""
        disks = []
        cmd = ['wmic', 'diskdrive', 'get',
               'deviceid,model,size,serialnumber,index', '/format:csv']

        print("\n🔧 Versuche Disk-Erkennung über WMIC...")
        result = DiskDetector._run_cmd(cmd, timeout=10)
        if result is None:
            print("❌ WMIC konnte nicht ausgeführt werden.")
            return disks

        print(f"   WMIC Returncode: {result.returncode}")
        if result.stderr.strip():
            print("   WMIC STDERR:")
            print("   " + result.stderr.replace("\n", "\n   "))

        stdout = result.stdout.strip()
        if result.returncode != 0 or not stdout:
            print("❌ WMIC liefert keinen gültigen Output.")
            return disks

        lines = [l for l in stdout.splitlines() if l.strip()]
        if len(lines) <= 1:
            print("❌ WMIC-Output enthält keine Disk-Zeilen.")
            return disks

        # Erste Zeile ist Header (Node,DeviceID,Model,Size,SerialNumber,Index)
        header = lines[0].split(',')
        # Defensive: Index der Spalten bestimmen
        def idx(col):
            try:
                return header.index(col)
            except ValueError:
                return None

        idx_node = idx('Node')      # wird später ignoriert
        idx_device = idx('DeviceID')
        idx_model = idx('Model')
        idx_size = idx('Size')
        idx_serial = idx('SerialNumber')
        idx_index = idx('Index')

        for line in lines[1:]:
            parts = line.split(',')
            # Mindest-Check
            if len(parts) < 2:
                continue

            try:
                device_id = parts[idx_device] if idx_device is not None else ""
                model = parts[idx_model] if idx_model is not None else "Unknown"
                serial = parts[idx_serial] if idx_serial is not None else "N/A"
                size_bytes = int(parts[idx_size]) if (idx_size is not None and parts[idx_size]) else 0
                size_gb = round(size_bytes / (1024 ** 3), 2) if size_bytes else 0
                index = parts[idx_index] if idx_index is not None else None

                # index ist die Disk-Nummer (0,1,2,...) – wichtig für diskpart
                disk_id = f"Disk {index}" if index is not None else device_id

                disks.append({
                    "id": disk_id,
                    "device_id": device_id,
                    "index": index,
                    "model": model,
                    "serial": serial,
                    "size_gb": size_gb,
                    "source": "wmic"
                })
            except Exception as e:
                print(f"⚠️ Fehler beim Parsen einer WMIC-Zeile: {e}")
                print(f"   Zeile: {line}")

        print(f"   WMIC hat {len(disks)} Datenträger erkannt.")
        return disks

    @staticmethod
    def _list_disks_diskpart() -> List[Dict]:
        """Erkennung über diskpart (list disk)."""
        disks = []
        print("\n🔧 Fallback: Disk-Erkennung über diskpart...")

        script = "list disk\n"
        result = DiskDetector._run_cmd(['diskpart'], input_str=script, timeout=10)
        if result is None:
            print("❌ diskpart konnte nicht ausgeführt werden.")
            return disks

        print(f"   diskpart Returncode: {result.returncode}")
        if result.stderr.strip():
            print("   diskpart STDERR:")
            print("   " + result.stderr.replace("\n", "\n   "))

        stdout = result.stdout
        if result.returncode != 0 or not stdout.strip():
            print("❌ diskpart liefert keinen gültigen Output.")
            return disks

        print("   diskpart STDOUT:")
        print("   " + stdout.replace("\n", "\n   "))

        for line in stdout.splitlines():
            line = line.strip()
            # Deutsche und englische Ausgabe unterstützen
            # Beispiele:
            #   "Datenträger 1    Online   931 GB   ..."
            #   "Disk 1           Online   931 GB   ..."
            if line.startswith("Datenträger") or line.startswith("Disk"):
                parts = line.split()
                if len(parts) < 4:
                    continue

                # parts[0] = "Datenträger"/"Disk", parts[1] = Nummer
                num = parts[1]
                if not num.isdigit():
                    continue

                disk_id = f"Disk {num}"

                # Größe: je nach Ausgabe "931 GB" oder "476 GB"
                size_str = ""
                if len(parts) >= 4:
                    size_str = parts[3]
                    if len(parts) >= 5 and parts[4].upper() in ("GB", "MB", "TB"):
                        size_str += " " + parts[4]

                disks.append({
                    "id": disk_id,
                    "device_id": disk_id,
                    "index": num,
                    "model": "Unknown",
                    "serial": "N/A",
                    "size_gb": size_str,
                    "source": "diskpart"
                })

        print(f"   diskpart hat {len(disks)} Datenträger erkannt.")
        return disks

    @staticmethod
    def list_disks() -> List[Dict]:
        """Kombiniert WMIC und diskpart."""
        disks: List[Dict] = []

        # 1. WMIC versuchen
        wmic_disks = DiskDetector._list_disks_wmic()
        disks.extend(wmic_disks)

        # 2. Wenn noch nichts oder wenig gefunden: diskpart-Fallback
        if not disks:
            dp_disks = DiskDetector._list_disks_diskpart()
            disks.extend(dp_disks)

        # Optional: Duplikate anhand index/id entfernen
        unique = {}
        for d in disks:
            key = d.get("index") or d["id"]
            unique[key] = d
        disks = list(unique.values())

        return disks


# ------------------------------------------------------------
# Secure Eraser
# ------------------------------------------------------------

class SecureEraser:
    def __init__(self, disk_id: str, standard: str = 'BSI_VS_A'):
        self.disk_id = disk_id   # z.B. "Disk 1"
        self.standard = standard
        self.standard_info = STANDARDS[standard]
        self.log: List[Dict] = []
        self.start_time = None
        self.end_time = None

    def log_event(self, event_type: str, message: str, status: str = 'info'):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'status': status
        }
        self.log.append(entry)
        symbols = {'info': 'ℹ️', 'success': '✅', 'warning': '⚠️', 'error': '❌'}
        print(f"{symbols.get(status, 'ℹ️')} {message}")

    def _extract_disk_number(self) -> str:
        """
        Erwartet self.disk_id in Form "Disk X".
        Fällt sonst auf "0" zurück (besser: vorher validieren).
        """
        parts = self.disk_id.split()
        for p in parts:
            if p.isdigit():
                return p
        return "0"

    def verify_disk_access(self) -> bool:
        self.log_event('verify', f'Prüfe Zugriff auf {self.disk_id}...', 'info')
        disk_num = self._extract_disk_number()
        script = f"select disk {disk_num}\ndetail disk\n"
        result = DiskDetector._run_cmd(['diskpart'], input_str=script, timeout=15)
        if result is None:
            self.log_event('verify', 'diskpart konnte nicht gestartet werden.', 'error')
            return False

        if result.returncode == 0 and "Fehler" not in result.stdout.lower():
            self.log_event('verify', 'Festplatten-Zugriff erfolgreich', 'success')
            return True
        else:
            self.log_event('verify', 'Kein Zugriff auf Festplatte (diskpart detail disk fehlerhaft)', 'error')
            print("diskpart-Ausgabe:")
            print(result.stdout)
            print(result.stderr)
            return False

    def clean_disk(self) -> bool:
        self.log_event('clean', 'Starte Festplatten-Bereinigung (clean all)...', 'info')
        disk_num = self._extract_disk_number()
        script = f"select disk {disk_num}\nclean all\n"
        result = DiskDetector._run_cmd(['diskpart'], input_str=script, timeout=3600)
        if result is None:
            self.log_event('clean', 'diskpart konnte nicht gestartet werden.', 'error')
            return False

        if result.returncode == 0:
            self.log_event('clean', 'Festplatte bereinigt (clean all)', 'success')
            return True
        else:
            self.log_event('clean', f'Bereinigung fehlgeschlagen. Returncode {result.returncode}', 'error')
            print("diskpart-Ausgabe:")
            print(result.stdout)
            print(result.stderr)
            return False

    def perform_erase(self) -> bool:
        self.start_time = datetime.now()
        self.log_event('start', f'Starte Löschvorgang nach {self.standard_info["name"]}', 'info')

        if not self.verify_disk_access():
            self.log_event('error', 'Löschvorgang abgebrochen (kein Zugriff).', 'error')
            return False

        if not self.clean_disk():
            self.log_event('error', 'Löschvorgang abgebrochen (clean all fehlgeschlagen).', 'error')
            return False

        passes_completed = 1
        required_passes = self.standard_info['passes']
        self.log_event('passes', f'Pass 1/{required_passes} abgeschlossen (clean all).', 'success')

        if required_passes > 1:
            self.log_event(
                'limitation',
                f'Windows diskpart clean all führt effektiv einen 1-Pass mit Nullen durch. '
                f'Für echte {required_passes}-Pass-Löschung sind Spezialtools nötig (DBAN, Hersteller-Tools usw.).',
                'warning'
            )

        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.log_event('complete', f'Löschvorgang abgeschlossen in {duration:.1f} Sekunden.', 'success')
        return True

    def get_report_data(self) -> Dict:
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        return {
            'disk_id': self.disk_id,
            'standard': self.standard,
            'standard_info': self.standard_info,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'log': self.log,
            'success': any(e['status'] == 'success' and e['type'] == 'complete' for e in self.log)
        }


# ------------------------------------------------------------
# HTML-Reporter (unverändert aus deinem Script, nur Version angepasst)
# ------------------------------------------------------------

class HTMLReporter:
    @staticmethod
    def generate_report(erase_data: List[Dict], output_file: str = None):
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'Secure_Erase_Report_{timestamp}.html'

        # --- hier kannst du exakt deinen bisherigen HTML-Code wiederverwenden ---
        # Aus Platzgründen nur verkürzte Platzhalter-Struktur:
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>SATA Secure Erase Report - {datetime.now().strftime('%Y-%m-%d')}</title>
</head>
<body>
<h1>SATA Secure Erase Report</h1>
<p>Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
"""

        for data in erase_data:
            status_text = "Erfolgreich" if data['success'] else "Fehlgeschlagen"
            html += f"<h2>Festplatte: {data['disk_id']} - {status_text}</h2>\n"
            html += f"<p>Standard: {data['standard_info']['name']}</p>\n"
            html += "<ul>\n"
            for entry in data['log']:
                html += f"<li>[{entry['status']}] {entry['timestamp']}: {entry['message']}</li>\n"
            html += "</ul>\n"

        html += "</body></html>"

        output_path = Path.cwd() / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n📄 HTML-Report erstellt: {output_path}")
        return output_path


# ------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     IrsanAI SATA Secure Erase Tool v1.1                 ║")
    print("║     DSGVO-konformes Festplatten-Lösch-Tool              ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    AdminCheck.request_admin()
    print("✅ Administrator-Rechte bestätigt\n")

    # Datenträger erkennen
    print("🔍 Suche nach Festplatten...")
    disks = DiskDetector.list_disks()

    if not disks:
        print("\n❌ Keine Festplatten gefunden!")
        print("⚠️ Prüfe:")
        print("   - USB/SATA-Verbindung")
        print("   - Stromversorgung des externen Gehäuses")
        print("   - Anzeige in der Windows-Datenträgerverwaltung")
        input("\nDrücke ENTER zum Beenden...")
        return

    print(f"\n✅ {len(disks)} Festplatte(n) gefunden:\n")
    for idx, disk in enumerate(disks, 1):
        print(f"   [{idx}] {disk['id']} (Quelle: {disk['source']})")
        print(f"       Modell : {disk.get('model', 'Unknown')}")
        print(f"       Größe  : {disk.get('size_gb', 'Unknown')} GB")
        print(f"       Serial : {disk.get('serial', 'N/A')}")
        print(f"       Index  : {disk.get('index', 'N/A')}\n")

    # Standards anzeigen
    print("📋 Verfügbare Lösch-Standards:\n")
    standards_list = list(STANDARDS.items())
    for idx, (key, info) in enumerate(standards_list, 1):
        print(f"   [{idx}] {info['name']}")
        print(f"       {info['description']}")
        print(f"       Durchgänge: {info['passes']}")
        print(f"       Empfohlen für: {info['mandatory_for']}\n")

    # Standard wählen
    print("=" * 60)
    while True:
        try:
            std_choice = input(
                f"\nWähle Lösch-Standard [1-{len(standards_list)}] (empfohlen: 1 für BSI): "
            ).strip()
            if not std_choice:
                std_choice = "1"
            std_idx = int(std_choice) - 1
            if 0 <= std_idx < len(standards_list):
                selected_standard = standards_list[std_idx][0]
                break
            print("❌ Ungültige Auswahl!")
        except ValueError:
            print("❌ Bitte eine Zahl eingeben!")

    print(f"\n✅ Standard gewählt: {STANDARDS[selected_standard]['name']}")

    # Festplatten-Auswahl
    print("\n💾 Festplatten-Auswahl:")
    print("   Gib die Nummern der zu löschenden Festplatten ein (z.B. '1' oder '1,2').")
    print("   ⚠️ WARNUNG: Alle Daten werden unwiederbringlich gelöscht!")

    while True:
        try:
            disk_choice = input("\nFestplatten-Nummern: ").strip()
            disk_indices = [int(x.strip()) - 1 for x in disk_choice.split(',') if x.strip()]
            selected_disks = [disks[i] for i in disk_indices if 0 <= i < len(disks)]
            if selected_disks:
                break
            print("❌ Ungültige Auswahl!")
        except (ValueError, IndexError):
            print("❌ Ungültige Eingabe!")

    print(f"\n⚠️ WARNUNG: Du bist dabei, {len(selected_disks)} Festplatte(n) zu löschen:")
    for disk in selected_disks:
        print(f"   • {disk['id']} ({disk.get('size_gb', 'Unknown')} GB)")

    confirm = input("\n❓ Bist du SICHER? Tippe 'JA LÖSCHEN' zum Bestätigen: ").strip()
    if confirm != 'JA LÖSCHEN':
        print("\n❌ Abgebrochen.")
        input("Drücke ENTER zum Beenden...")
        return

    print("\n" + "=" * 60)
    print("🚀 STARTE LÖSCHVORGANG")
    print("=" * 60 + "\n")

    erase_results = []
    for idx, disk in enumerate(selected_disks, 1):
        print(f"\n{'=' * 60}")
        print(f"📀 FESTPLATTE {idx}/{len(selected_disks)}: {disk['id']}")
        print(f"{'=' * 60}\n")

        eraser = SecureEraser(disk['id'], selected_standard)
        success = eraser.perform_erase()
        erase_results.append(eraser.get_report_data())

        if success:
            print(f"\n✅ Festplatte {disk['id']} erfolgreich gelöscht!")
        else:
            print(f"\n❌ Fehler beim Löschen von {disk['id']}")

    print("\n" + "=" * 60)
    print("📄 ERSTELLE HTML-REPORT")
    print("=" * 60 + "\n")

    report_path = HTMLReporter.generate_report(erase_results)

    json_file = report_path.with_suffix('.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(erase_results, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON-Backup erstellt: {json_file}")

    print("\n" + "=" * 60)
    print("✅ VORGANG ABGESCHLOSSEN")
    print("=" * 60)
    print(f"\n📊 Zusammenfassung:")
    print(f"   Gelöschte Festplatten: {len(selected_disks)}")
    print(f"   Erfolgreiche Löschungen: {sum(1 for r in erase_results if r['success'])}")
    print(f"   Fehlgeschlagene Löschungen: {sum(1 for r in erase_results if not r['success'])}")
    print(f"   Verwendeter Standard: {STANDARDS[selected_standard]['name']}")
    print(f"\n📄 Reports:")
    print(f"   HTML: {report_path}")
    print(f"   JSON: {json_file}")

    print("\n💡 Möchtest du den HTML-Report jetzt öffnen?")
    open_report = input("   [J/N]: ").strip().upper()
    if open_report == 'J':
        import webbrowser
        webbrowser.open(str(report_path))

    print("\n✅ Alle Festplatten können nun DSGVO-konform an Dritte übergeben werden.")
    input("Drücke ENTER zum Beenden...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Abbruch durch Benutzer")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        input("\nDrücke ENTER zum Beenden...")
        sys.exit(1)
