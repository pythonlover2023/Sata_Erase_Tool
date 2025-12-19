#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrsanAI Compliance Auditor v1.0
Generiert einen detaillierten Audit-Bericht zur Einhaltung von Löschstandards.
"""

class ComplianceAuditor:
    """
    Analysiert die Konformität des Löschvorgangs mit dem gewählten Standard.
    """

    # SOLL-Anforderungen der Standards
    STANDARDS_REQUIREMENTS = {
        'BSI_VS_A': {
            'name': 'BSI VS-A (Verschlusssache - Allgemein)',
            'requirements': [
                "**Pass 1:** Überschreiben mit einem festen Bitmuster (z.B. Nullen).",
                "**Pass 2:** Überschreiben mit dem Komplement des ersten Musters (z.B. Einsen).",
                "**Pass 3:** Überschreiben mit einem zufälligen Bitmuster.",
                "**Verifikation:** Der letzte Schreibvorgang muss überprüft werden (nicht zwingend für VS-A, aber empfohlen)."
            ],
            'simple_explanation': "Die Daten werden dreimal überschrieben: erst mit Nullen, dann mit Einsen und zum Schluss mit zufälligen Zeichen. Das ist wie ein Whiteboard, das man erst abwischt, dann mit schwarzer Tinte übermalt und dann nochmal mit einem zufälligen Muster bekritzelt."
        },
        'NIST_800_88': {
            'name': 'NIST SP 800-88 Rev. 1 (Clear)',
            'requirements': [
                "**Pass 1:** Überschreiben aller adressierbaren Speicherorte mit einem festen Wert (z.B. Nullen).",
                "**Verifikation:** Eine Stichproben- oder vollständige Überprüfung des Überschreibvorgangs wird empfohlen."
            ],
            'simple_explanation': "Alle Daten werden einmal komplett mit Nullen überschrieben. Für moderne Festplatten ist das so, als würde man ein Buch komplett mit schwarzer Tinte übermalen – die ursprüngliche Schrift ist danach nicht mehr lesbar."
        },
        'DOD_5220_22_M': {
            'name': 'DoD 5220.22-M (7-Pass)',
            'requirements': [
                "**Pass 1:** Überschreiben mit einem festen Bitmuster (z.B. Nullen).",
                "**Pass 2:** Überschreiben mit dem Komplement (z.B. Einsen).",
                "**Pass 3:** Überschreiben mit einem zufälligen Bitmuster.",
                "**Pass 4:** Überschreiben mit einem anderen festen Bitmuster.",
                "**Pass 5:** Überschreiben mit dem Komplement von Pass 4.",
                "**Pass 6:** Überschreiben mit einem anderen zufälligen Bitmuster.",
                "**Pass 7:** Verifikation des letzten Schreibvorgangs."
            ],
            'simple_explanation': "Die Daten werden siebenmal auf verschiedene Weisen überschrieben. Das ist ein extrem gründlicher, aber für heutige Technik veralteter Prozess, vergleichbar mit dem siebenmaligen Schreddern eines Dokuments in immer kleinere Teile."
        }
    }

    # IST-Implementierung des Tools
    IMPLEMENTATION_DETAILS = {
        'tool_name': "IrsanAI SATA Secure Erase Tool v1.3",
        'method': "Windows `diskpart` utility",
        'command': "clean all",
        'technical_action': "Führt einen einzelnen Überschreibvorgang auf der gesamten Festplatte durch. Jeder Sektor wird mit Nullen (0x00) überschrieben.",
        'passes_executed': 1,
        'verification_implemented': False
    }

    def __init__(self, standard_key: str):
        self.standard_key = standard_key
        self.soll = self.STANDARDS_REQUIREMENTS.get(standard_key)
        self.ist = self.IMPLEMENTATION_DETAILS

    def generate_audit_html(self) -> str:
        """
        Erstellt den HTML-Code für den Audit-Bericht.
        """
        if not self.soll:
            return "<p>Audit für diesen Standard nicht verfügbar.</p>"

        # Führe die Konformitätsprüfung durch
        soll_passes = len([req for req in self.soll['requirements'] if "Pass" in req])
        ist_passes = self.ist['passes_executed']
        
        # Bewertung
        if self.standard_key == 'NIST_800_88':
            conformity_level = "✅ Vollständig Konform"
            conformity_color = "#28a745" # Grün
            summary = f"Die Implementierung erfüllt die Kernanforderung des NIST SP 800-88 (Clear) Standards durch einen vollständigen 1-Pass-Überschreibvorgang mit Nullen."
        elif soll_passes > ist_passes:
            conformity_level = "⚠️ Teilweise Konform (Limitation)"
            conformity_color = "#ffc107" # Gelb
            summary = f"Die Implementierung erfüllt den ersten Pass des {self.soll['name']} Standards. Windows `diskpart` unterstützt nativ keine Multi-Pass-Verfahren. Für volle Konformität wären externe Tools oder Hardware-Lösungen nötig."
        else:
            conformity_level = "✅ Konform (Basierend auf 1-Pass)"
            conformity_color = "#28a745"
            summary = "Die Implementierung führt einen 1-Pass-Löschvorgang durch, der die Grundlage für diesen Standard bildet."

        # HTML-Struktur aufbauen
        html = f"""
        <div class="audit-section">
            <h3>🛡️ Audit & Compliance Report</h3>
            <div class="audit-summary" style="border-left-color: {conformity_color};">
                <strong>Auditor's Verdict:</strong> {conformity_level}<br>
                <p>{summary}</p>
            </div>

            <div class="audit-grid">
                <!-- SOLL-Anforderungen -->
                <div class="audit-card">
                    <h4>SOLL: Anforderungen nach "{self.soll['name']}"</h4>
                    <ul>
                        {''.join(f"<li>{req}</li>" for req in self.soll['requirements'])}
                    </ul>
                    <div class="simple-explanation">
                        <strong>Einfach erklärt:</strong>
                        <p>{self.soll['simple_explanation']}</p>
                    </div>
                </div>

                <!-- IST-Implementierung -->
                <div class="audit-card">
                    <h4>IST: Technische Implementierung des Tools</h4>
                    <ul>
                        <li><strong>Tool:</strong> {self.ist['tool_name']}</li>
                        <li><strong>Methode:</strong> {self.ist['method']}</li>
                        <li><strong>Befehl:</strong> <code>{self.ist['command']}</code></li>
                        <li><strong>Aktion:</strong> {self.ist['technical_action']}</li>
                        <li><strong>Durchgeführte Pässe:</strong> {self.ist['passes_executed']}</li>
                        <li><strong>Verifikation:</strong> {'Ja' if self.ist['verification_implemented'] else 'Nein (durch Tool nicht durchgeführt)'}</li>
                    </ul>
                </div>
            </div>
        </div>
        """
        return html

    @staticmethod
    def get_audit_styles_css() -> str:
        """Gibt die benötigten CSS-Stile für den Audit-Bericht zurück."""
        return """
        .audit-section { background: #f0f4f8; padding: 25px; border-radius: 8px; margin-top: 30px; }
        .audit-section h3 { color: #333; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .audit-summary { background: #fff; padding: 15px; margin-bottom: 20px; border-left: 5px solid; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .audit-summary p { margin-top: 5px; color: #555; }
        .audit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .audit-card { background: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .audit-card h4 { color: #667eea; margin-bottom: 15px; }
        .audit-card ul { list-style-position: inside; padding-left: 5px; color: #444; }
        .audit-card li { margin-bottom: 8px; }
        .simple-explanation { margin-top: 15px; padding-top: 10px; border-top: 1px dashed #ccc; }
        .simple-explanation p { color: #666; font-style: italic; }
        @media (max-width: 768px) { .audit-grid { grid-template-columns: 1fr; } }
        """
