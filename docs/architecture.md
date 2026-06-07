Microphone Input
     ->
Frame Buffer (1024 samples @ 16kHz)
     ->
Pitch Detection Engine (YIN / MPM)
     ->
Confidence Filter (voiced/unvoiced gating)
     ->
Frequency Smoothing (EMA)
     ->
Note Mapping (Hz → MIDI float)
     ->
Hysteresis Stabilizer (anti-jitter system)
     ->
MIDI Event Generator
     ->
USB MIDI Output (Teensy 4.1 target)
