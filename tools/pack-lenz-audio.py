"""Embed Meister Lenz's assets/audio recordings in the standalone factory HTML."""
from pathlib import Path
import base64,json,re
root=Path(__file__).resolve().parents[1]
p=root/'index.html';s=p.read_text();m=json.loads((root/'assets/audio/lenz-manifest.json').read_text())
clips={c['text']:'data:audio/mpeg;base64,'+base64.b64encode((root/'assets/audio'/c['file']).read_bytes()).decode() for c in m['clips']}
runtime=(root/'tools/lenz-audio.js').read_text().replace('__LENZ_CLIPS__',json.dumps(clips,ensure_ascii=False,separators=(',',':')))
block='<script id="lenzAudioRuntime">'+runtime+'</script>'
if '<!-- LENZ_AUDIO_RUNTIME -->' in s:s=s.replace('<!-- LENZ_AUDIO_RUNTIME -->',block)
else:
 s,n=re.subn(r'<script id="lenzAudioRuntime">[\s\S]*?</script>',lambda _:block,s)
 if n!=1:raise ValueError('Expected one Meister Lenz audio runtime')
p.write_text(s);print(f'Embedded {len(clips)} Meister Lenz MP3 recordings.')
