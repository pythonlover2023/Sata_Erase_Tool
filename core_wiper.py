#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI Core Wiper v1.1
Low-Level Disk Wiping Engine für Sata_Erase
"""

import os
import time
import sys
import random

class CoreWiper:
    """
    Führt Low-Level-Schreiboperationen auf einem physischen Laufwerk durch.
    """
    
    BUFFER_SIZE = 1024 * 1024  # 1 MB Puffer
    
    def __init__(self, disk_number: int, simulation: bool = False):
        self.disk_number = disk_number
        self.simulation = simulation
        
        if sys.platform == 'win32':
            self.device_path = f"\\\\.\\PhysicalDrive{disk_number}"
        else:
            # Linux Fallback (vereinfacht)
            self.device_path = f"/dev/sd{chr(97 + disk_number)}"
            
        self.disk_handle = None
        self.total_size = 0

    def __enter__(self):
        """Öffnet das Handle zum physischen Laufwerk."""
        if self.simulation:
            self.total_size = 10 * 1024 * 1024 * 1024 # 10 GB Simulation
            return self

        try:
            # Unter Windows darf O_BINARY nicht für Block-Devices verwendet werden.
            if sys.platform == 'win32':
                flags = os.O_RDWR
            else:
                flags = os.O_RDWR | getattr(os, 'O_BINARY', 0)

            self.disk_handle = os.open(self.device_path, flags)
            
            # Ermittle Größe
            self.total_size = os.lseek(self.disk_handle, 0, os.SEEK_END)
            os.lseek(self.disk_handle, 0, os.SEEK_SET) # Reset Pointer
            
        except PermissionError:
            raise IOError(f"Zugriff verweigert auf {self.device_path}. Admin-Rechte erforderlich und sicherstellen, dass kein anderes Programm (z.B. Explorer) auf das Laufwerk zugreift.")
        except Exception as e:
            raise IOError(f"Fehler beim Öffnen von {self.device_path}: {e}")
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Schließt das Handle."""
        if self.disk_handle:
            os.close(self.disk_handle)
            self.disk_handle = None

    def _get_buffer(self, pattern: str) -> bytes:
        """Erstellt den Schreib-Puffer basierend auf dem Pattern."""
        if pattern == 'zeros':
            return b'\x00' * self.BUFFER_SIZE
        elif pattern == 'ones':
            return b'\xff' * self.BUFFER_SIZE
        elif pattern == 'random':
            return os.urandom(self.BUFFER_SIZE)
        else:
            # Versuche Hex-Pattern (z.B. '0xAA')
            try:
                if pattern.startswith('0x'):
                    val = int(pattern, 16)
                    return bytes([val]) * self.BUFFER_SIZE
            except:
                pass
            # Fallback
            return b'\x00' * self.BUFFER_SIZE

    def execute_pass(self, pattern: str):
        """
        Führt einen Überschreib-Pass durch.
        Yields: (bytes_written, total_size)
        """
        if self.total_size == 0: return

        buffer = self._get_buffer(pattern)
        bytes_written = 0
        
        if not self.simulation:
            os.lseek(self.disk_handle, 0, os.SEEK_SET)

        while bytes_written < self.total_size:
            # Berechne verbleibende Bytes für den letzten Block
            remaining = self.total_size - bytes_written
            current_buffer_size = min(self.BUFFER_SIZE, remaining)
            
            if not self.simulation:
                # Wenn wir am Ende sind und der Puffer kleiner sein muss
                if current_buffer_size < self.BUFFER_SIZE:
                    os.write(self.disk_handle, buffer[:current_buffer_size])
                else:
                    # Bei 'random' müssen wir jedes Mal neu generieren
                    if pattern == 'random':
                        os.write(self.disk_handle, os.urandom(self.BUFFER_SIZE))
                    else:
                        os.write(self.disk_handle, buffer)
            else:
                time.sleep(0.002) # Simulation Speed

            bytes_written += current_buffer_size
            yield bytes_written, self.total_size

    def verify_pass(self, pattern: str):
        """
        Verifiziert den letzten Pass.
        Yields: (bytes_verified, total_size, success)
        """
        if self.total_size == 0: return

        expected_buffer = self._get_buffer(pattern)
        bytes_verified = 0
        
        if not self.simulation:
            os.lseek(self.disk_handle, 0, os.SEEK_SET)

        while bytes_verified < self.total_size:
            remaining = self.total_size - bytes_verified
            read_size = min(self.BUFFER_SIZE, remaining)
            
            if not self.simulation:
                data = os.read(self.disk_handle, read_size)
                
                # Vergleich (nur bei nicht-random Patterns sinnvoll machbar hier)
                if pattern != 'random':
                    expected_chunk = expected_buffer[:read_size]
                    if data != expected_chunk:
                        yield bytes_verified, self.total_size, False
                        return
            else:
                time.sleep(0.001)

            bytes_verified += read_size
            yield bytes_verified, self.total_size, True
