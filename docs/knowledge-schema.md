# Musical knowledge schema

Flow stores musical understanding as evidence-backed, executable recipes. It
does not treat a recording, a transcription, and a theory about that recording
as the same thing.

## Record types

| Record | Meaning |
|---|---|
| Source | Where an analyzed performance came from |
| Observation | A timestamped measurable claim |
| Interpretation | A musical explanation supported by observations |
| Recipe | A reusable procedure expressed relative to musical context |
| Realization | One exact performance of a recipe |
| Evaluation | Human or system judgment of a realization |

## Recipe anatomy

A recipe records:

- intent and expected perceptual effect;
- required musical context and contraindications;
- optional, time-varying foreground focus: which roles are featured and
  whether melody is foreground, background, intermittent, absent, or unknown;
- relative events using beats, scale degrees, chord functions, roles, and
  continuous pitch where equal temperament is inappropriate;
- relationships among parts;
- performance instructions such as microtiming, articulation, and dynamics;
- legal transformations and invariants;
- provenance, evidence, alternatives, confidence, and review status.

## Recipe versus realization

The **recipe** is adaptable: “delay selected lead attacks while the rhythm
section remains stable.” The **realization** is exact: tempo, key, events,
instrument definitions, random seed, and engine version. A seed alone is not a
durable reproduction contract because algorithms change.

The recipe's role list describes available voices; it does not require a lead.
An optional `focus_plan` can change by beat span. For example, bass and
percussion may hold foreground focus while `melody_presence` is `absent`.
That means the melody is intentionally not carrying the passage; it does not
mean the ensemble is silent. `background` and `intermittent` distinguish a
quiet or fragmentary melody from a fully absent one. Unspecified spans remain
unknown rather than being assumed to have a lead.

```json
{
  "start_beat": 16,
  "duration_beats": 8,
  "foreground_roles": ["bass", "percussion"],
  "melody_presence": "absent"
}
```

A `rest` event belongs to a specific role lane; the other lanes can continue.
The focus plan records what carries attention, while the events record what
each role plays.

## Status lifecycle

`proposed → reviewed → demonstrated → validated`

An entry can also be `rejected` or `superseded`. Demonstration means Flow can
perform the claimed technique; validation means the result supports the stated
interpretation in context.

The canonical machine-readable contract lives in
`schemas/musical_knowledge_entry.schema.json`.

