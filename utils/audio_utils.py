import pyaudio
import wave
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

def record_audio(path, duration=RECORD_SECONDS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print(f"[🎙️] Ghi âm {duration}s...")
    frames = [stream.read(CHUNK) for _ in range(0, int(RATE / CHUNK * duration))]
    stream.stop_stream(); stream.close(); p.terminate()
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def play_audio(path):
    if not os.path.exists(path): return print("[❌] Không tìm thấy file âm thanh.")
    wf = wave.open(path, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
    print("[🔊] Phát lại...")
    data = wf.readframes(CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream(); stream.close(); p.terminate()
