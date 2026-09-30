# HISTORICAL GENERATOR: no longer produces the active recap palette.
# Use scripts/prepare_recap_audio.py; provenance is in MoodRecap/Audio/CREDITS.md.

"""Generates every recap cue: the paper-and-air palette, plus the one chime.

Same approach as `recap-bed-generator.py`, and for the same reason: an exported
recap ends up on other people's feeds, so anything with a licence attached is a
liability that travels. Original synthesis has no licence to travel with it —
and since this script now writes the whole set, the folder no longer carries a
third-party sample at all.

**The palette is paper, card and air.** The first pass reached for mechanism —
a ratcheting counter, a hard block landing — and the note back was that it
sounded like winding a mechanical clock, or cocking a weapon. That is the wrong
instrument for a private mood journal. Everything here is made of soft noise
shaped into things that are handled rather than operated: a card riffled, a page
turned, a breath. Slightly mechanical is fine — *paper* is slightly mechanical —
but nothing is allowed to ring, click or ratchet.

**One bell, once.** `chime` plays on the intro emoji and nowhere else. A
notification tone is a strong sound and the story is thirty seconds long; heard
three times it stops being an arrival and starts being an alert.

Levels are baked into the files rather than trimmed at playback, because the
exporter muxes the cues at their own level while the live player used to trim
them — the two mixes drifted apart. Peaks below are the mastered targets.

Deterministic on purpose — a seeded LCG rather than `random`, so regenerating
produces byte-identical output and a changed asset is always a changed script.
Writes WAV; `afconvert` makes the m4a:

    python3 docs/recap-cue-generator.py
    for f in recap-*.wav; do
        afconvert -f m4af -d aac -b 128000 "$f" "EveryDayEmoji/MoodRecap/Audio/${f%.wav}.m4a"
    done

Briefs are in `docs/recap-sound-design.md`.
"""

import math
import struct
import wave

# 48 kHz stereo is the house format: the exporter muxes every one of these into
# one composition, and matching rates keeps AVFoundation from resampling or
# meeting a channel-layout change mid-track. Cues the briefs call mono are
# written dual-mono — "mono" there means "don't move it in the image", which a
# centred pair satisfies.
RATE = 48000


# --- helpers ---------------------------------------------------------------

class Rand:
    """Deterministic LCG. Numerical Recipes constants."""

    def __init__(self, seed):
        self.state = seed

    def next(self):
        self.state = (1664525 * self.state + 1013904223) % (2 ** 32)
        return self.state / (2 ** 32)

    def bipolar(self):
        return self.next() * 2.0 - 1.0


class LowPass:
    """One-pole. Enough for opening and closing a filter; nothing here wants
    resonance, which is exactly where 'metallic' would come from."""

    def __init__(self):
        self.y = 0.0

    def process(self, x, cutoff):
        a = 1.0 - math.exp(-2.0 * math.pi * cutoff / RATE)
        self.y += a * (x - self.y)
        return self.y


class HighPass:
    """One-pole complement. Paper has no bottom end, and leaving the low
    frequencies in is what turns a page turn into a thud on a phone speaker."""

    def __init__(self):
        self.low = LowPass()

    def process(self, x, cutoff):
        return x - self.low.process(x, cutoff)


def paper_grain(out, at, rand, length=0.010, cutoff=4200.0, floor=500.0,
                amp=1.0, pan=0.0):
    """One flick of paper: a very short noise burst, band-limited and decayed.

    The whole palette is built from this. A grain with a fast decay and no tone
    reads as a page or a card; give it a resonance or a pitch and it becomes a
    click, which is the sound the note back was about.
    """
    start = int(at * RATE)
    n = int(RATE * length)
    low, high = LowPass(), HighPass()
    # Equal-power pan, so moving a grain across the image does not change how
    # loud it is.
    left_gain = math.sqrt((1.0 - pan) * 0.5)
    right_gain = math.sqrt((1.0 + pan) * 0.5)

    for i in range(n):
        if start + i >= len(out):
            break
        t = i / RATE
        # Fast attack, faster decay: the grain is over before it can be pitched.
        env = min(1.0, t / 0.0006) * math.exp(-t / (length * 0.32))
        v = high.process(low.process(rand.bipolar(), cutoff), floor) * env * amp
        l, r = out[start + i]
        out[start + i] = (l + v * left_gain, r + v * right_gain)


