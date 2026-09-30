# Recap audio — sources and playback

The recap uses recorded music and card sounds. The selected sources are CC0:

- Holizna's [“Poor, But Happy”](https://freemusicarchive.org/music/holiznacc0/busted-guitar-lofi-edit/poor-but-happy/), supplied in the [Happy Lo-Fi collection](https://opengameart.org/content/happy-lo-fi-lofi-collection): instrumental jazz guitar with a light lo-fi beat.
- [Kenney Casino Audio](https://kenney.nl/assets/casino-audio): card slides, placement and fanning recordings for the seven scheduled cue assets.

Exact source members, licences and asset measurements live in
[`Audio/CREDITS.md`](../EveryDayEmoji/MoodRecap/Audio/CREDITS.md). The schedule and
design criteria are in [`recap-sound-design.md`](recap-sound-design.md).

## Preparing the assets

[`scripts/prepare_recap_audio.py`](../scripts/prepare_recap_audio.py) accepts the
downloaded source archives, verifies their SHA-256 hashes, trims and masters the
recordings, and writes 48 kHz stereo AAC `.m4a` files at 128 kbps. It uses Python's
standard library and macOS `afconvert`; it does not download anything.

```bash
python3 scripts/prepare_recap_audio.py \
  --music /path/to/happy-lo-fi.zip \
  --effects /path/to/kenney_casino-audio.zip \
  --output EveryDayEmoji/MoodRecap/Audio
```

The music uses the first 40 seconds of the recording, attenuated by 9.5 dB during
mastering. That covers the longest current story, 35 seconds, without a loop
boundary. Card excerpts receive filtering, short edge fades and level control;
the script contains the exact source mapping and targets.

`docs/recap-bed-generator.py` and `docs/recap-cue-generator.py` are historical
experiments. They are not the recipe for the current palette. Legacy sound enum
cases and unused assets remain in the library; `RecapCueSchedule` determines
which ones are heard.

## Playback and export

Sound starts off. A localized speaker button in the story has a 44-point target
and an accessible on/off value. Its preference also controls whether the exported
MP4 contains audio. Playback uses the ambient audio session, respecting silent
mode and mixing with other audio.

`RecapCueSchedule` supplies both playback and export. A complete year has at most
10 cues, a complete month 9, and a sparse period 5. There are no transition,
counter or burst sounds; export completion uses haptics only.

`RecapSoundtrack` retains prepared players for overlapping cues. Holding or
backgrounding the story pauses playback; resuming preserves positions. Seeking
discards cues belonging to the skipped passage and repositions the music. Audio
stops at the story's end and while exporting or showing the share sheet.

Live playback and export both use `RecapSound.volume`: 0.8 for the bed and 1.0
for cues. `RecapAudioMix` supplies the bed's 0.25-second fade-in and 1-second
fade-out relative to the actual story duration. Missing assets degrade to
silence, and export retains source assets while composing their tracks.

The remaining quality check is listening to both playback and the exported MP4
on a phone speaker against the visuals. Source provenance and signal measurements
do not establish whether the music and effects feel appropriate.
