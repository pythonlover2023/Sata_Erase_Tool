#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI OS/HW Detector v1.3
Automatische Betriebssystem- und Hardware-Erkennung
"""

import platform
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


class IrsanAI_Detector:
    def __init__(self):
        self.detection_data = {}
        self.timestamp = datetime.now().isoformat()

    def detect_os(self):
        """Detaillierte OS-Erkennung"""
        os_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'python_version': sys.version.split()[0]
        }
        return os_info

    def detect_privileges(self):
        """Prüft auf Administrator/Root-Rechte"""
        os_type = platform.system()

        try:
            if os_type == 'Windows':
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = subprocess.run(['id', '-u'], capture_output=True, text=True).stdout.strip() == '0'

            return {
                'has_admin': is_admin,
                'required': True,
                'message': 'Administrator-Rechte erforderlich für Festplatten-Operationen'
            }
        except:
            return {
                'has_admin': False,
                'required': True,
                'message': 'Konnte Berechtigungen nicht prüfen'
            }

    def detect_storage_tools(self):
        """Erkennt verfügbare Storage-Management-Tools"""
        os_type = platform.system()
        tools = {}

        if os_type == 'Windows':
            check_tools = ['diskpart', 'cipher', 'wmic']
        elif os_type == 'Linux':
            check_tools = ['dd', 'shred', 'hdparm', 'smartctl', 'lsblk']
        elif os_type == 'Darwin':
            check_tools = ['diskutil', 'dd']
        else:
            check_tools = []

        for tool in check_tools:
            try:
                if os_type == 'Windows':
                    result = subprocess.run(['where', tool], capture_output=True, timeout=2)
                else:
                    result = subprocess.run(['which', tool], capture_output=True, timeout=2)
                tools[tool] = result.returncode == 0
            except:
                tools[tool] = False

        return tools

    def detect_python_packages(self):
        """Prüft installierte Python-Pakete"""
        required = ['psutil', 'jinja2']
        installed = {}

        for pkg in required:
            try:
                __import__(pkg)
                installed[pkg] = True
            except ImportError:
                installed[pkg] = False

        return installed

    def detect_disk_info(self):
        """Grundlegende Festplatten-Informationen (ohne Admin-Rechte)"""
        try:
            import psutil
            disks = []
            for partition in psutil.disk_partitions(all=True):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024 ** 3), 2)
                    })
                except:
                    pass
            return disks
        except ImportError:
            return []

    def run_detection(self):
        """Führt vollständige Erkennung durch"""
        print("🔍 IrsanAI OS/HW Detector v1.3")
        print("=" * 50)

        # OS-Erkennung
        print("\n📋 Betriebssystem-Erkennung...")
        self.detection_data['os'] = self.detect_os()
        print(f"   System: {self.detection_data['os']['system']} {self.detection_data['os']['release']}")
        print(f"   Architektur: {self.detection_data['os']['architecture']}")

        # Berechtigungen
        print("\n🔐 Berechtigungs-Check...")
        self.detection_data['privileges'] = self.detect_privileges()
        status = "✅ OK" if self.detection_data['privileges']['has_admin'] else "⚠️ FEHLT"
        print(f"   Admin/Root-Rechte: {status}")

        # Storage-Tools
        print("\n🛠️ Storage-Tool-Erkennung...")
        self.detection_data['tools'] = self.detect_storage_tools()
        available = sum(self.detection_data['tools'].values())
        total = len(self.detection_data['tools'])
        print(f"   Verfügbare Tools: {available}/{total}")
        for tool, available in self.detection_data['tools'].items():
            status = "✅" if available else "❌"
            print(f"   {status} {tool}")

        # Python-Pakete
        print("\n📦 Python-Paket-Check...")
        self.detection_data['packages'] = self.detect_python_packages()
        for pkg, installed in self.detection_data['packages'].items():
            status = "✅" if installed else "❌"
            print(f"   {status} {pkg}")

        # Festplatten-Info
        print("\n💾 Festplatten-Überblick...")
        self.detection_data['disks'] = self.detect_disk_info()
        if self.detection_data['disks']:
            for disk in self.detection_data['disks']:
                print(f"   📀 {disk['device']}: {disk['total_gb']} GB ({disk['fstype']})")
        else:
            print("   ⚠️ Keine Informationen verfügbar (psutil fehlt)")

        # Timestamp
        self.detection_data['timestamp'] = self.timestamp

        return self.detection_data

    def save_results(self, filename='irsanai_detection.json'):
        """Speichert Erkennungsergebnisse"""
        output_path = Path.cwd() / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.detection_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Ergebnisse gespeichert: {output_path}")
        return output_path

    def print_recommendations(self):
        """Gibt Empfehlungen basierend auf Erkennung"""
        print("\n" + "=" * 50)
        print("📌 EMPFEHLUNGEN")
        print("=" * 50)

        # Admin-Rechte
        if not self.detection_data['privileges']['has_admin']:
            print("\n⚠️ KRITISCH: Administrator-Rechte erforderlich!")
            os_type = self.detection_data['os']['system']
            if os_type == 'Windows':
                print("   → Starte PyCharm als Administrator")
            else:
                print("   → Führe Script mit sudo aus: sudo python3 [script.py]")

        # Fehlende Tools
        missing_tools = [k for k, v in self.detection_data['tools'].items() if not v]
        if missing_tools:
            print(f"\n⚠️ Fehlende Tools: {', '.join(missing_tools)}")
            os_type = self.detection_data['os']['system']
            if os_type == 'Linux':
                print("   → Installation: sudo apt install smartmontools hdparm (Debian/Ubuntu)")
                print("   → Installation: sudo yum install smartmontools hdparm (RHEL/CentOS)")

        # Fehlende Pakete
        missing_pkgs = [k for k, v in self.detection_data['packages'].items() if not v]
        if missing_pkgs:
            print(f"\n⚠️ Fehlende Python-Pakete: {', '.join(missing_pkgs)}")
            print(f"   → Installation: pip install {' '.join(missing_pkgs)}")

        print("\n✅ System bereit für IrsanAI Festplatten-Lösch-Tool")


def main():
    detector = IrsanAI_Detector()
    detector.run_detection()
    detector.save_results()
    detector.print_recommendations()

    print("\n" + "=" * 50)
    print("🎯 Nächster Schritt: Hauptprogramm wird generiert")
    print("=" * 50)


if __name__ == '__main__':
    main()