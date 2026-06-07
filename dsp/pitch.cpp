#include <math.h>
#include <float.h>

#define SAMPLE_RATE 16000
#define MIN_FREQ 80
#define MAX_FREQ 1000

float detect_pitch_mpm(float* x, int N)
{
    if (N <= 0) return -1.0f;

    // remove DC + normalize
    float mean = 0.0f;
    for (int i = 0; i < N; i++)
        mean += x[i];
    mean /= N;

    float maxv = 0.0f;
    static float buffer[1024];

    for (int i = 0; i < N; i++)
    {
        buffer[i] = x[i] - mean;
        float a = fabsf(buffer[i]);
        if (a > maxv) maxv = a;
    }

    if (maxv < 1e-6f) return -1.0f;

    for (int i = 0; i < N; i++)
        buffer[i] /= maxv;

    int min_lag = SAMPLE_RATE / MAX_FREQ; // high freq limit
    int max_lag = SAMPLE_RATE / MIN_FREQ; // low freq limit

    float best_score = -FLT_MAX;
    int best_lag = -1;

    // MPM core: normalized autocorrelation
    for (int lag = min_lag; lag < max_lag; lag++)
    {
        float num = 0.0f;
        float den1 = 0.0f;
        float den2 = 0.0f;

        for (int i = 0; i < N - lag; i++)
        {
            float a = buffer[i];
            float b = buffer[i + lag];

            num += a * b;
            den1 += a * a;
            den2 += b * b;
        }

        float denom = sqrtf(den1 * den2) + 1e-9f;
        float score = num / denom;

        if (score > best_score)
        {
            best_score = score;
            best_lag = lag;
        }
    }

    if (best_lag <= 0) return -1.0f;

    return (float)SAMPLE_RATE / (float)best_lag;
}
