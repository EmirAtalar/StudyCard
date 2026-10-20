"""Natural speech, versioned cache and bounded background prefetch."""
import asyncio
import base64
import hashlib
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from duocards.languages import get_language_code
from duocards.paths import CACHE_DIR as PROFILE_CACHE_DIR
from http.client import HTTPException
import logging
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

CACHE_DIR = str(PROFILE_CACHE_DIR / 'audio')
logger=logging.getLogger(__name__)


def _is_mp3(payload):
    return payload.startswith(b'ID3') or (len(payload)>=2 and payload[0]==0xff and payload[1]&0xe0==0xe0)


def _is_audio_file(path):
    try:
        with open(path,'rb') as stream:
            return _is_mp3(stream.read(3))
    except OSError:
        return False


def _fetch_rpc_audio(text, lang):
    """Use Translate's speech RPC when its legacy MP3 endpoint fails.

    The request format is also used by gTTS; no extra runtime package is needed.
    """
    parameters = json.dumps([text, lang, None, 'null'])
    body = urllib.parse.urlencode({'f.req': json.dumps([[['jQ1olc', parameters, None, 'generic']]])}).encode()
    request = urllib.request.Request(
        'https://translate.google.com/_/TranslateWebserverUi/data/batchexecute',
        data=body,
        headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://translate.google.com/',
                 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'})
    with urllib.request.urlopen(request, timeout=6) as response:
        payload = response.read(4_000_000).decode('utf-8')
    # Responses contain an anti-XSSI prefix and length lines before JSON frames.
    for line in payload.splitlines():
        try:
            records = json.loads(line)
        except ValueError:
            continue
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, list) or len(record)<3 or record[:2]!=['wrb.fr', 'jQ1olc']:
                continue
            if not isinstance(record[2], str):
                continue
            try:
                result = json.loads(record[2])
                if not isinstance(result, list) or not result or not isinstance(result[0], str):
                    continue
                audio = base64.b64decode(result[0], validate=True)
            except ValueError:
                continue
            if _is_mp3(audio):
                return audio
    raise ValueError('Speech RPC returned no MP3 audio')


def _fetch_dictionary_audio(text, lang):
    """Use a recorded pronunciation only when it matches the complete word."""
    word=text.casefold().replace('i\u0307','i')
    if lang!='en' or not word or not any(c.isalpha() for c in word) or not all(c.isalpha() or c in "'-" for c in word):
        raise ValueError('No dictionary recording for this text')
    request=urllib.request.Request(
        'https://api.dictionaryapi.dev/api/v2/entries/en/'+urllib.parse.quote(word,safe=''),
        headers={'User-Agent':'StudyCard/1.0'})
    with urllib.request.urlopen(request,timeout=6) as response:
        entries=json.loads(response.read(1_000_000))
    if not isinstance(entries,list):
        raise ValueError('Dictionary returned no pronunciations')
    urls=[]
    for entry in entries:
        if not isinstance(entry,dict):
            continue
        entry_word=entry.get('word')
        phonetics=entry.get('phonetics')
        if not isinstance(entry_word,str) or entry_word.casefold()!=word or not isinstance(phonetics,list):
            continue
        for phonetic in phonetics:
            if not isinstance(phonetic,dict):
                continue
            url=phonetic.get('audio','')
            if not isinstance(url,str):
                continue
            if url.startswith('//'):
                url='https:'+url
            if urllib.parse.urlparse(url).scheme=='https' and url not in urls:
                urls.append(url)
    for url in urls[:3]:
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'StudyCard/1.0'})
            with urllib.request.urlopen(request,timeout=6) as response:
                payload=response.read(2_000_000)
            if _is_mp3(payload):
                return payload
        except (OSError,ValueError,HTTPException) as error:
            if isinstance(error,urllib.error.HTTPError):
                error.close()
    raise ValueError('Dictionary returned no matching MP3 recording')