def air(out, at, seconds, rand, open_from, open_to, amp=1.0, curve=0.5,
        floor=280.0, pan=0.0):
    """A breath: noise through a filter that opens and closes again.

    `curve` is where the peak sits in the span, so a swell can lean early
    (something arriving) or late (something leaving).
    """
    start = int(at * RATE)
    n = int(RATE * seconds)
    low_l, low_r, high = LowPass(), LowPass(), HighPass()
    left_gain = math.sqrt((1.0 - pan) * 0.5)
    right_gain = math.sqrt((1.0 + pan) * 0.5)

    for i in range(n):
        if start + i >= len(out):
            break
        progress = i / n
        # Raised cosine either side of the peak: no edge anywhere in it.
        if progress < curve:
            env = 0.5 - 0.5 * math.cos(math.pi * progress / curve)
        else:
            env = 0.5 + 0.5 * math.cos(math.pi * (progress - curve) / (1.0 - curve))
        cutoff = open_from + (open_to - open_from) * progress
        source = high.process(rand.bipolar(), floor)
        v = env * amp
        l, r = out[start + i]
        out[start + i] = (
            l + low_l.process(source, cutoff) * v * left_gain,
            r + low_r.process(source, cutoff) * v * right_gain,
        )


def body(out, at, seconds, freq, amp=1.0, drop=0.0, attack=0.004):
    """The soft low body under a thump — a stack of paper settling, not a hit.

    Sine only, with an optional downward glide. No harmonics: one octave up is
    all it takes to hear wood instead of paper.
    """
    start = int(at * RATE)
    n = int(RATE * seconds)
    phase = 0.0

    for i in range(n):
        if start + i >= len(out):
            break
        t = i / RATE
        phase += 2.0 * math.pi * (freq - drop * (t / seconds)) / RATE
        env = min(1.0, t / attack) * math.exp(-t / (seconds * 0.30))
        v = math.sin(phase) * env * amp
        l, r = out[start + i]
        out[start + i] = (l + v, r + v)


def tone(out, at, seconds, freq, amp=1.0, attack=0.012, partials=((1.0, 1.0, 1.0),)):
    """A soft-edged pitched voice for the two cues allowed to be musical.

    `partials` are (ratio, amplitude, decay multiplier). Integer ratios only —
    an inharmonic partial is what makes a bell sound like metal, and the brief
    for both of these says warm.
    """
    start = int(at * RATE)
    n = int(RATE * seconds)
    phases = [0.0] * len(partials)

    for i in range(n):
        if start + i >= len(out):
            break
        t = i / RATE
        v = 0.0
        for index, (ratio, partial_amp, decay) in enumerate(partials):
            phases[index] += 2.0 * math.pi * freq * ratio / RATE
            v += math.sin(phases[index]) * partial_amp * math.exp(-t / (seconds * decay))
        # A long raised-cosine attack is what keeps it off the "ping".
        v *= min(1.0, 0.5 - 0.5 * math.cos(math.pi * min(1.0, t / attack))) * amp
        l, r = out[start + i]
        out[start + i] = (l + v, r + v)


def silence(seconds):
    return [(0.0, 0.0)] * int(RATE * seconds)


def fade_edges(buf, seconds=0.003):
    n = int(RATE * seconds)
    for i in range(min(n, len(buf))):
        g = i / n
        buf[i] = tuple(s * g for s in buf[i])
        buf[-1 - i] = tuple(s * g for s in buf[-1 - i])


def normalise(buf, peak_dbfs):
    peak = max((max(abs(s) for s in frame) for frame in buf), default=0.0)
    if peak == 0:
        return
    gain = 10 ** (peak_dbfs / 20.0) / peak
    for i, frame in enumerate(buf):
        buf[i] = tuple(s * gain for s in frame)


def measure(buf):
    peak = max((max(abs(s) for s in frame) for frame in buf), default=0.0)
    total = sum(s * s for frame in buf for s in frame)
    rms = math.sqrt(total / (len(buf) * 2)) if buf else 0.0
    to_db = lambda v: 20 * math.log10(v) if v > 0 else -120.0
    return to_db(peak), to_db(rms)


def write(path, buf):
    fade_edges(buf)
    peak_db, rms_db = measure(buf)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for frame in buf:
            for s in frame:
                frames += struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
        w.writeframes(bytes(frames))
    print(f"{path}: {len(buf) / RATE:.3f}s  peak {peak_db:.1f} dBFS  avg {rms_db:.1f} dBFS")


