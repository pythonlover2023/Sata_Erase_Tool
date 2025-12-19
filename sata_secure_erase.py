#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI SATA Secure Erase Tool v1.2
DSGVO+ konformes Festplatten-Lösch-Tool mit professionellem Reporting

Standards:
- BSI VS-A (3x Überschreiben + Verifikation)
- NIST SP 800-88 Rev. 1 (Clear/Purge/Destroy)
- DoD 5220.22-M (7x Überschreiben - veraltet aber oft gefordert)

Autor: IrsanAI
Datum: 2025-12-19
"""

import os
import sys
import subprocess
import ctypes
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

# Importiere Module
from compliance_auditor import ComplianceAuditor
from core_wiper import CoreWiper

# Konstanten
VERSION = "1.2"
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

class AdminCheck:
    """Prüfung und Anforderung von Administrator-Rechten"""
    
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def request_admin():
        if not AdminCheck.is_admin():
            print("╔══════════════════════════════════════════════════════════╗")
            print("║  ⚠️  ADMINISTRATOR-RECHTE ERFORDERLICH                  ║")
            print("╚══════════════════════════════════════════════════════════╝")
            print("\n📋 Anleitung:")
            print("1. Schließe PyCharm")
            print("2. Rechtsklick auf PyCharm-Icon")
            print("3. 'Als Administrator ausführen'")
            print("4. Öffne dieses Projekt erneut")
            print("5. Führe das Script erneut aus")
            print("\n❌ Script wird beendet...")
            input("\nDrücke ENTER zum Beenden...")
            sys.exit(1)

class DiskDetector:
    """Erkennung und Verwaltung von Festplatten"""
    
    @staticmethod
    def list_disks() -> List[Dict]:
        """Liste alle externen physischen Festplatten auf (USB/SATA) und schließt die Boot-Disk aus."""
        disks = []
        boot_disk_index = "0" 

        try:
            cmd = [
                'wmic', 'diskdrive', 'get', 
                'DeviceID,Model,Size,SerialNumber,InterfaceType,Index,MediaType', 
                '/format:csv'
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = [p.strip() for p in line.split(',')]
                        if not parts or len(parts) < 8:
                            continue
                        
                        node, device_id, index, iface_type, media_type, model, serial, size = parts

                        if not index or not iface_type:
                            continue
                        
                        if index == boot_disk_index:
                            continue

                        is_external = (
                            iface_type.upper() == 'USB' or 
                            'External' in media_type or 
                            'Removable' in media_type
                        )

                        if is_external:
                            try:
                                size_gb = round(int(size) / (1024**3), 2) if size else 0
                                disks.append({
                                    'id': f"Disk {index}",
                                    'number': int(index),
                                    'model': model if model else 'Unknown',
                                    'serial': serial if serial else 'N/A',
                                    'size_gb': size_gb,
                                    'bus_type': iface_type,
                                    'path': device_id
                                })
                            except (ValueError, IndexError):
                                continue
        except FileNotFoundError:
            print("⚠️ WMIC.exe nicht gefunden. Festplatten-Erkennung unter Windows nicht möglich.")
        except Exception as e:
            print(f"⚠️ Fehler bei Festplatten-Erkennung: {e}")
        
        return disks
    
    @staticmethod
    def get_disk_info(disk_id: str) -> Dict:
        """Detaillierte Informationen zu einer Festplatte"""
        info = {
            'id': disk_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'detected'
        }
        
        try:
            result = subprocess.run(
                ['wmic', 'diskdrive', 'where', f'deviceid="{disk_id}"', 'get', '*', '/format:list'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        info[key.strip()] = value.strip()
        except:
            pass
        
        return info

class SecureEraser:
    """Kernfunktionalität für sicheres Löschen"""
    
    def __init__(self, disk_number: int, standard: str = 'BSI_VS_A'):
        self.disk_number = disk_number
        self.disk_id = f"Disk {disk_number}"
        self.standard = standard
        self.standard_info = STANDARDS[standard]
        self.log = []
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
    
    def verify_disk_access(self) -> bool:
        """Prüfe ob auf Festplatte zugegriffen werden kann"""
        self.log_event('verify', f'Prüfe Zugriff auf {self.disk_id}...', 'info')
        try:
            with CoreWiper(self.disk_number) as wiper:
                if wiper.total_size > 0:
                    self.log_event('verify', f'Festplatten-Zugriff erfolgreich. Größe: {wiper.total_size / (1024**3):.2f} GB', 'success')
                    return True
                else:
                    self.log_event('verify', 'Festplattengröße ist 0.', 'error')
                    return False
        except Exception as e:
            self.log_event('verify', f'Zugriffsfehler: {e}', 'error')
            return False
    
    def perform_erase(self) -> bool:
        """Führe kompletten Löschvorgang durch"""
        self.start_time = datetime.now()
        self.log_event('start', f'Starte Löschvorgang nach {self.standard_info["name"]}', 'info')
        
        if not self.verify_disk_access():
            return False
        
        try:
            with CoreWiper(self.disk_number) as wiper:
                patterns = self.standard_info['patterns']
                total_passes = len(patterns)
                
                for i, pattern in enumerate(patterns):
                    if pattern == 'verify':
                        continue # Verifizierung wird separat behandelt

                    pass_num = i + 1
                    self.log_event('pass_start', f"Starte Pass {pass_num}/{total_passes} mit Pattern '{pattern}'", 'info')

                    # Führe den Schreib-Pass durch
                    last_log_time = time.time()
                    for bytes_written, total_size in wiper.execute_pass(pattern):
                        # Fortschrittsanzeige alle 5 Sekunden
                        if time.time() - last_log_time > 5:
                            progress = (bytes_written / total_size) * 100
                            print(f"   Pass {pass_num}: {progress:.1f}% ({bytes_written / (1024**2):.0f} MB)", end='\r')
                            last_log_time = time.time()
                    
                    print("") # Newline nach Progress
                    self.log_event('pass_end', f"Pass {pass_num}/{total_passes} abgeschlossen.", 'success')

                # Führe Verifizierung durch
                if self.standard_info.get('verify', False):
                    last_pattern = patterns[-1] if patterns[-1] != 'verify' else patterns[-2]
                    if last_pattern == 'random':
                        self.log_event('verify_skip', "Verifizierung bei Random-Pattern nicht möglich (technisch bedingt).", 'warning')
                    else:
                        self.log_event('verify_start', f"Starte Verifizierung des letzten Passes ('{last_pattern}')...", 'info')
                        verification_ok = True
                        
                        last_log_time = time.time()
                        for bytes_verified, total_size, is_match in wiper.verify_pass(last_pattern):
                            if not is_match:
                                self.log_event('verify_fail', f"Verifizierung bei Byte {bytes_verified} fehlgeschlagen!", 'error')
                                verification_ok = False
                                break
                            
                            if time.time() - last_log_time > 5:
                                progress = (bytes_verified / total_size) * 100
                                print(f"   Verify: {progress:.1f}%", end='\r')
                                last_log_time = time.time()
                        
                        print("")
                        if verification_ok:
                            self.log_event('verify_success', "Verifizierung erfolgreich abgeschlossen.", 'success')
                
        except Exception as e:
            self.log_event('critical_error', f"Ein kritischer Fehler ist aufgetreten: {e}", 'error')
            return False

        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.log_event('complete', f'Löschvorgang abgeschlossen in {duration:.1f} Sekunden', 'success')
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

class HTMLReporter:
    """Professionelles HTML-Reporting mit Audit-Funktion"""
    
    @staticmethod
    def generate_report(erase_data: List[Dict], output_file: str = None):
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'Secure_Erase_Report_{timestamp}.html'
        
        # PDF Export Skript und Button
        pdf_script = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.9.2/html2pdf.bundle.min.js"></script>
        <script>
            function exportToPDF() {
                const element = document.getElementById('report-content');
                const opt = {
                    margin:       0.5,
                    filename:     'Secure_Erase_Report.pdf',
                    image:        { type: 'jpeg', quality: 0.98 },
                    html2canvas:  { scale: 2, useCORS: true },
                    jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
                };
                html2pdf().set(opt).from(element).save();
            }
        </script>
        """
        pdf_button = '<button onclick="exportToPDF()" class="pdf-btn">📄 PDF Export</button>'

        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SATA Secure Erase Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    {pdf_script}
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 20px; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #4a00e0 0%, #8e2de2 100%); color: white; padding: 40px; text-align: center; border-top-left-radius: 10px; border-top-right-radius: 10px; }}
        .header h1 {{ margin-bottom: 10px; }}
        .content {{ padding: 30px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-item {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #8e2de2; }}
        .summary-item strong {{ display: block; margin-bottom: 5px; color: #4a00e0; }}
        .disk-section {{ border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 30px; overflow: hidden; }}
        .disk-header {{ display: flex; justify-content: space-between; align-items: center; padding: 20px; background: #f8f9fa; border-bottom: 1px solid #e0e0e0; }}
        .disk-header h3 {{ color: #4a00e0; }}
        .status-badge {{ padding: 8px 20px; border-radius: 20px; font-weight: bold; }}
        .status-success {{ background: #d4edda; color: #155724; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        .log-section {{ padding: 20px; }}
        .log-entry {{ padding: 10px; margin-bottom: 8px; border-radius: 5px; display: flex; gap: 15px; align-items: center; }}
        .log-info {{ background: #e7f3ff; border-left: 3px solid #2196F3; }}
        .log-success {{ background: #d4edda; border-left: 3px solid #28a745; }}
        .log-warning {{ background: #fff3cd; border-left: 3px solid #ffc107; }}
        .log-error {{ background: #f8d7da; border-left: 3px solid #dc3545; }}
        .log-timestamp {{ font-size: 0.85em; color: #6c757d; min-width: 70px; }}
        .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 0.9em; background: #f8f9fa; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;}}
        .pdf-btn {{ position: fixed; bottom: 20px; right: 20px; background: #4a00e0; color: white; border: none; padding: 15px 25px; border-radius: 50px; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.2); font-size: 16px; z-index: 100; }}
        .pdf-btn:hover {{ background: #8e2de2; }}
        {ComplianceAuditor.get_audit_styles_css()}
    </style>
</head>
<body>
    {pdf_button}
    <div class="container" id="report-content">
        <div class="header">
            <h1>🔒 SATA Secure Erase Report</h1>
            <p>DSGVO-konformes Festplatten-Löschprotokoll (v{VERSION})</p>
            <p>Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S Uhr')}</p>
        </div>
        <div class="content">
"""
        
        for idx, data in enumerate(erase_data, 1):
            status_class = 'status-success' if data['success'] else 'status-error'
            status_text = 'Erfolgreich' if data['success'] else 'Fehlgeschlagen'
            duration_seconds = data.get('duration_seconds')
            duration_text = f"{duration_seconds:.1f}s ({duration_seconds/60:.1f}min)" if duration_seconds is not None else "N/A"

            # Compliance Auditor aufrufen
            auditor = ComplianceAuditor(data['standard'])
            audit_html = auditor.generate_audit_html()

            html += f"""
            <div class="disk-section">
                <div class="disk-header">
                    <h3>Festplatte #{idx}: {data['disk_id']}</h3>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>
                <div class="summary-grid" style="padding: 20px;">
                    <div class="summary-item"><strong>Startzeit</strong> {datetime.fromisoformat(data['start_time']).strftime('%H:%M:%S') if data['start_time'] else 'N/A'}</div>
                    <div class="summary-item"><strong>Endzeit</strong> {datetime.fromisoformat(data['end_time']).strftime('%H:%M:%S') if data['end_time'] else 'N/A'}</div>
                    <div class="summary-item"><strong>Dauer</strong> {duration_text}</div>
                    <div class="summary-item"><strong>Standard</strong> {data['standard_info']['name']}</div>
                </div>
                
                {audit_html}

                <div class="log-section">
                    <h4>📋 Detailliertes Ereignisprotokoll</h4>
                    {''.join(f'''
                        <div class="log-entry log-{log['status']}">
                            <span class="log-timestamp">{datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')}</span>
                            <span>{log['message']}</span>
                        </div>
                    ''' for log in data['log'])}
                </div>
            </div>
            """
        
        html += """
        </div>
        <div class="footer">
            <p><strong>IrsanAI SATA Secure Erase Tool v""" + VERSION + """</strong></p>
            <p>Dieses Dokument dient als Nachweis der ordnungsgemäßen Löschung gemäß DSGVO Art. 17.</p>
        </div>
    </div>
</body>
</html>
"""
        
        output_path = Path.cwd() / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n📄 HTML-Report erstellt: {output_path}")
        return output_path

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     IrsanAI SATA Secure Erase Tool v1.2                 ║")
    print("║     DSGVO-konformes Festplatten-Lösch-Tool              ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    AdminCheck.request_admin()
    print("✅ Administrator-Rechte bestätigt\n")
    
    print("🔍 Suche nach Festplatten...")
    disks = DiskDetector.list_disks()
    
    if not disks:
        print("❌ Keine Festplatten gefunden!")
        input("\nDrücke ENTER zum Beenden...")
        return
    
    print(f"\n✅ {len(disks)} Festplatte(n) gefunden:\n")
    for idx, disk in enumerate(disks, 1):
        print(f"   [{idx}] {disk['id']} ({disk.get('model', 'Unknown')}) - {disk.get('size_gb', 'Unknown')} GB")
    
    print("\n📋 Verfügbare Lösch-Standards:\n")
    standards_list = list(STANDARDS.items())
    for idx, (key, info) in enumerate(standards_list, 1):
        print(f"   [{idx}] {info['name']}")
    
    while True:
        try:
            std_choice = input(f"\nWähle Lösch-Standard [1-{len(standards_list)}]: ").strip() or "1"
            std_idx = int(std_choice) - 1
            if 0 <= std_idx < len(standards_list):
                selected_standard = standards_list[std_idx][0]
                break
            print("❌ Ungültige Auswahl!")
        except ValueError:
            print("❌ Bitte eine Zahl eingeben!")
    
    print(f"\n✅ Standard gewählt: {STANDARDS[selected_standard]['name']}")
    
    while True:
        try:
            disk_choice = input("\nFestplatten-Nummern (z.B. '1' oder '1,2'): ").strip()
            disk_indices = [int(x.strip()) - 1 for x in disk_choice.split(',')]
            selected_disks = [disks[i] for i in disk_indices if 0 <= i < len(disks)]
            if selected_disks:
                break
            print("❌ Ungültige Auswahl!")
        except (ValueError, IndexError):
            print("❌ Ungültige Eingabe!")
    
    print(f"\n⚠️  WARNUNG: Du bist dabei, {len(selected_disks)} Festplatte(n) zu löschen:")
    for disk in selected_disks:
        print(f"   • {disk['id']} ({disk.get('size_gb', 'Unknown')} GB)")
    
    confirm = input("\n❓ Bist du SICHER? Tippe 'JA LÖSCHEN' zum Bestätigen: ").strip()
    
    if confirm != 'JA LÖSCHEN':
        print("\n❌ Abgebrochen.")
        return
    
    print("\n" + "=" * 60 + "\n🚀 STARTE LÖSCHVORGANG\n" + "=" * 60 + "\n")
    
    erase_results = []
    for disk in selected_disks:
        print(f"\n--- Lösche Festplatte: {disk['id']} ---\n")
        eraser = SecureEraser(disk['number'], selected_standard)
        eraser.perform_erase()
        erase_results.append(eraser.get_report_data())
    
    print("\n" + "=" * 60 + "\n📄 ERSTELLE HTML-REPORT\n" + "=" * 60 + "\n")
    report_path = HTMLReporter.generate_report(erase_results)
    
    open_report = input("\n💡 Möchtest du den HTML-Report jetzt öffnen? [J/n]: ").strip().upper()
    if open_report != 'N':
        import webbrowser
        webbrowser.open(str(report_path))
    
    print("\n✅ Vorgang abgeschlossen.")
    input("\nDrücke ENTER zum Beenden...")

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
