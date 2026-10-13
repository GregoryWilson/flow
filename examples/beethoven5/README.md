# Beethoven's Fifth: opening benchmark

## Question

Can Flow hear one musical idea, describe what it measured, distinguish that
evidence from interpretation, and encode the idea deeply enough to reproduce
and transform it?

## Inputs kept outside Git

Place a selected local recording under `recordings/beethoven5/`. Record its
source and performance identity in the future intake manifest. The repository
does not distribute or commit the recording.

The experiment will eventually use three isolated evidence lanes:

1. **Audio-only:** automatic measurements with no score or published analysis.
2. **Score reference:** reviewed symbolic facts about the composition.
3. **Interpretive sources:** attributed musical analysis and performance notes.

Do not expose lanes 2 or 3 to the audio-only interpretation until its output is
frozen. This lets us measure listening rather than recognition or recall.

## Baseline commands

```powershell
flow analyze recordings\beethoven5\performance.ogg --start 0 --duration 30 --out analysis.beethoven5.opening.json
flow init-beethoven --out beethoven-opening.recipe.json
```

## First review checklist

- Inspect detected onsets against the opening gestures.
- Compare raw onset events with onset clusters; clusters are an aid for ensemble
  attacks and are not note transcriptions.
- Review candidate inter-onset gaps and low-energy intervals manually; they are
  not automatically labeled fermatas, phrase boundaries, silence, or notated rests.
- Compare two-second chroma windows to see harmonic/pitch-class evidence evolve.
- Inspect short-window pitch candidates as relative salience evidence, not
  transcribed notes; orchestral harmonics can produce plausible but incorrect peaks.
- Inspect pulse-window interval spread to identify unstable or ambiguous pulse
  tracking around held notes.
- Inspect beat estimates and document ambiguity around pauses and held notes.
- Compare chroma evidence with the score only after audio-only output is saved.
- Mark which observations support motif boundaries.
- Render the recipe with neutral synthesis.
- Test transposition, proportional augmentation, orchestration changes, and
  rhythmic recontextualization.
- Record which transformations preserve identity and which destroy it.

