/* Offline recordings; the packer inserts the original transcript -> MP3 mapping. */
(function(){
 const clips=__LENZ_CLIPS__;
 const clean=text=>String(text).replace(/<[^>]+>/g,'').replace(/\s+/g,' ').trim();
 const parts=text=>(Array.isArray(text)?text:[text]).flatMap(t=>(clean(t).match(/[^.!?…]+[.!?…]*/g)||[]).map(t=>t.trim()).filter(Boolean));
 const player=window.__lenzAudioPlayer||(window.__lenzAudioPlayer=new Audio());
 window.LenzAudio={parts,has:text=>parts(text).every(t=>clips[t]),speaking:false,
  play(text,done){
   let index=0,stopped=false,finished=false;const queue=parts(text);
   const end=()=>{if(stopped||finished)return;finished=true;this.speaking=false;if(done)done()};
   const next=()=>{
    if(stopped)return;if(index===queue.length){end();return}
    const text=queue[index++],src=clips[text];
    if(!src){console.error('Fehlende Meister-Lenz-Aufnahme:',text);end();return}
    let advanced=false;
    const advance=()=>{if(stopped||advanced)return;advanced=true;next()};
    player.src=src;player.preload='auto';player.onended=advance;
    player.onerror=()=>{console.error('Meister-Lenz-Aufnahme konnte nicht abgespielt werden:',text);end()};
    this.speaking=true;const promise=player.play();if(promise&&promise.catch)promise.catch(end);
   };
   next();
   return ()=>{stopped=true;this.speaking=false;player.onended=null;player.onerror=null;player.pause();player.removeAttribute('src');player.load()};
  }
 };
})();
