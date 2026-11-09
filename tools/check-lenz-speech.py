"""Check rendered MP3s, vocabulary pronunciation preparation and dash pauses."""
import concurrent.futures,importlib.util,json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('speech',root/'tools/generate-lenz-audio.py');speech=importlib.util.module_from_spec(spec);spec.loader.exec_module(speech)
assert speech.speech_parts('Die „Conche“ rührt – beim Conchieren.')==['Die Konsche rührt','beim Konschieren.']
assert speech.speech_parts('Erst rösten - dann mahlen.')==['Erst rösten','dann mahlen.']
assert speech.speech_parts('Kakao-Bohnen')==['Kakao-Bohnen']
assert speech.speech_parts('Wusstest du schon?')==['Wusstest du schon?']
m=json.loads((root/'assets/audio/lenz-manifest.json').read_text());assert m['dash_pause_ms']==350
assert m['voice']=='de-DE-FlorianMultilingualNeural'
assert sum(c['text']=='Wusstest du schon?' for c in m['clips'])==1
sample=next(c for c in m['clips'] if c['text']=='Beim Mahlen wird es warm, die Kakaobutter schmilzt – deshalb wird alles dickflüssig.')
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(root/'assets/audio'/sample['file']),'-af','silencedetect=noise=-45dB:d=0.32','-f','null','-'],capture_output=True,text=True,check=True)
starts=[float(v) for v in re.findall(r'silence_start: ([\d.]+)',r.stderr)]
pauses=[float(v) for v in re.findall(r'silence_duration: ([\d.]+)',r.stderr)]
assert any(start>.3 and pause>=.34 for start,pause in zip(starts,pauses)),(starts,pauses)
# A short phrase is synthesized in its existing German paragraph, then cut at
# service-provided word boundaries so none of the extra context is audible.
cuts=json.loads((root/'assets/audio/lenz-context-cuts.json').read_text())
for text,context in m.get('contexts',{}).items():
    clip=next(c for c in m['clips'] if c['text']==text);cut=cuts[clip['file']]
    assert cut['context']==context and cut['text']==text
    assert speech.words(' '.join(cut['kept_words']))==speech.words(text)
    if text in m.get('context_spans',{}):
        if text=='Geschafft!':
            assert context=='Das habe ich geschafft.'
            assert speech.words(' '.join(cut['removed_words']))==['das','habe','ich']
            assert speech.words(' '.join(cut['kept_words']))==['geschafft']
        elif text=='Sauber!':
            assert context=='Das ist sauber! Bring die Kiste jetzt zu Station 2 zum Rösten.'
            assert speech.words(' '.join(cut['removed_words']))==['das','ist']
            assert cut['next_word']=='Bring'
            assert speech.words(' '.join(cut['kept_words']))==['sauber']
        assert cut['previous_word_end_seconds']<=cut['start_seconds']<=cut['word_start_seconds']
    else:
        assert cut['cut_seconds']<=cut['next_word_seconds']
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(root/'assets/audio'/clip['file'])],text=True))
    assert abs(duration-(cut['cut_seconds']-cut.get('start_seconds',0))-.12)<.15,(text,duration,cut)
assert 'Geschafft!' in m['contexts'] and len(m['contexts'])==7
def check(c):
 r=subprocess.run(['ffmpeg','-v','error','-i',str(root/'assets/audio'/c['file']),'-f','null','-'],capture_output=True)
 assert r.returncode==0,(c['file'],r.stderr)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(check,m['clips']))
print(f"OK: Conche/Conchieren pronunciation preparation, 350 ms dash pause in an encoded recording, {len(m['clips'])} MP3s decode without errors.")
