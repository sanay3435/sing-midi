#pragma once

class Hysteresis {
private:
    int last_midi = -1;

public:
    int apply(float midi_float);
};
