// Read the displayed lesson text directly from the HTML to avoid transcript drift.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const root=path.join(__dirname,'..'),s=fs.readFileSync(path.join(root,'index.html'),'utf8');
const texts=[];
for(const m of s.matchAll(/\b(?:intro|task|fact|cap):'((?:[^'\\]|\\.)*)'/g))texts.push(vm.runInNewContext("'"+m[1]+"'"));
const next=vm.runInNewContext(s.match(/const NEXT_LINE=(\[[\s\S]*?\]);/)[1]);texts.push(...next);
for(const m of s.matchAll(/\bsay\('((?:[^'\\]|\\.)*)'\)/g))texts.push(vm.runInNewContext("'"+m[1]+"'"));
const greeting='Hallo! Ich bin Meister Lenz und leite die Produktionshalle hier in der Schokoladenfabrik. Heute hilfst du mir. Zieh dir vorne am Eingang Kittel und Haube an, dann geht es los!';texts.push(greeting,'Wusstest du schon?');
const quiz=vm.runInNewContext(s.match(/const QUIZ=(\[[\s\S]*?\]);/)[1]);for(const [q,opts] of quiz)texts.push(q,...opts);
const clean=t=>String(t).replace(/<[^>]+>/g,'').replace(/\s+/g,' ').trim();
const parts=t=>(clean(t).match(/[^.!?…]+[.!?…]*/g)||[]).map(t=>t.trim()).filter(Boolean);
const clips=[...new Set(texts.flatMap(parts))].sort().map(text=>({text,file:'lenz-'+crypto.createHash('sha256').update(text).digest('hex').slice(0,12)+'.mp3'}));
// Give short calls their existing German follow-up sentences for language context.
const contexts={};
for(const t of texts){const first=parts(t)[0];if(['Hallo!','Geschafft!','Sauber!','Schön glatt!','Sehr gut!','Riechst du das?'].includes(first)&&parts(t).length>1)contexts[first]=clean(t)}
const firstFact=vm.runInNewContext("'"+s.match(/fact:'((?:[^'\\]|\\.)*)'/)[1]+"'");
contexts['Wusstest du schon?']='Wusstest du schon? '+firstFact;
contexts['Geschafft!']='Das habe ich geschafft.';
const context_spans={'Geschafft!':{first_word:3,word_count:1}};
const manifest={voice:'de-DE-FlorianMultilingualNeural',rate:'-12%',pitch:'-16Hz',dash_pause_ms:350,pronunciations:{Conchieren:'Konschieren',Conche:'Konsche'},contexts,context_spans,clips};
fs.writeFileSync(path.join(root,'assets/audio/lenz-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(`${clips.length} Meister Lenz sentences extracted from displayed lesson text.`);
