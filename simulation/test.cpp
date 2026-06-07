#include <iostream>
#include <cmath>

#include "../dsp/pitch.h"

const float SAMPLE_RATE = 16000.0f;
const int BUFFER_SIZE = 1024;

void generate_sine(float* buffer, float frequency)
{
    for (int i = 0; i < BUFFER_SIZE; i++)
    {
        buffer[i] = sinf(
            2.0f * M_PI *
            frequency *
            i /
            SAMPLE_RATE
        );
    }
}

int main()
{
    float buffer[BUFFER_SIZE];

    generate_sine(buffer, 440.0f);

    float detected =
        detect_pitch_mpm(buffer, BUFFER_SIZE);

    std::cout
        << "Expected: 440 Hz\n"
        << "Detected: "
        << detected
        << " Hz\n";

    return 0;
}