# --- the one bell ----------------------------------------------------------
# `chime` — the intro emoji, once per story. Warm, integer partials, long
# attack, no inharmonicity. It is the only sound in the set that announces
# anything, which is the whole reason it appears exactly once.

def chime():
    out = silence(1.20)
    rand = Rand(7717)
    # A5 with an octave and a twelfth above it: a bell's shape without a bell's
    # metal. The fifth (ratio 3) is what makes it read as bright rather than
    # plain.
    tone(out, 0.0, 1.15, 880.0, amp=0.62, attack=0.016,
         partials=((1.0, 0.60, 1.00), (2.0, 0.24, 0.62), (3.0, 0.11, 0.40)))
    # A breath of paper under the onset, so it belongs to this palette rather
    # than to the notification centre.
    paper_grain(out, 0.0, rand, length=0.05, cutoff=3200.0, floor=700.0, amp=0.20)
    normalise(out, -9.0)
    return out


# --- arrivals --------------------------------------------------------------
# `pop` — an emoji landing with an overshoot. Was a bell, on loan from a
# jingle pack, and it was the sound the note back called "notification". Now a
# closed book: a soft low body with a page-flutter on the front.

def pop():
    out = silence(0.34)
    rand = Rand(4241)
    paper_grain(out, 0.0, rand, length=0.030, cutoff=2600.0, floor=420.0, amp=0.75)
    body(out, 0.004, 0.24, 132.0, amp=0.55, drop=26.0)
    # The overshoot: a second, much softer settle as it comes back.
    paper_grain(out, 0.085, rand, length=0.022, cutoff=1800.0, floor=380.0, amp=0.26)
    normalise(out, -13.0)
    return out


# `impact` — podium blocks landing. Kept weighty, because three blocks arriving
# with no weight is limp, but the attack is a paper edge rather than a rim shot:
# a heavy stack set down, not a block struck.

def impact():
    out = silence(0.42)
    rand = Rand(9091)
    paper_grain(out, 0.0, rand, length=0.040, cutoff=2000.0, floor=300.0, amp=0.70)
    body(out, 0.002, 0.30, 104.0, amp=0.80, drop=22.0)
    body(out, 0.002, 0.16, 208.0, amp=0.16, drop=18.0)
    normalise(out, -12.0)
    return out


# --- handling --------------------------------------------------------------
# `counter` — numbers rolling up. This is the cue the note back was about. It
# was a ratchet; it is now a riffle: a thumb let off the edge of a deck,
# decelerating into the number it lands on. Same information, no mechanism.

def counter():
    out = silence(0.78)
    rand = Rand(1301)
    at = 0.0
    gap = 0.030
    for i in range(15):
        # Each tick slightly quieter and duller than the last, and the gaps
        # widen — a deck running out of cards, which is what "landing on a
        # number" sounds like.
        progress = i / 14
        paper_grain(
            out, at, rand,
            length=0.008 + 0.004 * progress,
            cutoff=4200.0 - 1500.0 * progress,
            floor=520.0,
            amp=0.55 + 0.25 * (1.0 - progress) + 0.10 * rand.next(),
            pan=(rand.bipolar() * 0.12),
        )
        at += gap
        gap *= 1.11
    # The last card, landing: a little more body, dead centre.
    paper_grain(out, at, rand, length=0.026, cutoff=2200.0, floor=360.0, amp=0.85)
    body(out, at, 0.14, 150.0, amp=0.22, drop=20.0)
    # A touch hotter than the other handling cues: it is fifteen tiny grains
    # with air between them, so its *average* is 25 dB under its peak and the
    # bed would otherwise swallow it whole.
    normalise(out, -13.0)
    return out


# `cascade` — calendar cells filling in, 86ms apart, or 53 year-columns 49ms
# apart. One pre-baked sweep: at that spacing a discrete trigger is a machine
# gun. A deck being shuffled across the frame, left to right.

def cascade():
    out = silence(2.60)
    rand = Rand(20260901)
    at = 0.02
    gap = 0.085
    while at < 2.35:
        progress = at / 2.35
        paper_grain(
            out, at, rand,
            length=0.014 - 0.005 * progress,
            cutoff=3800.0 - 900.0 * progress,
            floor=560.0,
            amp=(0.42 + 0.30 * rand.next()) * (1.0 - 0.45 * progress),
            pan=-0.55 + 1.10 * progress,
        )
        at += gap
        # Accelerating, then easing off, so it blurs into texture and settles
        # rather than ending mid-run.
        gap = max(0.030, gap * (0.955 if progress < 0.7 else 1.06))
    normalise(out, -17.0)
    return out


