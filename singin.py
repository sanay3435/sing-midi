import numpy as np
import sounddevice as sd
import librosa
import time

class PitchDetector:
    def __init__(self, sample_rate=16000, chunk_size=2048):
        """
        Initialize the pitch detector
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Number of samples per analysis window
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_listening = False
        self.current_pitch = None
        self.current_confidence = 0.0
        
    def detect_pitch(self, audio_chunk):
        """
        Detect the pitch of an audio chunk using librosa
        
        Args:
            audio_chunk: numpy array of audio samples
            
        Returns:
            frequency (Hz), confidence (0-1)
        """
        # Use librosa's pyin algorithm for robust pitch detection
        # pyin = "probabilistic YIN" - very accurate for monophonic sources
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_chunk,
            fmin=80,      # Minimum frequency (Hz) - roughly E2 note
            fmax=400,     # Maximum frequency (Hz) - roughly G4 note
            sr=self.sample_rate
        )
        
        # Get the most recent valid pitch estimate
        # voiced_probs tells us confidence in the pitch detection
        if len(f0) > 0:
            # Find the last valid pitch (non-NaN value)
            valid_indices = ~np.isnan(f0)
            if np.any(valid_indices):
                last_valid_idx = np.where(valid_indices)[0][-1]
                frequency = f0[last_valid_idx]
                confidence = voiced_probs[last_valid_idx]
                return float(frequency), float(confidence)
        
        return None, 0.0
    
    def frequency_to_note(self, frequency):
        """
        Convert frequency (Hz) to note name and octave
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            note_name (str), midi_number (int)
        """
        if frequency is None or frequency <= 0:
            return "---", 0
        
        # A4 = 440 Hz = MIDI note 69
        # Formula: MIDI_note = 69 + 12 * log2(frequency / 440)
        midi_number = round(69 + 12 * np.log2(frequency / 440.0))
        
        # Note names
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_index = midi_number % 12
        octave = (midi_number // 12) - 1
        
        note_name = f"{note_names[note_index]}{octave}"
        return note_name, midi_number
    
    def audio_callback(self, indata, frames, time_info, status):
        """
        Callback function for real-time audio stream
        """
        if status:
            print(f"Audio error: {status}")
            return
        
        # Extract audio data
        audio_chunk = indata[:, 0]  # Get first channel if stereo
        
        # Detect pitch
        frequency, confidence = self.detect_pitch(audio_chunk)
        
        self.current_pitch = frequency
        self.current_confidence = confidence
    
    def start_listening(self):
        """Start real-time pitch detection from microphone"""
        self.is_listening = True
        print(f"Starting pitch detection... (Press Ctrl+C to stop)")
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Chunk size: {self.chunk_size} samples\n")
        print("Frequency (Hz) | Note  | Confidence")
        print("-" * 40)
        
        try:
            # Start audio stream
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self.audio_callback,
                latency='low'
            ):
                while self.is_listening:
                    if self.current_pitch is not None:
                        note_name, midi_num = self.frequency_to_note(self.current_pitch)
                        print(f"{self.current_pitch:>14.2f} | {note_name:>5} | {self.current_confidence:>10.3f}")
                    time.sleep(0.1)  # Update display 10 times per second
        
        except KeyboardInterrupt:
            print("\n\nStopped listening.")
            self.is_listening = False


if __name__ == "__main__":
    # Create detector with reasonable frequency range for human voice
    detector = PitchDetector(sample_rate=16000, chunk_size=2048)
    
    # Start listening
    detector.start_listening()
