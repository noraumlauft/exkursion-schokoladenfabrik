"""Render Meister Lenz texts with natural cocoa vocabulary and audible dash pauses.
Requires edge-tts and ffmpeg. Existing unchanged recordings are retained.
"""
import argparse,asyncio,hashlib,json,re,tempfile,wave
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
DASH=re.compile(r'\s*[–—]\s*|\s+-\s+')
def speech_parts(text):
    # This changes pronunciation only; the displayed transcript stays unchanged.
    return [p.strip().replace('Conchieren','Konschieren').replace('Conche','Konsche').replace('„','').replace('“','') for p in DASH.split(text) if p.strip()]
async def command(*args):
    proc=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    out,err=await proc.communicate()
    if proc.returncode:raise RuntimeError(err.decode())
    return out
def words(text):
    return re.findall(r'\w+',text.casefold())
async def render_part(part,manifest,mp3):
    context=manifest.get('contexts',{}).get(part)
    if not context:
        await edge_tts.Communicate(part,manifest['voice'],rate=manifest['rate'],pitch=manifest['pitch']).save(str(mp3))
        return await command('ffmpeg','-v','error','-i',str(mp3),'-f','s16le','-ar','24000','-ac','1','pipe:1'),None
    span=manifest.get('context_spans',{}).get(part)
    if not span:assert context.startswith(part+' '),(part,context)
    spoken=' '.join(speech_parts(context))
    boundaries=[]
    with mp3.open('wb') as out:
        async for chunk in edge_tts.Communicate(spoken,manifest['voice'],rate=manifest['rate'],pitch=manifest['pitch'],boundary='WordBoundary').stream():
            if chunk['type']=='audio':out.write(chunk['data'])
            elif chunk['type']=='WordBoundary':boundaries.append(chunk)
    count=len(words(part));first=span['first_word'] if span else 0
    if span:assert span['word_count']==count
    kept=boundaries[first:first+count]
    assert len(kept)==count and words(' '.join(b['text'] for b in kept))==words(part),(part,boundaries)
    pcm=await command('ffmpeg','-v','error','-i',str(mp3),'-f','s16le','-ar','24000','-ac','1','pipe:1')
    start=0
    if span:
        # Keep the end of the exact requested sentence, removing "Das habe ich".
        assert first>0 and first+count==len(boundaries),(part,boundaries)
        previous_end=(boundaries[first-1]['offset']+boundaries[first-1]['duration'])/10_000_000
        word_start=kept[0]['offset']/10_000_000
        start=max(previous_end,word_start-.015)
        end=len(pcm)/2/24000
        mp3.with_name('source-sentence.mp3').write_bytes(mp3.read_bytes())
        audit={'removed_words':[b['text'] for b in boundaries[:first]],'previous_word_end_seconds':previous_end,'word_start_seconds':word_start,'next_word':None,'next_word_seconds':None}
    else:
        assert len(boundaries)>count,(part,boundaries)
        last_end=(kept[-1]['offset']+kept[-1]['duration'])/10_000_000
        next_start=boundaries[count]['offset']/10_000_000
        assert next_start>=last_end,(last_end,next_start)
        end=last_end+min(.18,(next_start-last_end)/2)
        audit={'next_word':boundaries[count]['text'],'next_word_seconds':next_start}
    # Only the selected word span is delivered, with its natural sentence ending.
    pcm=pcm[int(start*24000)*2:int(end*24000)*2]+bytes(int(.12*24000)*2)
    return pcm,{'text':part,'context':context,'kept_words':[b['text'] for b in kept],'start_seconds':start,'cut_seconds':end,**audit}
async def main(manifest_path=None):
    manifest_path=Path(manifest_path) if manifest_path else ROOT/'assets/audio/lenz-manifest.json'
    folder=manifest_path.parent
    manifest=json.loads(manifest_path.read_text())
    state_path=folder/manifest_path.name.replace('-manifest.json','-render-state.json')
    state=json.loads(state_path.read_text()) if state_path.exists() else {}
    cuts_path=folder/'lenz-context-cuts.json'
    cuts=json.loads(cuts_path.read_text()) if cuts_path.exists() else {}
    sem=asyncio.Semaphore(3)
    async def render(clip):
        target=folder/clip['file'];text=clip['text']
        leading_dash=bool(re.match(r'^\s*[–—-](?:\s|$)',text))
        context=manifest.get('contexts',{}).get(text)
        version=('Lenz-context-v2-span:'+context+json.dumps(manifest['context_spans'][text],sort_keys=True)) if text in manifest.get('context_spans',{}) else ('Lenz-context-v1:'+context) if context else ('Lenz-Conche-v1-leading' if leading_dash else 'Lenz-Conche-v1')
        signature=hashlib.sha256(json.dumps([text,manifest['voice'],manifest['rate'],manifest['pitch'],manifest.get('dash_pause_ms',350),version]).encode()).hexdigest()
        if target.exists() and target.stat().st_size>1000 and state.get(clip['file'])==signature:
            state[clip['file']]=signature;return
        async with sem:
            for attempt in range(4):
                try:
                    with tempfile.TemporaryDirectory(prefix='lenz-speech-') as tmpdir:
                        parts=speech_parts(text);pcm=[]
                        for i,part in enumerate(parts):
                            mp3=Path(tmpdir)/f'{i}.mp3'
                            audio,cut=await render_part(part,manifest,mp3)
                            pcm.append(audio)
                            if cut:
                                cuts[clip['file']]=cut
                                if cut.get('removed_words'):
                                    (folder/'lenz-geschafft-quellsatz.mp3').write_bytes(mp3.with_name('source-sentence.mp3').read_bytes())
                        silence=bytes(int(24000*manifest.get('dash_pause_ms',350)/1000)*2)
                        wav=Path(tmpdir)/'speech.wav'
                        with wave.open(str(wav),'wb') as out:
                            out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes((silence if leading_dash else b'')+silence.join(pcm))
                        result=Path(tmpdir)/'speech.mp3'
                        await command('ffmpeg','-v','error','-i',str(wav),'-codec:a','libmp3lame','-b:a','64k',str(result))
                        target.write_bytes(result.read_bytes())
                    state[clip['file']]=signature
                    print(clip['file'],flush=True);return
                except Exception:
                    if attempt==3:raise
                    await asyncio.sleep(2*(attempt+1))
    await asyncio.gather(*(render(clip) for clip in manifest['clips']))
    state_path.write_text(json.dumps(state,indent=2)+'\n')
    cuts_path.write_text(json.dumps(cuts,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,help='Audio manifest; defaults to Meister Lenz')
    asyncio.run(main(parser.parse_args().manifest))
