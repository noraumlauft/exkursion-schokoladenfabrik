# Schokoladenfabrik – Lernspiel für den Sachunterricht

2D-Lernspiel: Mit Meister Lenz durch die Schokoladenfabrik, von der Kakaobohne bis zum Karton
(Reinigen, Rösten, Brechen und Mahlen, Mischen, Conchieren, Formen und Verpacken, Laderampe, Quiz, Urkunde).

- Alles steckt in einer einzigen Datei: `index.html`. Es werden keine weiteren Dateien gebraucht.
- Läuft im Browser auf Tablet, Handy und Computer.
- Meister Lenz spricht mit gespeicherten deutschen MP3-Aufnahmen; die Maschinengeräusche werden im Browser erzeugt.
- Schülermodus (Standard): Erklärungen und Animationen laufen beim ersten Mal ganz durch, überspringen geht erst beim zweiten Mal.
- Lehrermodus: 10× schnell oben links auf „☰ Schokoladenfabrik“ tippen. Dann lässt sich alles überspringen, auch ganze Stationen. Beenden über das Spielmenü.


## Meister Lenz: feste Sprachaufnahmen

Die deutsche Männerstimme `de-DE-FlorianMultilingualNeural` ist für einen
ruhigen, reiferen Erzählklang langsamer (`-12%`) und tiefer (`-16Hz`) eingestellt.
93 Sätze liegen als einzelne MP3-Dateien in `assets/audio/` und zusätzlich
vollständig eingebettet in `index.html` vor. Nach dem Laden benötigt die
Sprachausgabe keine Internetverbindung. Die Zuordnung zu den unveränderten
sichtbaren Texten steht in `assets/audio/lenz-manifest.json`.

Abgedeckt sind Begrüßung, Hygieneschleuse, sechs Stations-Erklärungen und
Aufgaben, Wissenssätze, Übergänge, Maschinenanimationen und Quiz-Vorlesen.
Gedankenstriche erhalten 350 ms zusätzliche Stille. Für die Aussprache nutzt
der Generator „Konsche“/„Konschieren“; angezeigt werden weiterhin die
Originalbegriffe „Conche“/„Conchieren“. Die Begrüßung lautet „Hallo!“ ohne frei
eingegebenen Namen, damit Aufnahme und sichtbarer Text übereinstimmen.
Der Name auf der Urkunde bleibt erhalten. Im Quiz werden genau die sichtbare
Frage und die Antworten gesprochen, ohne zusätzliches „Oder“.

Die Mundbewegung und das Leiserstellen der Fabrikgeräusche folgen der Aufnahme.
Stationssperren werden nach ihrem tatsächlichen Ende aufgehoben. Überspringen
und Schließen stoppen die Aufnahme. Ohne Ton bleibt die bisherige Lesezeit.

Werkzeuge:

- `node tools/extract-lenz-texts.cjs`: Texte aus dem HTML übernehmen.
- `python tools/generate-lenz-audio.py`: MP3s mit edge-tts und FFmpeg erzeugen;
  unveränderte Aufnahmen werden beibehalten. Benötigt Internetzugang.
- `python tools/pack-lenz-audio.py`: Aufnahmen in das HTML einbetten.
- `node tools/check-lenz-audio.cjs`: Textabdeckung, MP3-Einbettung,
  Wiedergabereihenfolge, Ende/Abbruch, Stummschaltung/Lesezeit, Mundbewegung,
  Tonabsenkung und JavaScript-Syntax prüfen.
- `python tools/check-lenz-browser.py`: lokaler Chromium-/ChromeDriver-Test.
- `python tools/check-lenz-speech.py`: MP3-Dekodierung, Aussprachevorlagen
  und hörbare Gedankenstrichpause mit installiertem edge-tts/FFmpeg prüfen.


Validiert: alle 93 MP3s dekodieren fehlerfrei; 350-ms-Pause an einem
Gedankenstrich in der kodierten Datei nachgewiesen. Der Chromium-Test bestätigt
echte lokale Audiowiedergabe und Wiedergabeende, passende Sprechblase und
Mundbewegung, Stationssperre, Überspringen, Wiederholen, Lesezeit bei
Stummschaltung und Quiz-Vorlesen. Änderungen lokal gespeichert.


### Aussprache: „Wusstest du schon?“

Auf ausdrücklichen Wunsch bleibt Florian die Stimme von Meister Lenz.
Die kurze Einleitung „Wusstest du?“ wurde in Text und Aufnahme durch
„Wusstest du schon?“ ersetzt und mit derselben Stimme neu erzeugt.
Neue Datei: `assets/audio/lenz-b08ac7eb40d4.mp3`. Alle anderen Aufnahmen
bleiben unverändert. Die frühere Datei bleibt als Arbeitsstand im Assets-Ordner,
wird aber nicht mehr eingebettet oder abgespielt.


### Kurze Ausrufe mit deutschem Satzkontext

Florian bleibt unverändert die Stimme von Meister Lenz. Der verwendete
Edge-Sprachdienst stellt keine verlässliche explizite Sprachsperre über
SSML-lang bereit: https://github.com/rany2/edge-tts#custom-ssml.
Um die automatische Spracherkennung bei kurzen Ausrufen zu unterstützen,
werden „Geschafft!“, „Hallo!“, „Sauber!“, „Schön glatt!“, „Sehr gut!“,
„Riechst du das?“ und „Wusstest du schon?“ mit ihren vorhandenen deutschen
Folgesätzen synthetisiert. Anschließend wird ausschließlich der gewünschte
Ausruf anhand der WordBoundary-Zeitmarken aus dem Audio herausgeschnitten;
die weiteren Kontextwörter sind nicht Teil der ausgelieferten Aufnahme.
Texte, Stimme und die anderen Aufnahmen bleiben unverändert.

Die Quelldaten stehen unter `contexts` im Manifest; Schnittzeiten und
beibehaltene Wörter in `assets/audio/lenz-context-cuts.json`. Der Generator
und die Textextraktion berücksichtigen diese Kontexte bei erneuter Erzeugung.
Tests prüfen die Wortzuordnung, Schnittzeit vor dem nächsten Wort, MP3-Dauer,
Dekodierung und die weiterhin wortgetreue Einbettung. Dies ist eine Hilfe
gegen falsche Spracherkennung, keine garantierte Sprachsperre oder ein
Training der Stimme. Eine phonetische Hörprüfung wird dadurch nicht ersetzt.


### „Geschafft!“ aus dem Satzende ausschneiden

Auf ausdrücklichen Wunsch wird dieser Ausruf jetzt aus dem exakt gesprochenen
Satz „Das habe ich geschafft.“ gewonnen. Die ersten drei Wörter („Das habe ich“)
werden anhand ihrer Wortzeitmarken entfernt; das letzte Wort „geschafft“ bleibt
mit dem natürlichen Satzende erhalten. Die Stimme bleibt Florian.
Vollständiger Quellsatz: `assets/audio/lenz-geschafft-quellsatz.mp3`.
Im Spiel verwendeter Ausschnitt: `assets/audio/lenz-2f6ad66debc4.mp3`.
Das Manifest enthält die Auswahl unter `context_spans`; die Textübernahme
behält diesen Sonderfall bei. Tests prüfen den exakten Quellsatz, die drei
entfernten Wörter, das beibehaltene letzte Wort, die Schnittzeit und die
Dauer des Ergebnisses. Die anderen Aufnahmen bleiben unverändert.
