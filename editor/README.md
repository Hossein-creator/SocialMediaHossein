# Video-Editor von IT Sade

Pipeline: **deine Aufnahme → Grafiken, Untertitel, Zooms, Farbe, Musik, Soundeffekte → fertiges Short (1080×1920)**

## Ablauf
1. Du nimmst nach dem Skript auf und schneidest grob (Versprecher und Pausen raus)
2. Du exportierst aus CapCut **ohne** Untertitel, Musik und Effekte: 1080p, 9:16, 30 fps
3. Du lädst die Datei hier ins Repo hoch: `editor/projekte/<video-name>/aufnahme.mp4`
4. Ich schreibe die `timeline.json` (Untertitel, Grafiken, Zooms, Soundeffekte) passend zu deinem Timing
5. Ich rendere das fertige Video und lege es in `fertig/` ab

## Dateien
| Datei | Aufgabe |
|-------|---------|
| `overlay.html` | Grafik-Engine: Untertitel, Hook-Titel, Karten, Vergleiche, Call-to-Action, Fortschrittsbalken |
| `render-overlay.js` | Rendert die Grafikebene als transparente Einzelbilder |
| `audio.py` | Erzeugt Hintergrundmusik und Soundeffekte (whoosh, pop, ding, typing …), alles selbst synthetisiert und ohne Lizenzprobleme |
| `compose.py` | Fügt alles zusammen: Zooms, Hook-Shake, Farbkorrektur, Vignette, Stimme säubern + Lautheit, Musik wird beim Sprechen automatisch leiser |
| `platzhalter.py` | Nur für Demos: Platzhalter statt echter Aufnahme |
| `projekte/<name>/timeline.json` | Drehbuch für ein Video |

## Befehle
```bash
node editor/render-overlay.js editor/projekte/NAME /tmp/frames
python3 editor/audio.py editor/projekte/NAME /tmp/bed.wav
python3 editor/compose.py editor/projekte/NAME editor/projekte/NAME/aufnahme.mp4 /tmp/frames /tmp/bed.wav fertig/NAME.mp4
```
