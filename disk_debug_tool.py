#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disk Detection Debug Tool
Findet heraus, warum Festplatten nicht erkannt werden
"""

import subprocess
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def test_wmic():
    """Test 1: WMIC-Erkennung"""
    print("\n" + "="*60)
    print("TEST 1: WMIC Diskdrive")
    print("="*60)
    
    try:
        result = subprocess.run(
            ['wmic', 'diskdrive', 'list', 'brief'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        print(f"Return Code: {result.returncode}")
        print(f"\nSTDOUT:\n{result.stdout}")
        print(f"\nSTDERR:\n{result.stderr}")
        
        if result.returncode == 0 and result.stdout.strip():
            print("\n✅ WMIC funktioniert!")
            return True
        else:
            print("\n❌ WMIC liefert keine Daten")
            return False
    except FileNotFoundError:
        print("❌ WMIC nicht gefunden (Windows 11?)")
        return False
    except Exception as e:
        print(f"❌ WMIC-Fehler: {e}")
        return False

def test_wmic_detailed():
    """Test 2: WMIC detaillierte Ausgabe"""
    print("\n" + "="*60)
    print("TEST 2: WMIC Diskdrive (detailliert)")
    print("="*60)
    
    try:
        result = subprocess.run(
            ['wmic', 'diskdrive', 'get', 'deviceid,model,size,serialnumber', '/format:list'],
            capture_output=True,
            text=True,
            timeout=15,
            encoding='utf-8',
            errors='ignore'
        )
        
        print(f"Return Code: {result.returncode}")
        print(f"\nAusgabe:\n{result.stdout}")
        
        if result.returncode == 0:
            print("\n✅ WMIC detailliert funktioniert!")
            return True
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_diskpart():
    """Test 3: Diskpart List Disk"""
    print("\n" + "="*60)
    print("TEST 3: Diskpart List Disk")
    print("="*60)
    
    try:
        diskpart_script = "list disk\nexit\n"
        result = subprocess.run(
            ['diskpart'],
            input=diskpart_script,
            capture_output=True,
            text=True,
            timeout=15,
            encoding='cp850',  # Windows Codepage
            errors='ignore'
        )
        
        print(f"Return Code: {result.returncode}")
        print(f"\nAusgabe:\n{result.stdout}")
        
        if result.returncode == 0:
            print("\n✅ Diskpart funktioniert!")
            
            # Analysiere Ausgabe
            lines = result.stdout.split('\n')
            disk_count = 0
            for line in lines:
                if 'Datenträger' in line or 'Disk' in line:
                    if any(char.isdigit() for char in line):
                        disk_count += 1
                        print(f"   Gefunden: {line.strip()}")
            
            print(f"\n📀 Anzahl erkannter Datenträger: {disk_count}")
            return True
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_diskpart_detail():
    """Test 4: Diskpart Detail für jede Disk"""
    print("\n" + "="*60)
    print("TEST 4: Diskpart Detail (für jede Disk)")
    print("="*60)
    
    try:
        # Erst Liste holen
        diskpart_script = "list disk\nexit\n"
        result = subprocess.run(
            ['diskpart'],
            input=diskpart_script,
            capture_output=True,
            text=True,
            timeout=15,
            encoding='cp850',
            errors='ignore'
        )
        
        # Disk-Nummern extrahieren
        disk_numbers = []
        for line in result.stdout.split('\n'):
            if 'Datenträger' in line or 'Disk' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() in ['datenträger', 'disk']:
                        if i + 1 < len(parts) and parts[i + 1].isdigit():
                            disk_numbers.append(parts[i + 1])
        
        print(f"Gefundene Disk-Nummern: {disk_numbers}")
        
        # Details für jede Disk
        for disk_num in disk_numbers:
            print(f"\n--- Disk {disk_num} Details ---")
            diskpart_script = f"select disk {disk_num}\ndetail disk\nexit\n"
            result = subprocess.run(
                ['diskpart'],
                input=diskpart_script,
                capture_output=True,
                text=True,
                timeout=15,
                encoding='cp850',
                errors='ignore'
            )
            print(result.stdout)
        
        return True
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_powershell():
    """Test 5: PowerShell Get-Disk"""
    print("\n" + "="*60)
    print("TEST 5: PowerShell Get-Disk")
    print("="*60)
    
    try:
        ps_script = "Get-Disk | Format-List *"
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        print(f"Return Code: {result.returncode}")
        print(f"\nAusgabe:\n{result.stdout}")
        
        if result.returncode == 0:
            print("\n✅ PowerShell Get-Disk funktioniert!")
            return True
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_psutil():
    """Test 6: psutil (falls installiert)"""
    print("\n" + "="*60)
    print("TEST 6: psutil disk_partitions")
    print("="*60)
    
    try:
        import psutil
        
        print("\n📀 Partitionen:")
        for partition in psutil.disk_partitions(all=True):
            print(f"\n  Device: {partition.device}")
            print(f"  Mountpoint: {partition.mountpoint}")
            print(f"  FSType: {partition.fstype}")
            print(f"  Opts: {partition.opts}")
            
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                print(f"  Size: {usage.total / (1024**3):.2f} GB")
            except:
                print(f"  Size: N/A (kein Zugriff)")
        
        print("\n✅ psutil funktioniert!")
        return True
    except ImportError:
        print("❌ psutil nicht installiert")
        print("   Installation: pip install psutil")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           Disk Detection Debug Tool                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Admin-Check
    if not is_admin():
        print("\n⚠️ WARNUNG: Nicht als Administrator ausgeführt!")
        print("   Manche Tests benötigen Admin-Rechte.\n")
    else:
        print("\n✅ Administrator-Rechte vorhanden\n")
    
    # Alle Tests durchführen
    results = {
        'WMIC Basic': test_wmic(),
        'WMIC Detailed': test_wmic_detailed(),
        'Diskpart List': test_diskpart(),
        'Diskpart Detail': test_diskpart_detail(),
        'PowerShell': test_powershell(),
        'psutil': test_psutil()
    }
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    for test, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test}")
    
    print("\n" + "="*60)
    print("EMPFEHLUNG")
    print("="*60)
    
    if results['PowerShell']:
        print("\n✅ PowerShell Get-Disk funktioniert am besten!")
        print("   → Verwende PowerShell-basierte Erkennung")
    elif results['Diskpart List']:
        print("\n✅ Diskpart funktioniert!")
        print("   → Verwende Diskpart-basierte Erkennung")
    elif results['WMIC Basic']:
        print("\n✅ WMIC funktioniert!")
        print("   → Verwende WMIC-basierte Erkennung")
    else:
        print("\n❌ KEINE Erkennungsmethode funktioniert!")
        print("\n   Mögliche Ursachen:")
        print("   1. Keine Admin-Rechte")
        print("   2. Festplatte nicht angeschlossen")
        print("   3. USB-Gehäuse defekt")
        print("   4. Windows-Sicherheitseinstellungen")
    
    print("\n" + "="*60)
    input("\nDrücke ENTER zum Beenden...")

if __name__ == '__main__':
    main()