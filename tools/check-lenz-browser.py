"""Check actual local MP3 playback, lesson locking and mute in Chromium."""
from pathlib import Path
import json,subprocess,time,urllib.request
root=Path(__file__).resolve().parents[1]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def request(method,path,data=None):
    req=urllib.request.Request('http://localhost:9518'+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=30) as response:return json.load(response)['value']
log=Path('/tmp/lenz-chromedriver.log').open('w')
driver=subprocess.Popen(['chromedriver','--port=9518'],stdout=log,stderr=log);session=None
try:
    for _ in range(60):
        try:request('GET','/status');break
        except Exception:time.sleep(.1)
    session=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'chrome','goog:chromeOptions':{'binary':'/usr/bin/chromium','args':['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required','--user-data-dir=/tmp/fabrik-lenz-webdriver','--window-size=1100,900']}}}})['sessionId']
    prefix='/session/'+session
    def js(code):return request('POST',prefix+'/execute/sync',{'script':code,'args':[]})
    def wait(condition):
        for _ in range(150):
            if js('return '+condition):return
            time.sleep(.05)
        raise AssertionError('Timed out: '+condition)
    request('POST',prefix+'/url',{'url':(root/'index.html').as_uri()})
    wait("typeof LenzAudio==='object' && !!document.querySelector('#go')")
    js("window.lenzErrors=[];window.addEventListener('error',e=>lenzErrors.push(e.message));if(Sfx.isMuted())Sfx.toggle();hideModal();say('Geschafft!');")
    wait('LenzAudio.speaking && document.querySelector(".meister.talk")!==null')
    assert js('return document.querySelector("#say").textContent')=='Geschafft!'
    wait('__lenzAudioPlayer.readyState>=2 && __lenzAudioPlayer.currentTime>.02')
    assert js('return __lenzAudioPlayer.duration')>.3
    wait('!LenzAudio.speaking');assert js("return heard.has('Geschafft!')")
    assert not js('return !!document.querySelector(".meister.talk")')
    js('setTeacher(true);openStation(0)')
    wait('LenzAudio.speaking');assert js('return document.querySelector("#area").classList.contains("wait")')
    js('document.querySelector("#wskip").click()');wait('!LenzAudio.speaking')
    assert not js('return document.querySelector("#area").classList.contains("wait")')
    assert js('return __lenzAudioPlayer.paused')
    js('document.querySelector("#spk").click()');wait('LenzAudio.speaking')
    js('hideModal();if(!Sfx.isMuted())Sfx.toggle();openStation(1)')
    assert not js('return LenzAudio.speaking');assert not js('return !!document.querySelector(".meister.talk")')
    assert js('return document.querySelector("#wtxt").textContent').startswith('📖')
    js('document.querySelector("#wskip").click();hideModal();if(Sfx.isMuted())Sfx.toggle();quiz(0,0);document.querySelector("#spk").click()')
    wait('LenzAudio.speaking');js('stopSpeech()');assert not js('return window.lenzErrors')
    print('Browser OK: actual MP3 playback and completion, matching speech bubble, mouth animation, station lock, skip, repeat, muted reading mode and quiz playback.')
finally:
    if session:
        try:request('DELETE','/session/'+session)
        except Exception:pass
    driver.terminate();driver.wait(timeout=10);log.close()