# `slide` — tag rows entering from the left. A card dealt across felt: friction,
# no pitch, over the instant it stops moving.

def slide():
    out = silence(0.30)
    rand = Rand(5533)
    air(out, 0.0, 0.24, rand, open_from=900.0, open_to=3000.0, amp=0.85,
        curve=0.42, floor=420.0, pan=-0.25)
    paper_grain(out, 0.20, rand, length=0.016, cutoff=2400.0, floor=500.0, amp=0.30)
    normalise(out, -17.0)
    return out


# --- air -------------------------------------------------------------------
# `bar` — a bar climbing. Air pressure equalising, per the brief; noise only,
# because a tone here turns twelve bars in `months` into a melody nobody wrote.

def bar():
    out = silence(0.60)
    rand = Rand(8123)
    air(out, 0.0, 0.52, rand, open_from=520.0, open_to=2600.0, amp=0.9,
        curve=0.72, floor=300.0)
    normalise(out, -17.0)
    return out


# `transition` — every scene change, ten times in half a minute. A breath drawn
# through cupped hands, and quiet enough to be noticed only in its absence.

def transition():
    out = silence(0.30)
    rand = Rand(6607)
    air(out, 0.0, 0.26, rand, open_from=1500.0, open_to=900.0, amp=0.8,
        curve=0.35, floor=520.0)
    normalise(out, -24.0)
    return out


# `burst` — eighteen confetti dots, once, after the counter lands. Eighteen
# grains, scattered wide, with no crack in front of them: a handful of paper
# thrown rather than a firework.

def burst():
    out = silence(0.95)
    rand = Rand(31417)
    for i in range(18):
        at = 0.005 + (rand.next() ** 1.7) * 0.55
        paper_grain(
            out, at, rand,
            length=0.012 + 0.010 * rand.next(),
            cutoff=5200.0 - 1800.0 * rand.next(),
            floor=650.0,
            amp=0.30 + 0.45 * rand.next(),
            pan=rand.bipolar() * 0.85,
        )
    # A soft breath under the scatter holds it together as one gesture.
    air(out, 0.0, 0.62, rand, open_from=2400.0, open_to=800.0, amp=0.28,
        curve=0.18, floor=600.0)
    normalise(out, -11.0)
    return out


# --- musical, sparingly ----------------------------------------------------
# `cta` — the share button arriving. The one cue permitted to feel like an
# ending, resolving upward.

def cta():
    out = silence(1.40)
    rand = Rand(2718)
    air(out, 0.0, 0.42, rand, open_from=700.0, open_to=3200.0, amp=0.45,
        curve=0.8, floor=350.0)
    tone(out, 0.16, 0.60, 587.33, amp=0.32, attack=0.020,           # D5
         partials=((1.0, 0.55, 0.9), (2.0, 0.14, 0.5)))
    tone(out, 0.40, 0.95, 880.00, amp=0.40, attack=0.024,           # A5
         partials=((1.0, 0.55, 1.0), (2.0, 0.18, 0.55), (3.0, 0.06, 0.35)))
    normalise(out, -12.0)
    return out


# `exportDone` — the file is written. Two plain ascending notes: a task
# finishing, not a celebration.

def export_done():
    out = silence(0.60)
    rand = Rand(4001)
    paper_grain(out, 0.0, rand, length=0.012, cutoff=3000.0, floor=600.0, amp=0.25)
    tone(out, 0.00, 0.22, 587.33, amp=0.40, attack=0.010, partials=((1.0, 0.6, 0.8),))
    tone(out, 0.13, 0.34, 783.99, amp=0.44, attack=0.010, partials=((1.0, 0.6, 0.9),))
    normalise(out, -14.0)
    return out


if __name__ == "__main__":
    for name, fn in [
        ("recap-chime", chime),
        ("recap-pop", pop),
        ("recap-impact", impact),
        ("recap-counter", counter),
        ("recap-cascade", cascade),
        ("recap-slide", slide),
        ("recap-bar", bar),
        ("recap-transition", transition),
        ("recap-burst", burst),
        ("recap-cta", cta),
        ("recap-exportDone", export_done),
    ]:
        write(f"{name}.wav", fn())
