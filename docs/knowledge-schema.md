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

## Status lifecycle

`proposed → reviewed → demonstrated → validated`

An entry can also be `rejected` or `superseded`. Demonstration means Flow can
perform the claimed technique; validation means the result supports the stated
interpretation in context.

The canonical machine-readable contract lives in
`schemas/musical_knowledge_entry.schema.json`.

