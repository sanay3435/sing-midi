#include "hysteresis.h"

int Hysteresis::apply(float midi_float)
{
    if (last_midi < 0)
        last_midi = (int)(midi_float + 0.5f);

    float lower = last_midi - 0.35f;
    float upper = last_midi + 0.65f;

    if (midi_float > upper)
        last_midi++;

    else if (midi_float < lower)
        last_midi--;

    return last_midi;
}