def _fetch_online_audio(text,lang):
    """Try alternate speech sources when an endpoint fails."""
    last_error=None
    for attempt in range(2):
        try:
            url='https://translate.google.com/translate_tts?'+urllib.parse.urlencode(
                dict(ie='UTF-8',tl=lang,client='tw-ob',q=text))
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(request,timeout=6) as response:
                payload=response.read(2_000_000)
            if not _is_mp3(payload):
                raise ValueError('Speech service returned no MP3 audio')
            return payload
        except (OSError,ValueError,HTTPException) as error:
            last_error=error
            if isinstance(error,urllib.error.HTTPError):
                error.close()
                # A denied or rate-limited request will not recover immediately.
                if 400<=error.code<500:
                    break
            if attempt==0:
                time.sleep(.25)
    try:
        return _fetch_rpc_audio(text,lang)
    except (OSError,ValueError,HTTPException) as error:
        if isinstance(error,urllib.error.HTTPError):
            error.close()
        last_error=error
    try:
        return _fetch_dictionary_audio(text,lang)
    except (OSError,ValueError,HTTPException) as error:
        if isinstance(error,urllib.error.HTTPError):
            error.close()
    try:
        url='https://translate.googleapis.com/translate_tts?'+urllib.parse.urlencode(
            dict(ie='UTF-8',tl=lang,client='gtx',q=text))
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=6) as response:
            payload=response.read(2_000_000)
        if _is_mp3(payload):
            return payload
        raise ValueError('Alternate speech service returned no MP3 audio')
    except (OSError,ValueError,HTTPException) as error:
        if isinstance(error,urllib.error.HTTPError):
            error.close()
        raise error from last_error


def _speech_chunks(text, limit=100):
    """Bound online fallback requests while keeping whole words together."""
    remaining=text.strip()
    while remaining:
        end=min(limit,len(remaining))
        if end<len(remaining):
            space=remaining.rfind(' ',0,end+1)
            if space>0:
                end=space
        yield remaining[:end]
        remaining=remaining[end:].lstrip()


def _get_cache_path(text,lang='en'):
    Path(CACHE_DIR).mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(f'natural-v2:{lang}:{text.strip()}'.encode()).hexdigest()
    return str(Path(CACHE_DIR)/(key+'.mp3'))


