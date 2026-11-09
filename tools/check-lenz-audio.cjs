const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.join(__dirname,'..'),s=fs.readFileSync(path.join(root,'index.html'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'assets/audio/lenz-manifest.json'),'utf8'));
const clips=Object.fromEntries(manifest.clips.map(c=>[c.text,c.file]));
let player=null,plays=0,muted=false,completed=0,talking=false;const duck=[],timers=[];
class Audio{constructor(){player=this}play(){plays++;return Promise.resolve()}pause(){this.paused=true}removeAttribute(){this.src=''}load(){}}
const context={Audio,console,document:{querySelectorAll:()=>[{classList:{toggle(c,on){talking=on}}}]},Sfx:{isMuted:()=>muted,duck(on,lvl){duck.push({on,lvl})}},setTimeout(fn,ms){const t={fn,ms};timers.push(t);return t},clearTimeout(t){const i=timers.indexOf(t);if(i>=0)timers.splice(i,1)}};
context.window=context;
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'lenz-audio.js'),'utf8').replace('__LENZ_CLIPS__',JSON.stringify(clips)),context);
const audio=context.LenzAudio;
function covered(t){assert(audio.has(t),'Missing Lenz recording: '+t)}
for(const m of s.matchAll(/\b(?:intro|task|fact|cap):'((?:[^'\\]|\\.)*)'/g))covered(vm.runInNewContext("'"+m[1]+"'"));
const next=vm.runInNewContext(s.match(/const NEXT_LINE=(\[[\s\S]*?\]);/)[1]);next.forEach(covered);
for(const m of s.matchAll(/\bsay\('((?:[^'\\]|\\.)*)'\)/g))covered(vm.runInNewContext("'"+m[1]+"'"));
const greeting=s.match(/say\(`(Hallo![^`]+)`\)/)[1];covered(greeting);
const quiz=vm.runInNewContext(s.match(/const QUIZ=(\[[\s\S]*?\]);/)[1]);quiz.forEach(([q,opts])=>covered([q,...opts]));covered('Wusstest du schon?');
assert(s.includes("pendingFact='Wusstest du schon? '"));
assert(s.includes('<b>💡 Wusstest du schon?</b>'));
assert(!audio.has('Wusstest du?'));
assert.equal(manifest.voice,'de-DE-FlorianMultilingualNeural');
assert(!s.includes('SpeechSynthesisUtterance'),'No device-specific voice should be used');
vm.runInNewContext(s.slice(s.indexOf('let speakId='),s.indexOf('function hideGuide()')),context);
const first=manifest.clips.slice(0,3).map(c=>c.text),message=first.join(' ');
context.speak(message,()=>completed++,.4);assert(talking);assert(duck.at(-1).on);assert.equal(duck.at(-1).lvl,.4);
for(const text of first){assert.equal(player.src,clips[text]);assert.equal(completed,0);player.onended()}
assert.equal(completed,1);assert(!talking);assert(!duck.at(-1).on);assert(!audio.speaking);
context.speak(greeting,()=>completed++);const stale=player.onended;context.stopSpeech();stale();assert.equal(completed,1);assert(player.paused);assert(!talking);assert(!duck.at(-1).on);
const before=plays;muted=true;context.speak(greeting,()=>completed++);assert.equal(plays,before);assert(!talking);assert(timers.length===1&&timers[0].ms>1000);timers.shift().fn();assert.equal(completed,2);muted=false;
// Quiz options have their own recordings, with no inserted question or "Oder" text.
let quizDone=0;audio.play([quiz[0][0],...quiz[0][1]],()=>quizDone++);
for(const text of [quiz[0][0],...quiz[0][1]]){assert.equal(player.src,clips[text]);player.onended()}assert.equal(quizDone,1);
const embedded=JSON.parse(s.match(/const clips=(\{[^\n]+\});/)[1]);
for(const c of manifest.clips){const bytes=fs.readFileSync(path.join(root,'assets/audio',c.file));assert(bytes.length>1000);assert.equal(embedded[c.text],'data:audio/mpeg;base64,'+bytes.toString('base64'))}
for(const m of s.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);
console.log(`OK: ${manifest.clips.length} original Lenz texts, lesson/quiz/greeting coverage, exact embedded MP3 bytes, sequential playback, mute/read time, cancel, mouth animation, ambient ducking, script syntax.`);
