# Flow

**Cohesive, yet beautifully incorrect.**

Flow is a local-first generative music system that continuously composes and
performs an evolving musical journey. Narrative provides intent, musical
knowledge provides craft, recent history provides continuity, and
experimentation provides surprise.

Flow has two simultaneous starting tracks:

1. **Listening Lab** — analyze music and turn observations into explainable,
   executable musical knowledge.
2. **Composition Engine** — perform, transform, and validate those musical
   ideas in real time.

The first benchmark is the opening of Beethoven's Fifth Symphony: detect its
events from audio, compare them with score-informed reference data, encode its
opening motif as a reusable recipe, and demonstrate transformations of that
recipe.

## Principles

- Local AI and local processing only; no cloud inference is required.
- Store musical understanding, not a collection of source recordings.
- Keep measurements separate from interpretations.
- Preserve provenance, confidence, alternatives, and cultural context.
- Test an interpretation by performing it.
- Treat silence as a composed event.
- Let discoveries travel upward: a compelling musical accident may redirect
  a phrase, story, or Epic.

## Repository layout

```text
docs/                    Architecture, schema, and roadmap
schemas/                 Machine-readable knowledge contracts
src/flow/listening/      Audio measurement pipeline
src/flow/knowledge/      Executable musical knowledge models
src/flow/composer/       Recipe realization and future playback engine
examples/beethoven5/     First listening benchmark
tests/                   Fast, local tests
```

## Quick start

Flow currently targets Python 3.11+ for the Listening Lab prototype.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[audio]"
python -m unittest discover -s tests -v
flow analyze path\to\authorized-recording.wav --out analysis.json
flow init-beethoven --out beethoven-opening.recipe.json
flow render-rhythm-demo --out rhythm-section-demo.mid --tempo 120 --tonic-midi 60
flow render-audio-demo --out rhythm-section-demo.wav --tempo 120 --tonic-midi 60
flow init-rhythm-demo --out my-idea.json
flow render-recipe my-idea.json --out my-idea.wav --tempo 120 --tonic-midi 60
```

`flow analyze` also records windowed timbre evidence: spectral shape, harmonic
profiles around pitch candidates, and onset strength. These features describe
the mixed sound; they do not identify instruments or separate audio sources.

Audio files, model weights, databases, and rendered sessions are deliberately
excluded from Git. See `examples/beethoven5/README.md` for the first experiment.

`render-rhythm-demo` exports a Standard MIDI File using General MIDI instrument
and drum assignments. `render-audio-demo` creates a dependency-free WAV preview
with simple synthesized voices so the arrangement can be heard immediately.
That reference sound is intended to check notes, roles, and handoffs; it is not
a production synthesizer or the final real-time playback engine.

`init-rhythm-demo` writes an editable knowledge-entry recipe. Adjust its events,
roles, rests, or focus plan in a text editor, then pass it to `render-recipe`.
The output extension selects WAV (`.wav`) or MIDI (`.mid`/`.midi`). The current
demo renderer supports melody, bass, and percussion roles.

## Status

Early architecture and Listening Lab scaffold. The immediate acceptance test
is not “classify Beethoven correctly”; it is “extract one idea deeply enough
to explain, reproduce, vary, and evaluate it.”