class AudioPlayer(QObject):
    state_changed=pyqtSignal(str)
    request_state_changed=pyqtSignal(int,str)
    def __init__(self):
        super().__init__()
        self.mpv_path=shutil.which('mpv')
        self.ffplay_path=shutil.which('ffplay')
        self.espeak_path=shutil.which('espeak-ng') or shutil.which('espeak')
        self._current_process=None
        self._lock=threading.Lock()
        self._generation=0
        self._downloads={}
        self._prefetch_pool=ThreadPoolExecutor(max_workers=3,thread_name_prefix='speech-cache')

    def stop(self):
        with self._lock:
            self._generation+=1
            generation=self._generation
            process=self._current_process
            self._current_process=None
            if process and process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass
        self._emit_state('idle',generation)

    def _emit_state(self,state,generation):
        self.state_changed.emit(state)
        self.request_state_changed.emit(generation,state)

    def play_pronunciation(self,text,lang='en',speed=None):
        if not text or not text.strip():
            return
        from duocards.settings import settings
        speed = settings.get('speech_speed', 1.0) if speed is None else speed
        lang=get_language_code(lang)
        self.stop()
        with self._lock:
            generation=self._generation
        self._emit_state('loading',generation)
        threading.Thread(target=self._play_worker,args=(text.strip(),lang,max(.5,min(2.,float(speed))),generation),daemon=True).start()
        return generation

    def play_sequence(self, items, speed=1.0, pause_ms=500):
        self.stop()
        with self._lock:
            generation = self._generation
        def run():
            for index, (text, lang) in enumerate(items):
                if not self._is_current(generation):
                    return
                self._emit_state('loading',generation)
                self._play_worker(text, get_language_code(lang), speed, generation)
                if index + 1 < len(items):
                    deadline = time.monotonic() + pause_ms / 1000
                    while time.monotonic() < deadline:
                        if not self._is_current(generation):
                            return
                        time.sleep(min(.05, max(0, deadline-time.monotonic())))
        threading.Thread(target=run, daemon=True, name='table-speech').start()

    def _is_current(self,generation):
        with self._lock:
            return generation==self._generation

    def prefetch(self, text, lang='en'):
        from duocards.settings import settings
        if not settings.get('audio_prefetch', True):
            return
        if text and text.strip() and (self.mpv_path or self.ffplay_path):
            self._prepare(text.strip(),get_language_code(lang))

    def _prepare(self,text,lang,foreground=False):
        key=(text,lang)
        download_here=False
        with self._lock:
            future=self._downloads.get(key)
            if future is not None and future.done():
                try:
                    if not future.result() or not _is_audio_file(_get_cache_path(text,lang)):
                        future=None
                except Exception:
                    future=None
            # A click must not wait behind unrelated background downloads.
            # Promote queued prefetches; share a download that already started.
            if future is None or (foreground and future.cancel()):
                if foreground:
                    future=Future()
                    future.set_running_or_notify_cancel()
                    download_here=True
                else:
                    future=self._prefetch_pool.submit(self._download,text,lang)
                self._downloads[key]=future
                # Finished futures need no unbounded retention.
                if len(self._downloads)>256:
                    self._downloads={k:v for k,v in self._downloads.items() if not v.done() or k==key}
        if download_here:
            try:
                future.set_result(self._download(text,lang))
            except Exception as error:
                future.set_exception(error)
        return future

    def _download(self,text,lang):
        try:
            cache_file=_get_cache_path(text,lang)
            if _is_audio_file(cache_file):
                return True
            temp_file=cache_file+f'.{threading.get_ident()}.part'
            # Earlier releases used MD5 names for the same natural Google audio.
            # Only reuse short text: old long requests could contain truncated speech.
            legacy_key=hashlib.md5(f'{lang}_{text.strip().lower()}'.encode()).hexdigest()
            legacy_file=str(Path(CACHE_DIR)/(legacy_key+'.mp3'))
            if len(text)<=100 and _is_audio_file(legacy_file):
                shutil.copyfile(legacy_file,temp_file)
                os.replace(temp_file,cache_file)
                return True
            # Prefer neural voices when edge-tts is installed; keep online natural
            # speech available in a plain stdlib installation too.
            voices={'en':'en-US-AriaNeural','tr':'tr-TR-EmelNeural','de':'de-DE-KatjaNeural',
                    'es':'es-ES-ElviraNeural','fr':'fr-FR-DeniseNeural','it':'it-IT-ElsaNeural',
                    'ja':'ja-JP-NanamiNeural','zh':'zh-CN-XiaoxiaoNeural','pt':'pt-BR-FranciscaNeural'}
            if lang in voices:
                try:
                    import edge_tts
                    async def synthesize():
                        await asyncio.wait_for(edge_tts.Communicate(text,voices[lang],connect_timeout=5,receive_timeout=8).save(temp_file),12)
                    asyncio.run(synthesize())
                except Exception:
                    Path(temp_file).unlink(missing_ok=True)
            if not _is_audio_file(temp_file):
                audio=bytearray()
                for chunk in _speech_chunks(text):
                    payload=_fetch_online_audio(chunk,lang)
                    # Each chunk has its own retry budget, so a long sentence
                    # is never cut off by a short whole-request deadline.
                    if not payload:
                        return False
                    audio.extend(payload)
                Path(temp_file).write_bytes(audio)
            os.replace(temp_file,cache_file)
            return True
        except (OSError,ValueError,HTTPException) as error:
            logger.warning('Could not prepare %s speech: %s',lang,error)
            return False
        finally:
            if 'temp_file' in locals():
                try: Path(temp_file).unlink(missing_ok=True)
                except OSError: pass

    def _play_worker(self,text,lang,speed,generation):
        if not self._is_current(generation):
            return
        try:
            cache_file=_get_cache_path(text,lang)
        except OSError:
            cache_file=''
        if cache_file and not _is_audio_file(cache_file) and (self.mpv_path or self.ffplay_path):
            future=self._prepare(text,lang,foreground=True)
            while self._is_current(generation):
                try:
                    future.result(timeout=.1)
                    break
                except TimeoutError:
                    continue
                except Exception as error:
                    logger.warning('Speech download failed: %s',error)
                    break
        if not self._is_current(generation):
            return
        if _is_audio_file(cache_file) and self.mpv_path:
            from duocards.settings import settings
            cmd=[self.mpv_path,'--no-video','--really-quiet',f'--speed={speed}',f"--volume={settings.get('speech_volume', 100)}",cache_file]
        elif _is_audio_file(cache_file) and self.ffplay_path:
            from duocards.settings import settings
            cmd=[self.ffplay_path,'-nodisp','-autoexit','-loglevel','quiet','-volume',str(settings.get('speech_volume', 100)),'-af',f'atempo={speed}',cache_file]
        else:
            if self._is_current(generation):
                self._emit_state('unavailable',generation)
            return
        try:
            with self._lock:
                if generation!=self._generation:
                    return
                process=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                self._current_process=process
            if self._is_current(generation):
                self._emit_state('playing',generation)
            returncode=process.wait()
            if self._is_current(generation):
                self._emit_state('idle' if returncode==0 else 'error',generation)
        except OSError:
            if self._is_current(generation):
                self._emit_state('error',generation)
        finally:
            with self._lock:
                if generation==self._generation:
                    self._current_process=None


audio_player=AudioPlayer()
