import numpy as np
import sounddevice as sd
import librosa
import time
import keyboard

mute = False


SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

current_mode = 'single'
current_pitch = None
current_confidence = 0.0
current_volume = 0.0
current_latency= 0.0





def detect_pitch_pyin(audio_chunk):


    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio_chunk,
        fmin=80,
        fmax=1000,
        sr=SAMPLE_RATE
    )

    valid = ~np.isnan(f0)

    if np.any(valid):
        latest_index = np.where(valid)[0][-1]

        frequency = f0[latest_index]
        confidence = voiced_probs[latest_index]

        return float(frequency), float(confidence)

    return None, 0.0

def detect_pitch_yin(audio_chunk):

    # remove DC offset
    audio = audio_chunk - np.mean(audio_chunk)

    # normalize
    if np.max(np.abs(audio)) < 1e-6:
        return None, 0.0

    audio = audio / np.max(np.abs(audio))

    # autocorrelation (core idea behind YIN)
    corr = np.correlate(audio, audio, mode='full')
    corr = corr[len(corr)//2:]

    # ignore very small lags (high frequencies limit)
    min_lag = int(SAMPLE_RATE / 1000)   # ~1000 Hz max
    max_lag = int(SAMPLE_RATE / 80)     # ~80 Hz min

    corr[:min_lag] = 0
    corr[max_lag:] = 0

    # find best match
    peak = np.argmax(corr)

    if peak <= 0:
        return None, 0.0

    frequency = SAMPLE_RATE / peak

    # simple confidence: strength of correlation peak
    confidence = 1.0

    return float(frequency), confidence

def detect_pitch_mpm(audio_chunk):
    import numpy as np

    audio = audio_chunk - np.mean(audio_chunk)

    if np.max(np.abs(audio)) < 1e-6:
        return None, 0.0

    audio = audio / np.max(np.abs(audio))

    # range limits (same idea as your other detector)
    min_lag = int(SAMPLE_RATE / 1000)   # ~1000 Hz
    max_lag = int(SAMPLE_RATE / 80)     # ~80 Hz

    best_lag = 0
    best_score = 0

    # normalized autocorrelation (core MPM idea)
    for lag in range(min_lag, max_lag):
        if lag >= len(audio):
            break

        segment1 = audio[:-lag]
        segment2 = audio[lag:]

        if len(segment1) == 0:
            continue

        score = np.dot(segment1, segment2) / len(segment1)

        if score > best_score:
            best_score = score
            best_lag = lag

    if best_lag == 0:
        return None, 0.0

    frequency = SAMPLE_RATE / best_lag

    # binary confidence (your requirement)
    confidence = 1.0

    return float(frequency), confidence

ACTIVE_DETECTOR = detect_pitch_mpm

def frequency_to_note(frequency):

    if frequency is None or frequency <= 0:
        return "---"

    midi = round(69 + 12 * np.log2(frequency / 440.0))

    notes = [
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B"
    ]

    note_name = notes[midi % 12]
    octave = (midi // 12) - 1

    return f"{note_name}{octave}"

def harmony(root,mode):
    notesref = ['C1', 'C#1', 'D1', 'D#1', 'E1', 'F1', 'F#1', 'G1', 'G#1', 'A1', 'A#1', 'B1',
 'C2', 'C#2', 'D2', 'D#2', 'E2', 'F2', 'F#2', 'G2', 'G#2', 'A2', 'A#2', 'B2',
 'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3',
 'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4',
 'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5',
 'C6', 'C#6', 'D6', 'D#6', 'E6', 'F6', 'F#6', 'G6', 'G#6', 'A6', 'A#6', 'B6',
 'C7', 'C#7', 'D7', 'D#7', 'E7', 'F7', 'F#7', 'G7', 'G#7', 'A7', 'A#7', 'B7',
 'C8', 'C#8', 'D8', 'D#8', 'E8', 'F8', 'F#8', 'G8', 'G#8', 'A8', 'A#8', 'B8',
 'C9', 'C#9', 'D9', 'D#9', 'E9', 'F9', 'F#9', 'G9', 'G#9', 'A9', 'A#9', 'B9']
    root = notesref.index(root) + 1
    notes = [root]
    output = []
    if mode == 'single':
        pass
    if mode == 'major':
        notes.append(root + 4)
        notes.append(root + 7)
    if mode =='minor':
        notes.append(root + 3)
        notes.append(root + 7)
    for i in notes:
        midi = i-1
        key = notesref[midi]
        output.append(key)
    return output

def harmony_mode():
    global current_mode
    global mute
    if keyboard.is_pressed('1'):
        current_mode ='major'
    if keyboard.is_pressed('2'):
        current_mode ='minor'
    if keyboard.is_pressed('0'):
        current_mode='single'
    if keyboard.is_pressed('m'):
        if mute:
            mute = False
        else:
            mute = True

def audio_callback(indata, frames, time_info, status):

    global current_pitch
    global current_confidence
    global current_volume

    if status:
        print(status)
        return

    audio_chunk = indata[:, 0]

   
    current_volume = np.sqrt(np.mean(audio_chunk ** 2))

    if current_volume < 0.01:
        return
    
    global current_latency

    start = time.perf_counter()

    pitch, confidence = ACTIVE_DETECTOR(audio_chunk)

    current_latency = (time.perf_counter() - start) * 1000

    if confidence >= 0.1:
        current_pitch = pitch
        current_confidence = confidence


print("Starting pitch detection...")
print("Press Ctrl+C to stop\n")

print(" Frequency | Note | Confidence | Volume | Harmony | Output | Latency")
print("--------------------------------------------------------------------")

try:
    with sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        callback=audio_callback
    ):

        while True:
            harmony_mode()
            
            if current_pitch is not None:

                note = frequency_to_note(current_pitch)
                if mute:
                    print('muted')
                else:
                    print(
                        f"{current_pitch:10.2f} Hz | "
                        f"{note:5} | "
                        f"{current_confidence:.3f} | "
                        f"{current_volume:.4f} | "
                        f"{current_mode} | "
                        f"{harmony(note,current_mode)} | "
                        f"{current_latency} ms"
                    )

            time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopped.")
