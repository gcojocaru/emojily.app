# HISTORICAL GENERATOR: no longer produces the active recap palette.
# Use scripts/prepare_recap_audio.py; provenance is in MoodRecap/Audio/CREDITS.md.

"""Generates the recap's bed — the loop under the whole story.

**Third pass. Bright, not eerie.** The first was a Dsus9 drone; the second made
it major, and the note back was that it still felt creepy and slow. Three
specific things were doing that, and all three are gone:

1. **The beating.** The channels were detuned ±0.28 Hz. On an 87 Hz root that is
   a 0.56 Hz beat — a throb every 1.8 seconds, which is the exact sound of a
   horror drone. Stereo width now comes from a **phase offset** instead, which
   widens without wobbling.
2. **The breathing.** Amplitude swung 38% over four-to-eight second cycles. Slow
   swells on a low pad is a held breath. The movement is now shallow (12%) and
   quicker, so it shimmers rather than looms.
3. **The register.** The weight sat on F2/C3, down where a pad turns into a
   rumble on a phone speaker. The chord is up an octave and the lowest voice is
   a light C3 rather than a heavy F2.

And one thing added: **sparse shimmer**. Single soft bell notes from the chord,
placed on a slow grid with gaps, never twice in a row on the same pitch. That is
what makes it read as *bright* rather than merely major — a still pad, however
happy its chord, sounds like waiting. There is still **no tune**: the notes are
chord tones in a seeded order, and nothing repeats inside the loop.

**C major add 9** — the plainest bright chord there is. No major seventh (dreamy,
jazzy, halfway to melancholy) and no suspension (unresolved, which is where this
started).

Seamless by construction: every frequency is snapped to a whole number of cycles
per loop, so the last sample meets the first exactly. Shimmer notes that would
run past the end wrap around to the start.

48 kHz stereo, matching every other generated asset, so the exporter's
composition never resamples mid-track.

    python3 docs/recap-bed-generator.py
    afconvert -f m4af -d aac -b 128000 bed.wav \\
        EveryDayEmoji/MoodRecap/Audio/recap-bed.m4a
"""

import math
import struct
import wave

RATE = 48000
SECONDS = 32.0            # a touch longer than the longest story (35s loops once)
N = int(RATE * SECONDS)


def snap(freq):
    """Nearest frequency with a whole number of cycles in the loop.

    Without this the loop point is a phase discontinuity — a click, or at these
    levels a soft thump every 32 seconds. The shift is at most 0.016 Hz, which
    is inaudible and worth far more than the click.
    """
    return round(freq * SECONDS) / SECONDS


# C major add 9, voiced from C3 up. The third (E4) is what makes it bright; the
# ninth (D5) keeps it from sounding like a fanfare; the two Cs either end give it
# somewhere to sit without weight down low.
PARTIALS = [
    (snap(130.81), 0.20, 6),    # C3   light root
    (snap(196.00), 0.16, 5),    # G3   fifth
    (snap(329.63), 0.15, 7),    # E4   major third — the bright one
    (snap(493.88), 0.075, 9),   # B4   colour, quiet enough not to be a 7th chord
    (snap(587.33), 0.060, 4),   # D5   the ninth
    (snap(783.99), 0.030, 11),  # G5   air
]

# Chord tones for the shimmer, two octaves above the pad's centre. Anything not
# in the chord would be a melody note, and a melody is a hook.
SHIMMER = [snap(f) for f in (1046.50, 1318.51, 1567.98, 2093.00)]   # C6 E6 G6 C7


class Rand:
    """Deterministic LCG, same as the cue generator's — regenerating this file
    has to produce the same bytes or a changed asset stops meaning a changed
    script."""

    def __init__(self, seed):
        self.state = seed

    def next(self):
        self.state = (1664525 * self.state + 1013904223) % (2 ** 32)
        return self.state / (2 ** 32)


def pad(buf):
    for i in range(N):
        t = i / RATE
        left = right = 0.0
        for freq, amp, lfo_cycles in PARTIALS:
            # Shallow and quicker than before: 12% either side, so the chord
            # moves without ever seeming to inhale.
            lfo = 0.88 + 0.12 * math.sin(2 * math.pi * lfo_cycles * t / SECONDS)
            phase = 2 * math.pi * freq * t
            # Width from a phase offset rather than a detune: the two channels
            # stay exactly in tune, so there is no beating anywhere.
            left += amp * lfo * math.sin(phase)
            right += amp * lfo * math.sin(phase + 0.42)
            # One quiet octave partial, so it is a chord rather than a set of
            # test tones.
            left += amp * 0.14 * lfo * math.sin(phase * 2)
            right += amp * 0.14 * lfo * math.sin(phase * 2 + 0.30)
        buf[i] = (left, right)


def shimmer(buf, rand):
    """Single soft bell notes, on a slow grid with gaps.

    The grid is 1.6s and roughly half the slots are empty, which is what keeps
    it from turning into a pulse. Two rules stop it becoming a tune: chord tones
    only, and never the same pitch twice running.
    """
    grid = 1.6
    length = 2.2
    previous = -1
    at = 0.4

    while at < SECONDS:
        if rand.next() < 0.55:
            index = int(rand.next() * len(SHIMMER))
            if index == previous:
                index = (index + 1) % len(SHIMMER)
            previous = index

            freq = SHIMMER[index]
            amp = 0.030 + 0.020 * rand.next()
            pan = (rand.next() - 0.5) * 1.2
            left_gain = math.sqrt((1.0 - pan) * 0.5)
            right_gain = math.sqrt((1.0 + pan) * 0.5)
            start = int(at * RATE)

            for j in range(int(length * RATE)):
                t = j / RATE
                # Long attack, long decay: a struck bell has an edge, and an
                # edge every 1.6 seconds would be a rhythm.
                env = min(1.0, t / 0.09) * math.exp(-t / 0.55)
                v = (math.sin(2 * math.pi * freq * t) * 0.8
                     + math.sin(2 * math.pi * freq * 2 * t) * 0.12) * env * amp
                # Wrap past the loop point instead of truncating, so the loop
                # has no seam and no gap in the shimmer either.
                index_out = (start + j) % N
                l, r = buf[index_out]
                buf[index_out] = (l + v * left_gain, r + v * right_gain)

        at += grid


buf = [(0.0, 0.0)] * N
pad(buf)
shimmer(buf, Rand(90311))

peak = max(max(abs(l), abs(r)) for l, r in buf)
# Loud enough to be heard under a phone speaker in a room, quiet enough that the
# cues still land on top of it.
gain = (0.30 / peak) if peak > 0 else 0.0

frames = bytearray()
total = 0.0
for l, r in buf:
    left, right = l * gain, r * gain
    frames += struct.pack("<hh", int(left * 32767), int(right * 32767))
    total += left * left + right * right

with wave.open("bed.wav", "w") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(bytes(frames))

rms = math.sqrt(total / (2 * N))
seam = max(abs(buf[0][0] - buf[-1][0]), abs(buf[0][1] - buf[-1][1])) * gain
print(f"bed.wav: {SECONDS:.1f}s  peak {20 * math.log10(0.30):.1f} dBFS"
      f"  avg {20 * math.log10(rms):.1f} dBFS  loop seam {seam:.5f}")
