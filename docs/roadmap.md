# Roadmap

## Milestone 0 — Shared language

- Versioned schema for sources, observations, interpretations, recipes, and
  realizations.
- Local CLI and fast tests.
- Repository rules that keep recordings and model weights out of Git.

## Milestone 1 — Beethoven opening benchmark

- Analyze the first 30–60 seconds of a selected performance of Beethoven's
  Fifth Symphony, first movement.
- Produce tempo, beat, onset, chroma, dynamics, and spectral measurements.
- Compare audio-only findings with score-informed reference data.
- Encode the opening motif as a relative rhythmic and interval recipe.
- Render faithful and transformed demonstrations.
- Record errors and uncertainty instead of correcting results invisibly.

### Listening Lab phase 1.1 — passage-aware evidence

- Analyze a bounded passage (for the current performance, begin with 0–30 s).
- Preserve raw onsets while adding configurable near-simultaneous attack clusters.
- Report onset gaps, local beat-interval windows, time-varying chroma, and
  low-energy intervals as candidates with timestamps—not as semantic labels.
- Inspect these outputs against listening and score references before adding
  motif, fermata, or phrase claims.

### Listening Lab phase 1.2 — phrase and pitch evidence

- Add short-window CQT pitch candidates with timestamps and relative strengths.
- Sample overlapping pitch windows at a finer hop so nearby onset events can be
  reviewed without treating a coarse pitch window as one note attack.
- Keep candidates explicitly separate from note transcription and score facts;
  ensemble harmonics and orchestration can make the strongest bin misleading.
- Call RMS threshold spans low-energy intervals, never silence or rests.
- Compare the first motif's candidates and onset gaps with a separately stored
  score reference after the audio-only measurements are frozen.
- Emit an ordered pitch-class comparison with octave support, onset-cluster
  counts, and performance timestamps; keep it out of the audio-only result.
- Pair whole-mix onset clusters with adjacent timestamped pitch windows so
  reviewers can inspect candidate pitches around each detected attack.
- Measure note and phrase accuracy against reviewed reference events before
  treating the analyzer as a source of reusable musical knowledge.

## Milestone 2 — Twenty-five-recording pilot

Choose deliberately contrasting recordings that expose limitations: dense and
sparse mixes, stable and free rhythm, equal and non-equal temperament, solo and
ensemble performance, acoustic and electronic production, instrumental and
vocal traditions. One recording must never stand in for an entire tradition.

## Milestone 3 — Initial 1,000-recording atlas

- Select by gaps across geography, period, musical organization, performance
  practice, instrumentation, vocal practice, and production—not popularity
  alone.
- Add continuous discovery driven by uncertainty and knowledge coverage.
- Track representation balance and known blind spots.

The atlas does not end at 1,000. That is an initial seed for lifelong musical
education.

## Composition milestones

In parallel, develop a four-role ensemble (drums, bass, harmony, lead), recipe
realization, motif memory, deliberate silence, weighted creative controls, and
buffered playback. The first musical acceptance test is a coherent twenty-minute
journey with meaningful development and uninterrupted performance.

