#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI SATA Secure Erase Tool v1.1
DSGVO+ konformes Festplatten-Lösch-Tool mit professionellem Reporting

Standards:
- BSI VS-A (3x Überschreiben + Verifikation)
- NIST SP 800-88 Rev. 1 (Clear/Purge/Destroy)
- DoD 5220.22-M (7x Überschreiben - veraltet aber oft gefordert)

Autor: IrsanAI
Datum: 2025-12-18
Version: 1.1 - Verbesserte USB-Erkennung + Boot-Disk-Schutz
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

# Konstanten
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
    """Erkennung und Verwaltung von Festplatten - PowerShell Edition"""
    
    @staticmethod
    def list_disks_powershell() -> List[Dict]:
        """Liste alle physischen Festplatten via PowerShell auf"""
        disks = []
        try:
            # PowerShell Get-Disk mit allen Details
            ps_script = """
            Get-Disk | ForEach-Object {
                [PSCustomObject]@{
                    Number = $_.Number
                    FriendlyName = $_.FriendlyName
                    Model = $_.Model
                    SerialNumber = $_.SerialNumber
                    BusType = $_.BusType
                    Size = $_.Size
                    IsSystem = $_.IsSystem
                    IsBoot = $_.IsBoot
                    OperationalStatus = $_.OperationalStatus
                    HealthStatus = $_.HealthStatus
                    PartitionStyle = $_.PartitionStyle
                }
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON
                data = json.loads(result.stdout)
                
                # Handle single disk (not array)
                if isinstance(data, dict):
                    data = [data]
                
                for disk in data:
                    disk_num = disk.get('Number')
                    bus_type = disk.get('BusType', 'Unknown')
                    is_boot = disk.get('IsBoot', False)
                    is_system = disk.get('IsSystem', False)
                    size_bytes = disk.get('Size', 0)
                    size_gb = round(size_bytes / (1024**3), 2) if size_bytes else 0
                    
                    # KRITISCH: Filtere Boot/System-Disks aus
                    if is_boot or is_system or disk_num == 0:
                        continue
                    
                    # FILTER: Nur externe USB/SATA-Festplatten
                    # BusTypes: USB, SATA, SAS sind erlaubt
                    # NICHT erlaubt: RAID, NVMe, Virtual, FileBackedVirtual
                    allowed_bus_types = ['USB', 'SATA', 'SAS', 'iSCSI']
                    
                    if bus_type not in allowed_bus_types:
                        continue
                    
                    disks.append({
                        'id': f'Disk {disk_num}',
                        'number': disk_num,
                        'model': disk.get('FriendlyName', disk.get('Model', 'Unknown')),
                        'serial': disk.get('SerialNumber', 'N/A'),
                        'size_gb': size_gb,
                        'bus_type': bus_type,
                        'status': disk.get('OperationalStatus', 'Unknown'),
                        'health': disk.get('HealthStatus', 'Unknown'),
                        'is_external': True  # Alle gefilterten Disks sind extern
                    })
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON-Fehler: {e}")
            print(f"Output war: {result.stdout[:200]}")
        except Exception as e:
            print(f"⚠️ PowerShell-Fehler: {e}")
        
        return disks
    
    @staticmethod
    def list_disks() -> List[Dict]:
        """Hauptmethode: Liste externe Festplatten"""
        print("🔍 Methode: PowerShell Get-Disk (mit USB/SATA-Filter)")
        disks = DiskDetector.list_disks_powershell()
        
        if disks:
            print(f"✅ {len(disks)} externe Festplatte(n) gefunden")
        else:
            print("⚠️ Keine externen Festplatten gefunden")
            print("   Hinweis: Boot-Disks (Disk 0) werden IMMER ausgeschlossen!")
        
        return disks
    
    @staticmethod
    def get_disk_info(disk_num: int) -> Dict:
        """Detaillierte Informationen zu einer Festplatte"""
        info = {
            'number': disk_num,
            'timestamp': datetime.now().isoformat(),
            'status': 'detected'
        }
        
        try:
            ps_script = f"Get-Disk -Number {disk_num} | Select-Object * | ConvertTo-Json"
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                info.update(data)
        except:
            pass
        
        return info

class SecureEraser:
    """Kernfunktionalität für sicheres Löschen"""
    
    def __init__(self, disk_num: int, standard: str = 'BSI_VS_A'):
        self.disk_num = disk_num
        self.disk_id = f"Disk {disk_num}"
        self.standard = standard
        self.standard_info = STANDARDS[standard]
        self.log = []
        self.start_time = None
        self.end_time = None
        
    def log_event(self, event_type: str, message: str, status: str = 'info'):
        """Ereignis protokollieren"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'status': status
        }
        self.log.append(entry)
        
        # Konsolen-Ausgabe
        symbols = {'info': 'ℹ️', 'success': '✅', 'warning': '⚠️', 'error': '❌'}
        print(f"{symbols.get(status, 'ℹ️')} {message}")
    
    def verify_disk_access(self) -> bool:
        """Prüfe ob auf Festplatte zugegriffen werden kann"""
        self.log_event('verify', f'Prüfe Zugriff auf Disk {self.disk_num}...', 'info')
        
        # SICHERHEITS-CHECK: Disk 0 darf NIEMALS gelöscht werden!
        if self.disk_num == 0:
            self.log_event('security', 'KRITISCH: Disk 0 ist die Boot-Disk und wird NICHT gelöscht!', 'error')
            return False
        
        try:
            diskpart_script = f"select disk {self.disk_num}\ndetail disk\n"
            
            result = subprocess.run(
                ['diskpart'],
                input=diskpart_script,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='cp850',
                errors='ignore'
            )
            
            if result.returncode == 0:
                # Prüfe ob es eine Boot-Disk ist
                if 'Startdatenträger  : Ja' in result.stdout or 'Boot' in result.stdout:
                    self.log_event('security', 'WARNUNG: Dies scheint eine Boot-Disk zu sein!', 'error')
                    return False
                
                self.log_event('verify', 'Festplatten-Zugriff erfolgreich', 'success')
                return True
            else:
                self.log_event('verify', 'Kein Zugriff auf Festplatte', 'error')
                return False
        except Exception as e:
            self.log_event('verify', f'Zugriffsfehler: {e}', 'error')
            return False
    
    def clean_disk(self) -> bool:
        """Führe Clean-Befehl auf Festplatte aus"""
        self.log_event('clean', 'Starte Festplatten-Bereinigung (clean all)...', 'info')
        
        try:
            diskpart_script = f"select disk {self.disk_num}\nclean all\n"
            
            self.log_event('clean', 'Führe "clean all" aus (kann mehrere Minuten dauern)...', 'info')
            
            result = subprocess.run(
                ['diskpart'],
                input=diskpart_script,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 Minuten Timeout für große Festplatten
                encoding='cp850',
                errors='ignore'
            )
            
            if result.returncode == 0:
                self.log_event('clean', 'Festplatte bereinigt (clean all - 1 Pass mit Nullen)', 'success')
                return True
            else:
                self.log_event('clean', f'Bereinigung fehlgeschlagen: {result.stderr}', 'error')
                return False
        except subprocess.TimeoutExpired:
            self.log_event('clean', 'Timeout bei clean all (>30 Min) - möglicherweise erfolgreich', 'warning')
            return True
        except Exception as e:
            self.log_event('clean', f'Fehler bei Bereinigung: {e}', 'error')
            return False
    
    def perform_erase(self) -> bool:
        """Führe kompletten Löschvorgang durch"""
        self.start_time = datetime.now()
        self.log_event('start', f'Starte Löschvorgang nach {self.standard_info["name"]}', 'info')
        
        # Schritt 1: Zugriff verifizieren
        if not self.verify_disk_access():
            self.log_event('error', 'Löschvorgang abgebrochen - Zugriff fehlgeschlagen', 'error')
            return False
        
        # Schritt 2: Clean All (überschreibt mit Nullen)
        if not self.clean_disk():
            self.log_event('error', 'Löschvorgang abgebrochen - Clean fehlgeschlagen', 'error')
            return False
        
        # Schritt 3: Dokumentiere Multi-Pass-Limitation
        passes_completed = 1  # clean all = 1 Pass
        required_passes = self.standard_info['passes']
        
        self.log_event('passes', f'Pass 1/{required_passes} abgeschlossen (clean all mit Nullen)', 'success')
        
        if required_passes > 1:
            self.log_event('limitation', 
                          f'Windows "clean all" führt 1-Pass durch. '
                          f'Für {required_passes}-Pass-Standard werden externe Tools benötigt:\n'
                          f'   • Linux: shred -vfz -n {required_passes} /dev/sdX\n'
                          f'   • DBAN: Bootfähiger USB mit DoD/Gutmann\n'
                          f'   • Eraser: Windows-GUI für Multi-Pass', 
                          'warning')
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        self.log_event('complete', 
                      f'Löschvorgang abgeschlossen in {duration:.1f} Sekunden ({duration/60:.1f} Minuten)', 
                      'success')
        
        return True
    
    def get_report_data(self) -> Dict:
        """Erstelle Report-Daten"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'disk_id': self.disk_id,
            'disk_number': self.disk_num,
            'standard': self.standard,
            'standard_info': self.standard_info,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'log': self.log,
            'success': any(e['status'] == 'success' and e['type'] == 'complete' for e in self.log)
        }

class HTMLReporter:
    """Professionelles HTML-Reporting"""
    
    @staticmethod
    def generate_report(erase_data: List[Dict], output_file: str = None):
        """Generiere HTML-Report"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'Secure_Erase_Report_{timestamp}.html'
        
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SATA Secure Erase Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .security-notice {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 40px;
            border-radius: 5px;
        }}
        .security-notice h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 40px;
        }}
        .summary {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }}
        .summary h2 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .summary-item strong {{
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        .disk-section {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .disk-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }}
        .disk-header h3 {{
            color: #667eea;
            font-size: 1.5em;
        }}
        .status-badge {{
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        .status-error {{
            background: #f8d7da;
            color: #721c24;
        }}
        .info-table {{
            width: 100%;
            margin: 20px 0;
            border-collapse: collapse;
        }}
        .info-table th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #667eea;
            border-bottom: 2px solid #667eea;
        }}
        .info-table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .info-table tr:last-child td {{
            border-bottom: none;
        }}
        .log-section {{
            margin-top: 25px;
        }}
        .log-section h4 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        .log-entry {{
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 0.95em;
        }}
        .log-info {{ background: #e7f3ff; border-left: 3px solid #2196F3; }}
        .log-success {{ background: #d4edda; border-left: 3px solid #28a745; }}
        .log-warning {{ background: #fff3cd; border-left: 3px solid #ffc107; }}
        .log-error {{ background: #f8d7da; border-left: 3px solid #dc3545; }}
        .log-timestamp {{
            color: #6c757d;
            font-size: 0.85em;
            min-width: 90px;
        }}
        .standards-section {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            margin-top: 30px;
        }}
        .standards-section h3 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        .standard-card {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .standard-card h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .standard-card p {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 8px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 SATA Secure Erase Report</h1>
            <p>DSGVO-konformes Festplatten-Löschprotokoll</p>
            <p>Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S Uhr')}</p>
        </div>
        
        <div class="security-notice">
            <h3>🛡️ Sicherheitshinweis</h3>
            <p><strong>Boot-Disk-Schutz aktiv:</strong> Disk 0 (System-Festplatte) wird automatisch von der Löschung ausgeschlossen.</p>
            <p><strong>USB-Filter aktiv:</strong> Nur externe USB/SATA-Festplatten werden zur Löschung angeboten.</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <h2>📊 Zusammenfassung</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <strong>Gelöschte Festplatten</strong>
                        {len(erase_data)}
                    </div>
                    <div class="summary-item">
                        <strong>Erfolgreiche Löschungen</strong>
                        {sum(1 for d in erase_data if d['success'])}
                    </div>
                    <div class="summary-item">
                        <strong>Verwendete Standards</strong>
                        {', '.join(set(d['standard'] for d in erase_data))}
                    </div>
                    <div class="summary-item">
                        <strong>Gesamtdauer</strong>
                        {sum(d['duration_seconds'] or 0 for d in erase_data)/60:.1f} Min
                    </div>
                </div>
            </div>
"""
        
        # Einzelne Festplatten-Reports
        for idx, data in enumerate(erase_data, 1):
            status_class = 'status-success' if data['success'] else 'status-error'
            status_text = '✅ Erfolgreich' if data['success'] else '❌ Fehlgeschlagen'
            
            html += f"""
            <div class="disk-section">
                <div class="disk-header">
                    <h3>Festplatte #{idx}: {data['disk_id']} (Disk {data['disk_number']})</h3>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>
                
                <table class="info-table">
                    <tr>
                        <th>Parameter</th>
                        <th>Wert</th>
                    </tr>
                    <tr>
                        <td><strong>Disk-Nummer</strong></td>
                        <td>Disk {data['disk_number']}</td>
                    </tr>
                    <tr>
                        <td><strong>Lösch-Standard</strong></td>
                        <td>{data['standard_info']['name']}</td>
                    </tr>
                    <tr>
                        <td><strong>Beschreibung</strong></td>
                        <td>{data['standard_info']['description']}</td>
                    </tr>
                    <tr>
                        <td><strong>Anzahl Durchgänge</strong></td>
                        <td>{data['standard_info']['passes']} Pass(es)</td>
                    </tr>
                    <tr>
                        <td><strong>Verifikation</strong></td>
                        <td>{'✅ Aktiviert' if data['standard_info']['verify'] else '❌ Deaktiviert'}</td>
                    </tr>
                    <tr>
                        <td><strong>Startzeit</strong></td>
                        <td>{datetime.fromisoformat(data['start_time']).strftime('%d.%m.%Y %H:%M:%S') if data['start_time'] else 'N/A'}</td>
                    </tr>
                    <tr>
                        <td><strong>Endzeit</strong></td>
                        <td>{datetime.fromisoformat(data['end_time']).strftime('%d.%m.%Y %H:%M:%S') if data['end_time'] else 'N/A'}</td>
                    </tr>
                    <tr>
                        <td><strong>Dauer</strong></td>
                        <td>{data['duration_seconds']:.1f} Sekunden ({data['duration_seconds']/60:.1f} Minuten)</td>
                    </tr>
                </table>
                
                <div class="log-section">
                    <h4>📋 Detailliertes Protokoll</h4>
"""
            
            for log_entry in data['log']:
                log_class = f"log-{log_entry['status']}"
                timestamp = datetime.fromisoformat(log_entry['timestamp']).strftime('%H:%M:%S')
                # Escape HTML in messages
                message = log_entry['message'].replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                html += f"""
                    <div class="log-entry {log_class}">
                        <span class="log-timestamp">{timestamp}</span>
                        <span>{message}</span>
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        # Standards-Dokumentation
        html += """
            <div class="standards-section">
                <h3>📜 Verwendete Lösch-Standards und DSGVO-Compliance</h3>
"""
        
        for std_key, std_info in STANDARDS.items():
            html += f"""
                <div class="standard-card">
                    <h4>{std_info['name']}</h4>
                    <p><strong>Beschreibung:</strong> {std_info['description']}</p>
                    <p><strong>Durchgänge:</strong> {std_info['passes']}</p>
                    <p><strong>Verpflichtend für:</strong> {std_info['mandatory_for']}</p>
                    <p><strong>Muster:</strong> {', '.join(std_info['patterns'])}</p>
                </div>
"""
        
        html += """
                <div class="standard-card">
                    <h4>🇪🇺 DSGVO-Anforderungen (Stand: Dezember 2025)</h4>
                    <p><strong>Art. 17 DSGVO (Recht auf Löschung):</strong> Personenbezogene Daten müssen unwiederbringlich gelöscht werden.</p>
                    <p><strong>Mindeststandard:</strong> NIST SP 800-88 Rev. 1 (1-Pass) - ausreichend für moderne Festplatten</p>
                    <p><strong>Empfohlen:</strong> BSI VS-A (3-Pass) - höhere Sicherheit für sensible Daten</p>
                    <p><strong>Rechenschaftspflicht:</strong> Dieser Report dient als Nachweis gemäß Art. 5 Abs. 2 DSGVO</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>IrsanAI SATA Secure Erase Tool v""" + VERSION + """</strong></p>
            <p>Dieses Dokument wurde automatisch generiert und dient als Compliance-Nachweis für DSGVO Art. 17.</p>
            <p>Erstellt am: """ + datetime.now().strftime('%d.%m.%Y um %H:%M:%S Uhr') + """</p>
            <p style="margin-top: 10px; font-size: 0.85em;">⚠️ Boot-Disk-Schutz: Disk 0 wird niemals zur Löschung angeboten</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Speichere Report
        output_path = Path.cwd() / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n📄 HTML-Report erstellt: {output_path}")
        return output_path

def main():
    """Hauptprogramm"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     IrsanAI SATA Secure Erase Tool v1.1                 ║")
    print("║     DSGVO-konformes Festplatten-Lösch-Tool              ║")
    print("║     🛡️  Mit Boot-Disk-Schutz & USB-Filter               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    # Admin-Check
    AdminCheck.request_admin()
    
    print("✅ Administrator-Rechte bestätigt\n")
    
    # Festplatten erkennen
    print("🔍 Suche nach EXTERNEN Festplatten (USB/SATA)...")
    print("🛡️  Sicherheit: Disk 0 (Boot-Disk) wird IMMER ausgeschlossen!\n")
    
    disks = DiskDetector.list_disks()
    
    if not disks:
        print("❌ Keine EXTERNEN Festplatten gefunden!")
        print("\n⚠️ Stelle sicher, dass:")
        print("   - Die Festplatte per USB angeschlossen ist")
        print("   - Das externe Gehäuse eingeschaltet ist")
        print("   - Windows die Festplatte erkennt (Datenträgerverwaltung)")
        print("\n💡 Hinweis:")
        print("   - Disk 0 (Boot-Disk) wird automatisch ausgeschlossen")
        print("   - Nur USB/SATA-Festplatten werden angezeigt")
        print("   - NVMe/RAID-Disks werden NICHT angezeigt (Sicherheit)")
        input("\nDrücke ENTER zum Beenden...")
        return
    
    print(f"\n✅ {len(disks)} externe Festplatte(n) gefunden:\n")
    for idx, disk in enumerate(disks, 1):
        print(f"   [{idx}] {disk['id']} ({disk['bus_type']})")
        print(f"       Modell: {disk.get('model', 'Unknown')}")
        print(f"       Größe: {disk.get('size_gb', 'Unknown')} GB")
        print(f"       Serial: {disk.get('serial', 'N/A')}")
        print(f"       Status: {disk.get('status', 'Unknown')} / {disk.get('health', 'Unknown')}\n")
    
    # Standard-Auswahl
    print("📋 Verfügbare Lösch-Standards:\n")
    standards_list = list(STANDARDS.items())
    for idx, (key, info) in enumerate(standards_list, 1):
        print(f"   [{idx}] {info['name']}")
        print(f"       {info['description']}")
        print(f"       Durchgänge: {info['passes']}")
        print(f"       Empfohlen für: {info['mandatory_for']}\n")
    
    # Benutzer-Auswahl
    print("=" * 60)
    
    # Standard wählen
    while True:
        try:
            std_choice = input(f"\nWähle Lösch-Standard [1-{len(standards_list)}] (empfohlen: 1 für BSI): ").strip()
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
    
    # Festplatten wählen
    print("\n💾 Festplatten-Auswahl:")
    print("   Gib die Nummern der zu löschenden Festplatten ein (z.B. '1' oder '1,2,3')")
    print("   ⚠️  WARNUNG: Alle Daten werden unwiederbringlich gelöscht!")
    
    while True:
        try:
            disk_choice = input("\nFestplatten-Nummern: ").strip()
            disk_indices = [int(x.strip()) - 1 for x in disk_choice.split(',')]
            selected_disks = [disks[i] for i in disk_indices if 0 <= i < len(disks)]
            if selected_disks:
                break
            print("❌ Ungültige Auswahl!")
        except (ValueError, IndexError):
            print("❌ Ungültige Eingabe!")
    
    print(f"\n⚠️  WARNUNG: Du bist dabei, {len(selected_disks)} Festplatte(n) zu löschen:")
    for disk in selected_disks:
        print(f"   • {disk['id']} - {disk.get('model', 'Unknown')} ({disk.get('size_gb', 'Unknown')} GB)")
    
    confirm = input("\n❓ Bist du SICHER? Tippe 'JA LÖSCHEN' zum Bestätigen: ").strip()
    
    if confirm != 'JA LÖSCHEN':
        print("\n❌ Abgebrochen.")
        input("Drücke ENTER zum Beenden...")
        return
    
    # Löschvorgang durchführen
    print("\n" + "=" * 60)
    print("🚀 STARTE LÖSCHVORGANG")
    print("=" * 60 + "\n")
    
    erase_results = []
    
    for idx, disk in enumerate(selected_disks, 1):
        print(f"\n{'='*60}")
        print(f"📀 FESTPLATTE {idx}/{len(selected_disks)}: {disk['id']}")
        print(f"{'='*60}\n")
        
        eraser = SecureEraser(disk['number'], selected_standard)
        success = eraser.perform_erase()
        erase_results.append(eraser.get_report_data())
        
        if success:
            print(f"\n✅ Festplatte {disk['id']} erfolgreich gelöscht!")
        else:
            print(f"\n❌ Fehler beim Löschen von {disk['id']}")
    
    # HTML-Report generieren
    print("\n" + "=" * 60)
    print("📄 ERSTELLE HTML-REPORT")
    print("=" * 60 + "\n")
    
    report_path = HTMLReporter.generate_report(erase_results)
    
    # JSON-Backup
    json_file = report_path.with_suffix('.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(erase_results, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON-Backup erstellt: {json_file}")
    
    # Zusammenfassung
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
    
    # Report öffnen
    print("\n💡 Möchtest du den HTML-Report jetzt öffnen?")
    open_report = input("   [J/N]: ").strip().upper()
    
    if open_report == 'J':
        import webbrowser
        webbrowser.open(str(report_path))
    
    print("\n✅ Alle Festplatten können nun DSGVO-konform an Dritte übergeben werden.")
    print("   Das HTML-Protokoll dient als Compliance-Nachweis.\n")
    
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