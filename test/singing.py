import numpy as np
import sounddevice as sd
import librosa
import time
import keyboard

SAMPLE_RATE = 16000
CHUNK_SIZE = 2048

current_mode = 'single'
current_pitch = None
current_confidence = 0.0
current_volume = 0.0


def detect_pitch(audio_chunk):


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

def harmony(root,mode,octave):
    notesref = [
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B"
    ]
    root = notesref.index(root[:-1]) + 1
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
        midi = (i%12)-1
        key = notesref[midi]
        output.append(key + octave)
    return output

def harmony_mode():
    global current_mode
    if keyboard.is_pressed('1'):
        current_mode ='major'
    if keyboard.is_pressed('2'):
        current_mode ='minor'
    if keyboard.is_pressed('0'):
        current_mode='single'

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

    pitch, confidence = detect_pitch(audio_chunk)

    if confidence >= 0.1:
        current_pitch = pitch
        current_confidence = confidence


print("Starting pitch detection...")
print("Press Ctrl+C to stop\n")

print(" Frequency | Note | Confidence | Volume | Harmony | Output")
print("----------------------------------------------------------")

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
                
                print(
                    f"{current_pitch:10.2f} Hz | "
                    f"{note:5} | "
                    f"{current_confidence:.3f} | "
                    f"{current_volume:.4f} | "
                    f"{current_mode} | "
                    f"{harmony(note,current_mode,note[-1])} | "
                )

            time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopped.")
