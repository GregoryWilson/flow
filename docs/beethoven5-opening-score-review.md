# Beethoven 5 opening: score-assisted layer review

## Purpose

Use the full orchestral score as a temporary calibration reference for Flow's audio-only analysis. The score is consulted after the audio analysis has been saved; it does not supply notes or timing to the normal analysis path.

## Reference inspected

The opening system of the full score for Symphony No. 5 in C minor, Op. 67, movement I, marked *Allegro con brio* (quarter note = 108; 2/4). The score shows individual instrument staves. The score is available from [IMSLP](https://s9.imslp.org/files/imglnks/usimg/2/2c/IMSLP878035-PMLP1586-Symphony_No.5_Op.67_Ludwig_van_Beethoven.pdf). The first score page labels the parts and shows their opening activity.

## What the score tells us about the opening

- The repeated short–short–short–long idea is shared across the string section and the two clarinet parts. It is therefore an ensemble motif, not a line unique to one instrument.
- Flutes, oboes, bassoons, horns, trumpets, and timpani are resting during the opening motif shown on this system. Their lack of a corresponding audio line in this passage is expected; it should not count as a detector miss.
- The clarinet staves are transposed. Any comparison with audio pitch must convert their written notes to concert pitch first.
- The source score gives notated timing and rests. It does not give the exact timing of the recording, and fermatas make a fixed beat-to-second conversion especially unreliable.

The existing score reference captures the upper motif as concert-pitch G4 ×3, E-flat4 held, then F4 ×3 and D4 held. It is a motif reference, not a complete transcription of the orchestral texture. This review does not add uncertain inner-part pitches.

## Comparison with the saved audio evidence

The saved comparison finds the ordered pitch-class sequence G, E-flat, F, D. Its strongest matching runs are approximately 0.736–1.717 s, 1.717–4.171 s, 4.171–4.907 s, and 4.907–7.851 s. Exact-pitch evidence is present for each run. The whole-mix onset report counts 4 onset clusters in the G run and 3 in the F run, where the score expects three short attacks in each group.

This supports the claim that the expected motif pitches occur in order. It does **not** verify the three attacks as melody attacks: onset clusters are computed from the full mixture, and the string and clarinet parts double the motif. The broad E-flat and D runs also include performance gaps/fermata time, so they should not be read as note-duration estimates.

## What this calibrates

For this passage, the score gives us a controlled example of:

1. **Expected activity:** which scored parts are playing or resting.
2. **Shared rhythm:** multiple parts may produce the same motif onsets, so one mix-level onset cannot be assigned to one instrument.
3. **Concert-pitch conversion:** transposing notation must be normalized before comparing pitch candidates.
4. **Phrase-level timing:** align the ordered score events to the recording before judging duration or expressive timing.

The score comparison reports pitch candidates by octave within each matched pitch-class run and now includes the score's expected active/resting parts for the opening motif. The activity annotation confirms that the motif is shared by strings and clarinets, while the other listed sections rest in this passage. It is score-only context: the audio evidence still cannot identify which of the active parts produced a candidate.

The comparison also maps score-beat starts to detected pitch-run starts and reports local seconds-per-beat and implied BPM between adjacent anchors. In the saved comparison, the anchors are approximately G4 at beat 0.5 / 0.736 s, E-flat4 at beat 2 / 1.717 s, F4 at beat 4.5 / 4.171 s, and D4 at beat 6 / 4.907 s. These are coarse boundaries, not detected note attacks. Fermatas and broad pitch runs stretch the intervals, so local BPM values are timing diagnostics, not a tempo estimate.

The new `score_attack_alignment` checks each individual notated note onset against the interpolated time, nearest unused whole-mix onset cluster (within 0.2 seconds by default), and nearby pitch windows. In the saved audio analysis, all eight expected attacks have a nearby onset cluster; seven have pitch-class salience at or above 0.3. The first G4 attack is below that pitch-class threshold. Eight other whole-mix onset clusters fall inside the motif's attack-time span and remain unassigned to its eight notes. Several show strong low-register D-sharp candidates alongside higher harmonics. These are candidates for additional rhythmic or accompaniment activity, not proof of fills, trills, or a separate instrument. The comparison with the scored viola and cello parts below checks whether their low registers fit the recorded candidates. Onset clusters combine the ensemble, and pitch windows overlap in time, so this remains compatible evidence rather than instrument identification.

The viola and cello staves have now been transcribed for this short passage as score-only part events: G3/E-flat3/F3/D3 in the viola and G2/E-flat2/F2/D2 in the cello, with the same short-short-short-long rhythm. The unassigned-onset report can show these scored pitches alongside the upper motif. In the saved audio windows, the G candidates include G3/G2, the E-flat candidates include E-flat3/E-flat2, and the F candidates include F3/F2. This makes the low candidates compatible with the notated string doublings; it weakens the idea that those pitches alone indicate a separate fill or trill. It still cannot assign an audio candidate to viola or cello, and the E-flat onsets fall inside the stretched interval flagged above, so their score-beat positions are especially uncertain.

Across the eight currently unassigned onset clusters, seven map to a scored motif note duration in the modeled upper-motif, viola, and cello lanes. Their nearby pitch candidates include the corresponding G, E-flat, or F pitch classes. The remaining cluster at 4.011 s maps to beat 4.34, where all three modeled lanes are notated at rest; its strongest candidate is still E-flat2. This position is inside the 1.5× stretched interval, so it could reflect lingering E-flat energy, a coarse alignment error, or an onset/pitch-analysis artifact. It is a useful rest-overlap candidate for listening review, not evidence of an extra performed note. The report now summarizes whether an unmatched onset overlaps scored notes or only rests in the modeled lanes.

The unassigned-onset report now maps each event's time back through the same coarse anchors and lists the score reference notes or rests at that estimated beat. This helps distinguish events that fall inside a notated rest from events that overlap one or more note durations. The inverse map inherits the anchor interpolation's uncertainty, especially around fermatas; it cannot establish a rearticulation, fill, trill, or instrument source.

The comparison now also reports each modeled score lane separately and groups simultaneous, different score pitches into vertical stacks. On the saved opening analysis, the upper reference line, viola, and cello lanes each have eight mapped attacks, and all eight align to a whole-mix onset within the default 0.2-second tolerance. Exact MIDI-pitch candidates support 8/8 upper-line attacks, 8/8 viola attacks, and 6/8 cello attacks; cello pitch-class candidates support all 8/8. The initial G2 candidate is just below the exact-pitch threshold (0.294 against 0.3), and F2 has no exact-pitch candidate at its first attack, although F2 appears at the later attacks. The final D2 attack has exact-pitch support (0.556). Candidate-list absence at an event is not proof that the part is absent.

The simultaneous stacks show G4/G3/G2, E-flat4/E-flat3/E-flat2, F4/F3/F2, then D4/D3/D2 at the modeled attacks. That is promising evidence for distinct lines across three registers in this score excerpt. The alignment deliberately lets one whole-mix onset support several score parts because the parts can double rhythmically. It does not separate the upper line into its violin and clarinet sources, distinguish which source produced any candidate, or verify parts omitted from the current part-event transcription. In particular, the upper reference line is an aggregate motif reference, not one identified instrument voice. Weak/absent candidate pitches and score-only voice counts remain explicit so a later audio-only separation method can be evaluated without treating the score as its answer.

Nearby pitch candidates are also compared with the score pitches at that estimated beat. Same-pitch-class and octave relationships can show that a low candidate is compatible with a scored motif tone. They cannot distinguish an instrument doubling from a harmonic or another source in the mix.

Because a fermata can stretch the time between two pitch-run anchors, unmatched events now carry a `score_time_map` diagnostic. It compares the interval's seconds per score beat with the passage median and flags ratios of 1.4 or greater as stretched. This is a warning that linear beat interpolation may be unreliable; it does not identify a fermata by itself.

## Limits

This is a small, manually reviewed opening passage, not a general score transcription benchmark. The existing analyzer reports pitch salience and whole-mix onset clusters; it does not separate sources, identify instruments, or prove which layer produced a pitch. Score-assisted results should remain separate from the audio-only report so the reference cannot leak into discovery.
