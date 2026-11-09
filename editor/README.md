# Video-Editor von IT Sade (v2)

**Deine Aufnahme → automatisches Transkript → Szenen, B-Roll, Effekte, Sound → fertiges Short (1080×1920)**

## Ablauf für dich
1. Nimm nach Skript auf: Handy hochkant, **ruhiger, einfarbiger Hintergrund** (gerne helle Wand), gutes Licht von vorne, Mikrofon an
2. In CapCut nur Versprecher und Pausen rausschneiden, **ohne** Untertitel, Musik und Effekte
3. Export: 1080p, 30 fps, 9:16
4. Hochladen nach `editor/projekte/<video-name>/aufnahme.mp4` (oder mir schicken)

## Was ich dann mache
1. **Transkript**: Whisper (large-v3-turbo) erkennt dein Persisch Wort für Wort mit Zeitstempeln. Ich korrigiere den Text gegen das Skript
2. **Hintergrund**: Ich stelle dich frei (KI-Segmentierung) und setze dich vor den virtuellen Arbeitsplatz (`design/hintergruende/`), mit Tiefenunschärfe, langsamer Kamerafahrt, Schatten und Neon-Kantenlicht
3. **Szenen** (`timeline.json`):
   - `full`: du im Bild, mit Punch-in-Zooms
   - `split`: B-Roll oben, du unten
   - `pip`: B-Roll im Vollbild, du in einer Kreis-Blase
   - `broll`: nur Animation, deine Stimme läuft weiter
4. **B-Roll-Animationen**:
   - `versus`: VS-Folie
   - `idcard`: Ausweis-Karte
   - `terminal`: Live-Terminal
   - `journey`: Gerät wandert von A nach B
   - `network`: animiertes Netzwerk mit Datenpaketen
   - `summary`: Zusammenfassung
5. **Over-Layer**:
   - Karaoke-Untertitel (aktuelles Wort gelb, Fachbegriffe cyan)
   - Glitch-Hook-Titel
   - Emoji-Sticker mit Partikeln
   - Teaser („آخر ویدیو …“)
   - Folgen-Button
   - Fortschrittsbalken
6. **Effekte**: Whip-Übergänge, Glitch, Shake, Flash, Light Leaks, Farblook (teal/orange), Vignette, Filmkorn
7. **Sound**:
   - Musik mit dramatischen Pausen
   - Whoosh, Pop, Ding, Tippen, Glitch, Riser, Drop
   - Musik wird beim Sprechen automatisch leiser
   - Stimme wird entrauscht und auf Plattform-Lautheit gebracht

## Dateien
| Datei | Aufgabe |
|-------|---------|
| `transcribe.py` | Transkript mit Wort-Zeitstempeln → `words.json` |
| `overlay.html` | Grafik-Engine (B-Roll + Over-Layer) |
| `render-overlay.js` | rendert `under`- und `over`-Layer als transparente Einzelbilder |
| `audio.py` | Musik + Soundeffekte (alles synthetisch, keine Lizenzprobleme) |
| `compose.py` | Compositor: Hintergrund, Freistellung, Layouts, Effekte, Ton → MP4 |
| `hintergrund.py` | erzeugt neue virtuelle Hintergründe per KI (SD-Turbo) |
| `words_from_script.py`, `platzhalter.py` | nur für Demos ohne echte Aufnahme |

## Befehle
```bash
python editor/transcribe.py editor/projekte/NAME/aufnahme.mp4 editor/projekte/NAME/words.json
node editor/render-overlay.js editor/projekte/NAME /tmp/u under
node editor/render-overlay.js editor/projekte/NAME /tmp/o over
python3 editor/audio.py editor/projekte/NAME /tmp/bed.wav
python editor/compose.py editor/projekte/NAME editor/projekte/NAME/aufnahme.mp4 /tmp/u /tmp/o /tmp/bed.wav fertig/NAME.mp4
```
Vorschau einzelner Sekunden: `PREVIEW="1,12.5,30" python editor/compose.py … /tmp/vorschau`

Python-Umgebung (Python 3.12): `pip install -r editor/requirements.txt`
