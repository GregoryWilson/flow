# Beethoven 5 voice-contrast passage

## Passage

Use measures 18–21 of movement I as the next score-assisted comparison. The opening motif is largely doubled; this short passage gives the benchmark different registers, pitches, and attack patterns across the score lanes.

The reference is a candidate transcription from Mutopia's MIDI. Mutopia says the material is provided as-is and makes no claim of musical correctness, so cross-check the note events against the published score before treating this as ground truth. The bassoon line in `events` is the alignment anchor. The remaining score lanes are under `part_events`. MIDI score tracks 05 and 06 keep neutral IDs because their embedded instrument labels do not match the orchestra staff names; the reference does not guess their instrument identity. Empty gaps are not encoded as rests.

## Keep analysis and score evidence separate

Run audio-only analysis first, then compare its saved output with the score reference. The start time below is an initial window estimate; the opening fermatas and the recording's tempo can shift the passage, so listen and adjust the start if needed.

```powershell
.\.venv\Scripts\python.exe -m flow.cli analyze .\recordings\beethoven5\performance.ogg --start 17 --duration 13 --out .\analysis.beethoven5.voice-contrast.json
.\.venv\Scripts\python.exe -m flow.cli compare-score .\analysis.beethoven5.voice-contrast.json --reference .\examples\beethoven5\score_reference_voice_contrast.json --out .\analysis.beethoven5.voice-contrast-comparison.json
```

## What this can tell us

The comparison can check whether the audio mix contains pitch and onset evidence compatible with the score's changing lines. One whole-mix onset can support multiple score lanes when they double or coincide. Timbre windows still describe the mix and do not identify an instrument or separate its audio source.

The score reference is derived from the full-orchestra MIDI/LilyPond transcription listed by Mutopia Project #941. Its MIDI does not encode dynamics. The source and transcription limits are recorded in the JSON.
