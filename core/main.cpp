#include <iostream>
#include "dsp/pitch.h"
#include "filters/hysteresis.h"

#define N 1024

Hysteresis h;

// fake input for now
void get_audio(float* buffer, int N)
{
    for (int i = 0; i < N; i++)
        buffer[i] = (float)rand() / RAND_MAX * 2.0f - 1.0f;
}

float freq_to_midi(float freq)
{
    return 69.0f + 12.0f * log2f(freq / 440.0f);
}

int main()
{
    float buffer[N];

    while (true)
    {
        get_audio(buffer, N);

        float freq = detect_pitch_mpm(buffer, N);
        if (freq <= 0) continue;

        float midi_float = freq_to_midi(freq);
        int note = h.apply(midi_float);

        std::cout << "Note: " << note << std::endl;
    }
}
