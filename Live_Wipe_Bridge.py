#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI Live Wipe Bridge v1.2 - Ultimate Immersion Upgrade
Verbindet Python-Löschvorgang mit 3D-Visualizer

Neue Features:
- Echte I/O-Messung mit psutil für realistische Geschwindigkeit
- Unterdrückung von harmlosen "ConnectionAbortedError" im Konsolen-Output
"""

import json
import time
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import socketserver

# Versuch, psutil zu importieren für echte I/O-Messung
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Ein Request-Handler, der ConnectionAbortedError unterdrückt."""
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except ConnectionAbortedError:
            pass # Ignoriere den Fehler, wenn der Client die Verbindung schließt

    def log_message(self, format, *args):
        pass  # Unterdrücke alle Log-Nachrichten

class LiveWipeBridge:
    """Bridge zwischen Python und 3D-Visualizer"""
    
    def __init__(self, disk_info: dict):
        self.disk_info = disk_info
        self.status_file = Path.cwd() / 'live_wipe_status.json'
        self.is_running = False
        self.start_time = None
        self.server_thread = None
        self.server = None
        
        # I/O Tracking mit psutil
        self.last_io_check_time = None
        self.last_bytes_written = 0
        self.physical_disk_name = self._get_physical_disk_name(disk_info.get('number'))

        # Initial status
        self.status = {
            'disk': {
                'model': disk_info.get('model', 'Unknown'),
                'capacity_gb': disk_info.get('size_gb', 0),
                'serial': disk_info.get('serial', 'N/A'),
                'disk_number': disk_info.get('number', 0)
            },
            'wipe': {
                'total_sectors': self._calculate_sectors(disk_info.get('size_gb', 0)),
                'wiped_sectors': 0,
                'progress_percent': 0.0,
                'speed_mbps': 0.0,
                'elapsed_seconds': 0,
                'eta_seconds': 0,
                'status': 'initializing'
            },
            'current_operation': {
                'sector': 0,
                'track': 0,
                'head': 0,
                'pattern': '0x00',
                'pass_number': 1,
                'operation': 'Preparing...'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        self._write_status()
        self._init_io_counters()

    def _get_physical_disk_name(self, disk_number: int) -> str:
        """Gibt den psutil-kompatiblen Namen für eine physische Festplatte zurück."""
        if PSUTIL_AVAILABLE and disk_number is not None:
            try:
                all_disks = psutil.disk_io_counters(perdisk=True)
                for name in all_disks.keys():
                    if str(disk_number) in name:
                        return name
            except Exception:
                pass 
        return None

    def _init_io_counters(self):
        """Initialisiert die I/O-Zähler für die Geschwindigkeitsmessung."""
        if PSUTIL_AVAILABLE and self.physical_disk_name:
            try:
                counters = psutil.disk_io_counters(perdisk=True)
                if self.physical_disk_name in counters:
                    self.last_bytes_written = counters[self.physical_disk_name].write_bytes
                    self.last_io_check_time = time.time()
            except Exception as e:
                print(f"⚠️ Konnte I/O-Zähler nicht initialisieren: {e}")

    def _calculate_sectors(self, size_gb: float) -> int:
        """Berechne Sektoren (512 bytes per sector)"""
        return int((size_gb * 1024 * 1024 * 1024) / 512)
    
    def _write_status(self):
        """Schreibe Status in JSON-Datei"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2)
    
    def _find_free_port(self):
        """Finde freien Port für HTTP-Server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def _start_http_server(self, port):
        """Starte HTTP-Server für Live-Daten"""
        class CORSRequestHandler(QuietHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                super().end_headers()
        
        self.server = HTTPServer(('localhost', port), CORSRequestHandler)
        self.server.serve_forever()
    
    def start(self):
        """Starte Bridge und öffne 3D-Visualizer"""
        self.is_running = True
        self.start_time = time.time()
        
        print("\n" + "="*60)
        print("🎮 STARTE 3D LIVE VISUALIZER")
        print("="*60)
        
        port = self._find_free_port()
        self.server_thread = threading.Thread(
            target=self._start_http_server,
            args=(port,),
            daemon=True
        )
        self.server_thread.start()
        
        time.sleep(1)
        
        viz_url = f"http://localhost:{port}/3D_Live_Disk_Wipe_Visualizer.html"
        
        print(f"\n   📺 Öffne 3D-Visualizer: {viz_url}")
        print(f"   📊 Live-Daten: {self.status_file}")
        print("\n   💡 Der Visualizer aktualisiert sich automatisch!")
        print("   💡 Du kannst das Browser-Fenster jederzeit schließen")
        
        webbrowser.open(viz_url)
        
        print("\n   ✅ 3D-Visualizer gestartet!")
        print("="*60 + "\n")
        
        self.status['wipe']['status'] = 'ready'
        self._write_status()
    
    def update_progress(self, wiped_sectors: int, total_sectors: int = None):
        """Update Lösch-Fortschritt"""
        if not self.is_running:
            return
        
        if total_sectors:
            self.status['wipe']['total_sectors'] = total_sectors
        
        self.status['wipe']['wiped_sectors'] = wiped_sectors
        
        total = self.status['wipe']['total_sectors']
        progress = (wiped_sectors / total * 100) if total > 0 else 0
        self.status['wipe']['progress_percent'] = round(progress, 2)
        
        elapsed_total = time.time() - self.start_time
        self.status['wipe']['elapsed_seconds'] = int(elapsed_total)
        
        if PSUTIL_AVAILABLE and self.physical_disk_name and self.last_io_check_time:
            try:
                current_counters = psutil.disk_io_counters(perdisk=True)
                if self.physical_disk_name in current_counters:
                    current_bytes_written = current_counters[self.physical_disk_name].write_bytes
                    time_delta = time.time() - self.last_io_check_time
                    
                    if time_delta > 0:
                        bytes_written_delta = current_bytes_written - self.last_bytes_written
                        bytes_per_sec = bytes_written_delta / time_delta
                        mbps = bytes_per_sec / (1024 * 1024)
                        self.status['wipe']['speed_mbps'] = round(mbps, 2)
                    
                    self.last_bytes_written = current_bytes_written
                    self.last_io_check_time = time.time()
            except Exception:
                if elapsed_total > 0:
                    bytes_per_sec = (wiped_sectors * 512) / elapsed_total
                    self.status['wipe']['speed_mbps'] = round(bytes_per_sec / (1024*1024), 2)
        else:
            if elapsed_total > 0:
                bytes_per_sec = (wiped_sectors * 512) / elapsed_total
                self.status['wipe']['speed_mbps'] = round(bytes_per_sec / (1024*1024), 2)

        current_speed_mbps = self.status['wipe']['speed_mbps']
        if current_speed_mbps > 0:
            remaining_bytes = (total - wiped_sectors) * 512
            remaining_mb = remaining_bytes / (1024 * 1024)
            eta = remaining_mb / current_speed_mbps
            self.status['wipe']['eta_seconds'] = int(eta)
        else:
            if wiped_sectors > 0:
                eta = (total - wiped_sectors) / wiped_sectors * elapsed_total
                self.status['wipe']['eta_seconds'] = int(eta)

        self.status['timestamp'] = datetime.now().isoformat()
        self._write_status()
    
    def update_operation(self, operation: str, sector: int = None, 
                        track: int = None, head: int = None, 
                        pattern: str = None, pass_num: int = None):
        if not self.is_running: return
        if operation: self.status['current_operation']['operation'] = operation
        if sector is not None: self.status['current_operation']['sector'] = sector
        if track is not None: self.status['current_operation']['track'] = track
        if head is not None: self.status['current_operation']['head'] = head
        if pattern: self.status['current_operation']['pattern'] = pattern
        if pass_num: self.status['current_operation']['pass_number'] = pass_num
        self._write_status()
    
    def set_status(self, status: str):
        self.status['wipe']['status'] = status
        self._write_status()
    
    def complete(self, success: bool = True):
        self.status['wipe']['status'] = 'complete' if success else 'failed'
        self.status['wipe']['progress_percent'] = 100.0 if success else self.status['wipe']['progress_percent']
        self.status['wipe']['speed_mbps'] = 0.0
        self._write_status()
        
        print("\n" + "="*60)
        print(f"{'✅' if success else '❌'} 3D-Visualizer: Löschvorgang {'abgeschlossen' if success else 'fehlgeschlagen'}")
        print("="*60)
    
    def stop(self):
        self.is_running = False
        if self.server:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

if __name__ == '__main__':
    pass
