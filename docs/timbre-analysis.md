# Timbre evidence

## Current measurement

`flow analyze` computes overlapping timbre windows on the same time grid as its
pitch-candidate windows. Each window reports:

- spectral centroid and bandwidth;
- spectral flatness and the 85% spectral rolloff;
- relative energy in eight broad frequency bands;
- mean and peak onset strength; and
- an eight-harmonic energy profile for each of the window's top pitch
  candidates, including its odd-to-even harmonic energy ratio.

`flow compare-score` attaches nearby timbre windows to each score-aligned part
attack. This makes it possible to compare the same acoustic context across the
upper reference, viola, and cello lanes.

## How to interpret it

These are measurements of a mono mixture, not instrument identities or
separated tracks. A harmonic profile can include partials from other notes,
octave doublings, and other instruments. Centroid, flatness, or an odd/even
ratio alone cannot prove that a violin or clarinet produced the sound. A strong
instrument claim needs repeated evidence across notes and time, plus validation
against labeled examples.

The first purpose is to find useful contrast: whether score-aligned parts have
repeatable differences in spectral envelope, harmonic balance, or attack
behavior. Later work can add instrument templates, vibrato/modulation measures,
and stereo-channel evidence, then test score-guided separation against known
parts. Old analysis JSON files have no timbre measurements; rerun `flow analyze`
from the original audio to create them.
