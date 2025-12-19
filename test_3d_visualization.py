#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test: 3D Visualizer mit Live-Daten
Simuliert Löschvorgang ohne echte Festplatte
"""

import sys
from pathlib import Path

# Import Bridge
sys.path.insert(0, str(Path(__file__).parent))
from Live_Wipe_Bridge import simulate_wipe_with_visualization

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         3D DISK WIPE VISUALIZER - QUICK TEST            ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    print("Dieser Test simuliert einen Löschvorgang mit 3D-Visualisierung.")
    print("Keine echte Festplatte wird gelöscht!\n")
    
    # Test-Disk-Daten (deine echte Festplatte)
    disk_info = {
        'model': 'ST1000DM 010-2EP102 USB Device',
        'size_gb': 931.32,
        'serial': '9AB6FFFFFFFF',
        'number': 1
    }
    
    print(f"📀 Test-Disk: {disk_info['model']}")
    print(f"   Größe: {disk_info['size_gb']} GB")
    print(f"   Serial: {disk_info['serial']}\n")
    
    # Dauer wählen
    print("Wähle Simulations-Dauer:")
    print("  [1] 10 Sekunden (schnell)")
    print("  [2] 30 Sekunden (normal)")
    print("  [3] 60 Sekunden (realistisch)")
    
    choice = input("\nDeine Wahl [1-3]: ").strip()
    
    durations = {'1': 10, '2': 30, '3': 60}
    duration = durations.get(choice, 30)
    
    print(f"\n✅ Simulation läuft {duration} Sekunden\n")
    
    # Starte Simulation
    try:
        simulate_wipe_with_visualization(disk_info, duration_seconds=duration)
    except KeyboardInterrupt:
        print("\n\n⚠️ Abbruch durch Benutzer")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
