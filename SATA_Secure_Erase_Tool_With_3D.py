#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI SATA Secure Erase Tool v1.5 - Smart Feedback
MIT 3D LIVE VISUALISIERUNG!

Neue Features:
- Smart Feedback System: Realistische, zeitbasierte Simulation im `diskpart`-Fallback-Modus.
- Verbesserte User Experience für spezielle Hardware (z.B. verschlüsselte RAIDs).
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import threading
import subprocess

sys.path.insert(0, str(Path(__file__).parent))

from sata_secure_erase import SecureEraser, AdminCheck, DiskDetector, STANDARDS, HTMLReporter
from Live_Wipe_Bridge import LiveWipeBridge
from core_wiper import CoreWiper

# Überschreibe SecureEraser mit 3D-Visualisierung
class SecureEraserWith3D(SecureEraser):
    """
    Erweitert SecureEraser um eine 3D-Live-Visualisierung und eine Fallback-Logik.
    """
    
    def __init__(self, disk_number: int, standard: str = 'BSI_VS_A', disk_info: dict = None):
        super().__init__(disk_number, standard)
        self.bridge = None
        self.disk_info = disk_info or {}
        self.start_time = None
        self.end_time = None
    
    def perform_erase(self, enable_3d: bool = True) -> bool:
        """
        Führt den Löschvorgang durch. Versucht zuerst die standardkonforme CoreWiper-Methode.
        Bei einem IOError (z.B. bei verschlüsselten RAIDs) wird auf die `diskpart`-Methode zurückgegriffen.
        """
        if enable_3d:
            self.bridge = LiveWipeBridge(self.disk_info)
            self.bridge.start()
            try:
                input("\n📺 3D-Visualizer im Browser geladen? [J zum Fortfahren]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                pass
        
        self.start_time = datetime.now()
        self.log_event('start', f'Starte Löschvorgang nach {self.standard_info["name"]}', 'info')
        
        if self.bridge:
            self.bridge.set_status('wiping')
            self.bridge.update_operation(operation='Initializing Drive Interface...')

        can_use_core_wiper = True
        try:
            with CoreWiper(self.disk_number) as test_wiper:
                if test_wiper.total_size == 0:
                    can_use_core_wiper = False
        except IOError as e:
            self.log_event('fallback', f"Direkter Zugriff via CoreWiper fehlgeschlagen: {e}", 'warning')
            self.log_event('fallback', "Wechsle zu robuster `diskpart` Methode (1-Pass Nullen).", 'warning')
            can_use_core_wiper = False

        if can_use_core_wiper:
            success = self._erase_with_core_wiper()
        else:
            success = self._erase_with_diskpart()

        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.log_event('complete', f'Löschvorgang abgeschlossen in {duration:.1f} Sekunden', 'success' if success else 'error')
        
        if self.bridge:
            self.bridge.complete(success=success)
            time.sleep(5)
            self.bridge.stop()
        
        return success

    def _erase_with_core_wiper(self) -> bool:
        """Standardkonformes Löschen mit Multi-Pass."""
        self.log_event('method', "Verwende standardkonforme CoreWiper-Engine.", 'info')
        try:
            with CoreWiper(self.disk_number) as wiper:
                patterns = self.standard_info['patterns']
                total_passes = len([p for p in patterns if p != 'verify'])

                pass_num = 0
                for pattern in patterns:
                    if pattern == 'verify': continue
                    
                    pass_num += 1
                    self.log_event('pass_start', f"Starte Pass {pass_num}/{total_passes} mit Pattern '{pattern}'", 'info')
                    
                    for bytes_written, total_size in wiper.execute_pass(pattern):
                        if self.bridge:
                            self.bridge.update_progress(bytes_written, total_size)
                            self.bridge.update_operation(
                                operation=f"Pass {pass_num}: Writing '{pattern}'",
                                sector=bytes_written // 512,
                                track=int((bytes_written / total_size) * 1000),
                                head=pass_num % 8
                            )
                    
                    self.log_event('pass_end', f"Pass {pass_num}/{total_passes} abgeschlossen.", 'success')

                if self.standard_info.get('verify', False):
                    last_pattern = next(p for p in reversed(patterns) if p != 'verify')
                    if last_pattern == 'random':
                        self.log_event('verify_skip', "Verifizierung bei Random-Pattern nicht möglich.", 'warning')
                    else:
                        self.log_event('verify_start', f"Starte Verifizierung des letzten Passes ('{last_pattern}')...", 'info')
                        verification_ok = True
                        for bytes_verified, total_size, is_match in wiper.verify_pass(last_pattern):
                            if self.bridge:
                                self.bridge.update_progress(bytes_verified, total_size)
                                self.bridge.update_operation(operation=f"Verifying Pass {total_passes}...")
                            if not is_match:
                                self.log_event('verify_fail', f"Verifizierung bei Byte {bytes_verified} fehlgeschlagen!", 'error')
                                verification_ok = False
                                break
                        if verification_ok:
                            self.log_event('verify_success', "Verifizierung erfolgreich abgeschlossen.", 'success')
            return True
        except Exception as e:
            self.log_event('critical_error', f"Ein kritischer Fehler ist aufgetreten: {e}", 'error')
            return False

    def _erase_with_diskpart(self) -> bool:
        """Fallback-Löschen mit `diskpart clean all` und intelligenter Simulation."""
        self.log_event('method', "Verwende `diskpart` Fallback-Methode.", 'warning')
        
        # Annahme für die Simulation
        assumed_speed_mbps = 80  # Konservative Annahme für USB/HDD
        total_size_gb = self.disk_info.get('size_gb', 0)
        total_size_bytes = total_size_gb * 1024 * 1024 * 1024
        estimated_duration_sec = total_size_bytes / (assumed_speed_mbps * 1024 * 1024) if assumed_speed_mbps > 0 else 3600

        try:
            diskpart_script = f"select disk {self.disk_number}\nonline disk\nattributes disk clear readonly\nclean all\n"
            
            process_complete = threading.Event()
            process_result = {'success': False, 'error': ''}
            wipe_start_time = time.time()

            def run_diskpart():
                try:
                    result = subprocess.run(['diskpart'], input=diskpart_script, capture_output=True, text=True, timeout=estimated_duration_sec * 1.5, encoding='cp850', errors='ignore')
                    process_result['success'] = (result.returncode == 0)
                    if not process_result['success']:
                        process_result['error'] = result.stdout or result.stderr
                except subprocess.TimeoutExpired:
                    process_result['error'] = "Diskpart-Timeout nach geschätzter Dauer überschritten."
                except Exception as e:
                    process_result['error'] = str(e)
                finally:
                    process_complete.set()

            thread = threading.Thread(target=run_diskpart, daemon=True)
            thread.start()

            if self.bridge:
                total_sectors = self.bridge.status['wipe']['total_sectors']
                while not process_complete.wait(timeout=1.0): # Update jede Sekunde
                    elapsed_time = time.time() - wipe_start_time
                    
                    # Zeitbasierter Fortschritt
                    progress_percent = (elapsed_time / estimated_duration_sec) * 100
                    if progress_percent >= 99.9:
                        progress_percent = 99.9 # Nicht 100% erreichen, bevor der Prozess fertig ist
                    
                    wiped_sectors = int((progress_percent / 100) * total_sectors)
                    self.bridge.update_progress(wiped_sectors)
                    
                    remaining_sec = max(0, estimated_duration_sec - elapsed_time)
                    remaining_min = remaining_sec / 60
                    self.bridge.update_operation(operation=f"Executing `diskpart` (Black-Box)... Estimated time remaining: ~{remaining_min:.0f} min")

            thread.join()

            if process_result['success']:
                if self.bridge: self.bridge.update_progress(self.bridge.status['wipe']['total_sectors'])
                self.log_event('clean', 'Festplatte via `diskpart` bereinigt (1-Pass Nullen).', 'success')
                return True
            else:
                self.log_event('clean', f'diskpart-Bereinigung fehlgeschlagen: {process_result["error"]}', 'error')
                return False
        except Exception as e:
            self.log_event('clean', f'Fehler bei diskpart-Ausführung: {e}', 'error')
            return False

def main_with_3d():
    """Hauptprogramm mit 3D-Visualisierung"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     IrsanAI SATA Secure Erase Tool v1.5                 ║")
    print("║     Smart Feedback & Multi-Pass Engine                ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    AdminCheck.request_admin()
    print("✅ Administrator-Rechte bestätigt\n")
    
    print("🔍 Suche nach EXTERNEN Festplatten (USB/SATA)...")
    disks = DiskDetector.list_disks()
    
    if not disks:
        print("❌ Keine EXTERNEN Festplatten gefunden!")
        input("\nDrücke ENTER zum Beenden...")
        return
    
    print(f"\n✅ {len(disks)} externe Festplatte(n) gefunden:\n")
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
            disk_choice = input("\nFestplatten-Nummer (z.B. '1' oder '1,2'): ").strip()
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
    
    viz_choice = input("\n🎮 3D-Visualizer aktivieren? [J/n]: ").strip().upper()
    enable_3d = (viz_choice != 'N')
    
    print("\n" + "=" * 60 + "\n🚀 STARTE LÖSCHVORGANG\n" + "=" * 60 + "\n")
    
    erase_results = []
    for disk in selected_disks:
        print(f"\n--- Lösche Festplatte: {disk['id']} ---\n")
        eraser = SecureEraserWith3D(disk['number'], selected_standard, disk_info=disk)
        success = eraser.perform_erase(enable_3d=enable_3d)
        erase_results.append(eraser.get_report_data())
        
        if success:
            print(f"\n✅ Festplatte {disk['id']} erfolgreich gelöscht!")
        else:
            print(f"\n❌ Fehler beim Löschen von {disk['id']}")
    
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
        main_with_3d()
    except KeyboardInterrupt:
        print("\n\n⚠️ Abbruch durch Benutzer")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
        input("\nDrücke ENTER zum Beenden...")
        sys.exit(1)
