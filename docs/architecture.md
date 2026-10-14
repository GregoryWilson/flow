# Architecture

Flow is organized around a shared symbolic language. Listening produces
observations and candidate techniques in that language; composition consumes
the same techniques and produces realizations that can be heard and evaluated.

## Creative hierarchy

| Layer | Purpose | Typical lifetime |
|---|---|---|
| Epic | Poetic seed, emotional trajectory, recurring themes | 5–10+ stories |
| Story | A musical chapter and local dramatic direction | Minutes |
| Phrase | Development of motifs, harmony, rhythm, and silence | 2–32 measures |
| Measure | Immediate continuation, disruption, or response | One measure |
| Performance | Timing, articulation, dynamics, timbre, and effects | Every event |

Direction normally travels downward. Discoveries may travel upward. A musical
accident that becomes compelling through repetition or response can alter the
phrase, story, or Epic.

Foreground focus also moves. A phrase may feature melody, bass, percussion,
harmony, or a combination, and the focus can change by story, phrase, or
measure. Lead melody is optional: it can move into the background, appear
intermittently, or be absent while other parts carry the passage. A rest in one
role does not imply silence in the ensemble.

## Start 1: Listening Lab

The Listening Lab is a pipeline of imperfect specialists rather than one
all-knowing model:

1. **Intake** records the source, recording identity, context, and analysis
   scope.
2. **Measurement** estimates waveform, spectral, rhythmic, tonal, dynamic,
   structural, and note-level events.
3. **Separation/transcription** may estimate stems and symbolic notes when a
   passage requires deeper analysis.
4. **Interpretation** proposes musical relationships and techniques supported
   by timestamped observations.
5. **Encoding** expresses a technique as an executable, context-sensitive
   recipe.
6. **Demonstration** performs the recipe and controlled variations.
7. **Review** records whether the explanation and reproduction are convincing.

Raw measurements, observations, interpretations, and validated knowledge are
separate records. Confidence must never be silently converted into certainty.

## Start 2: Composition and playback

The composition engine plans ahead of real-time playback. It retrieves musical
recipes, adapts them to the current context, generates alternatives, and scores
them for narrative fit, continuity, novelty, and playability. A deterministic
audio thread consumes already scheduled events; it never waits for an AI model
or database.

## Local runtime boundaries

- **Real time:** playback, synthesis, effects, event scheduling.
- **Ahead of playback:** narrative continuation, phrase planning, candidate
  generation, orchestration.
- **Background:** listening analysis, self-evaluation, feedback consolidation,
  knowledge indexing.
- **Between sessions:** optional model adaptation or training.

The initial Python prototype validates knowledge extraction and representation.
A later Windows performance host may use JUCE/C++ while retaining the same
serialized contracts.

