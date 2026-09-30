# Recap sound — current direction

The music carries the story; short recorded card sounds mark selected moments.
The chosen bed is Holizna's “Poor, But Happy,” an instrumental jazz-guitar track
with a light lo-fi beat. Effects come from Kenney Casino Audio. Both sources are
CC0; see [sources and playback](recap-audio.md) and
[asset credits](../EveryDayEmoji/MoodRecap/Audio/CREDITS.md).

The intended tone is warm and lightly rhythmic, with room for a difficult month.
Effects should remain quiet enough that a mood reveal does not become a reward
fanfare. These are design criteria for auditioning, not a claim that phone
listening has passed.

## Schedule

Offsets below are relative to the start of each scene. Optional scenes contribute
no cues when omitted. A complete year has 10 cues, a complete month 9, and a sparse
period 5.

| Scene | Cue | Offset | Role |
| --- | --- | --- | --- |
| Intro | `chime` | 0.0s | One soft opening card sound |
| Title | none | — | Leave the title to the music |
| Grid | `cascade` | +0.6s | One card-fan texture as the grid begins |
| Top mood | `pop` | +1.8s | Mark the completed count |
| Months | `bar` | +0.5s | One quiet texture for the chart |
| Streak | `pop` | +1.8s | Mark the completed count |
| Weekday | `bar` | +0.5s | One quiet texture for the chart |
| Spectrum | `bar` | +0.6s | One quiet texture for the chart |
| Tags | `slide` | +0.6s | One card slide for the section |
| Podium | `impact` | +1.0s | One placement sound for the reveal |
| Outro | `cta` | +0.7s | A short card sound for the share control |

There is no sound on every scene transition, counting digit, tag row or podium
block. `counter`, `burst` and `transition` remain legacy library cases but are
not scheduled. Export completion uses a haptic without restarting audio under
the share sheet. The retained name `chime` now refers to a card recording, not
a bell.

## Mix and delivery

The first 40 seconds of the music cover every current story length without a
splice. Mastering attenuates that excerpt by 9.5 dB; playback and export apply
the same additional 0.8 bed gain. Cue gains are 1.0, with relative levels set in
the assets. The bed fades in over 0.25 seconds and out over the final second of
the actual story duration.

Card excerpts have softened attacks and short tails. Keep those tails within
their scenes rather than filling every gap with texture. The active preparation
recipe is [`scripts/prepare_recap_audio.py`](../scripts/prepare_recap_audio.py),
which processes the downloaded archives into 48 kHz stereo AAC files. The two
older synthesis scripts under `docs/` are retained as history, not as fallback
instructions for this palette.

## Listening check

Enable sound with the recap's speaker button and compare a sparse month, a full
month and a full year. Listen twice on a phone speaker, including a period with
mostly difficult moods. Check that the music leaves the text easy to follow and
that effects remain distinct without sounding like alerts.

Hold and resume, skip forward and backward, leave and return to the app, then
export with sound enabled and disabled. Compare the audible export with normal
playback for balance and ending. This check still requires a human listener;
waveform measurements and automated checks cannot judge the tone.
