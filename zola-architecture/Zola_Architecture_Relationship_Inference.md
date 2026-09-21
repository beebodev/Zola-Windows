# Zola Architecture — Relationship Inference and Graph Model

Document version: 1.0
Created: 2026-06-09
Status: LOCKED — design decisions finalized in pre-Phase 19 scoping session
Supersedes: N/A (new document)
Companion documents:
- `zola-architecture/Zola_Architecture_Memory_Agency.md`
- `zola-architecture/lore/DESIGN_DECISIONS.md`
- `zola-architecture/audit/phase19/Zola_P19_Memory_Audit_01_Relationship_Schema.md`

---

## Purpose

This document defines the authoritative relationship graph model for Zola's world memory.
It covers the Firestore schema for relationship edges, the complete predicate taxonomy,
write-time inference rules, truth maintenance policy, and read-time traversal rules for
extended relationships. All implementation work touching the relationship graph must
treat this document as binding truth.

---

## Design Decisions Locked by This Document

The following decisions were finalized in the pre-Phase 19 design session on 2026-06-09
and are non-negotiable going forward. They are also recorded in DESIGN_DECISIONS.md.

**P19-D01 — Single schema, start fresh.**
The legacy `users/{userId}/people/` collection, the embedded `Relation` model
(DynamicMemory.kt), the `Person` document model, and `HybridMemoryBridge` are deleted
in Phase 19 Track 0. The structured `users/{userId}/relationships/` collection is the
only relationship storage path. No migration. No compatibility layer. All existing data
is test data and is discarded.

**P19-D02 — Relationship storage policy.**
Direct, explicitly stated relationships are stored as first-class Firestore edges.
Extended relationships that require multi-hop traversal are computed at read time
and are never written to Firestore unless explicitly stated by the user.

**P19-D03 — Siblings are stored, not computed.**
Sibling relationships are direct, stable, named relationships. When Zola writes a
PARENT_OF edge, she runs a synchronous inference pass that finds all other entities
sharing that parent and writes SIBLING_OF edges between them. This is write-time
inference, not read-time computation.

**P19-D04 — Extended family policy.**
Extended relationship predicates (AUNT_OF, UNCLE_OF, COUSIN_OF, SIBLING_IN_LAW_OF,
STEP_PARENT_OF, STEP_CHILD_OF) are valid storable types when explicitly stated by the
user. They are never stored as system-inferred edges — only stored when the user names
them directly. When not stored, they are available as read-time traversal results only.

**P19-D05 — derivedFrom field on inferred edges.**
Every system-inferred edge carries a `derivedFrom` field containing the list of source
edge IDs that caused the inference. This enables precise truth maintenance: when a
source edge is corrected or deleted, only edges that reference it in `derivedFrom`
need re-evaluation.

**P19-D06 — Inference is synchronous.**
Write-time inference runs synchronously during the relationship write transaction.
Inferred edges exist by the time the primary write commits. There is no eventual
consistency window for inferred relationships.

---

## Section 1 — Relationship Document Schema

### 1.1 Firestore Path

```
users/{userId}/world/relationships/{relationshipId}
```

The `userId` is the Firebase Auth UID. It is an instance boundary — it scopes
which Zola instance owns this world model. It is not an ontological claim. The
user is a participant in the graph, not the graph's root.

### 1.2 Field Specification

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | String | No | Unique document ID. Matches the Firestore document key. |
| `fromEntityId` | String | No | Subject entity ID. Source of the directed edge. |
| `toEntityId` | String | No | Object entity ID. Target of the directed edge. |
| `type` | RelationshipType | No | Typed predicate from the canonical enum. See Section 2. |
| `direction` | RelationshipDirection | No | FORWARD or BIDIRECTIONAL. Default: FORWARD. |
| `confidence` | Double | No | Confidence score 0.0–1.0. See Section 1.3 for defaults by source. |
| `source` | RelationshipSource | No | USER_STATEMENT, SYSTEM_INFERRED, or SYSTEM. See Section 1.4. |
| `sourceText` | String | Yes | Original natural language phrase that triggered the write. Null for system-inferred edges. |
| `derivedFrom` | List\<String\> | Yes | Edge IDs that caused this inference. Non-null only when source is SYSTEM_INFERRED. See Section 3.3. |
| `createdAt` | Long | No | Unix timestamp of creation. |
| `updatedAt` | Long | No | Unix timestamp of last update. |
| `fromEntityName` | String | Yes | Human-readable debug label. Not used for logic. |
| `toEntityName` | String | Yes | Human-readable debug label. Not used for logic. |
| `typeDisplay` | String | Yes | Display string for the relationship type. |

### 1.3 Confidence Defaults by Source

| Source | Default Confidence | Notes |
|--------|-------------------|-------|
| USER_STATEMENT | 1.0 | User explicitly stated the relationship. Highest authority. |
| SYSTEM_INFERRED | 0.85 | Derived from one inference hop (e.g., sibling from shared parent). |
| SYSTEM | 0.9 | System-created but not inferred (e.g., self-entity edges). |

Confidence on inferred edges degrades with inference chain depth. Each additional
hop beyond the first reduces confidence by 0.1, with a floor of 0.5. This is
relevant only for read-time traversal results — edges stored in Firestore are
always the result of a single inference hop from the write trigger.

### 1.4 RelationshipSource Enum

```
USER_STATEMENT   — User explicitly stated this relationship
SYSTEM_INFERRED  — Derived automatically from existing edges at write time
SYSTEM           — Created by the system for structural reasons (self-entity, etc.)
```

### 1.5 Authority at Read Time

When multiple edges exist for the same entity pair and predicate, the following
authority ranking applies. Higher authority wins at retrieval and display:

1. USER_STATEMENT
2. SYSTEM_INFERRED
3. SYSTEM

If a USER_STATEMENT edge contradicts a SYSTEM_INFERRED edge for the same pair,
the inferred edge is retracted immediately. See Section 4 — Truth Maintenance.

---

## Section 2 — Predicate Taxonomy

Predicates are split into two tiers. Tier 1 predicates may be stored in Firestore
as either USER_STATEMENT or SYSTEM_INFERRED edges. Tier 2 predicates are computed
at read time only and are never persisted unless the user explicitly names them,
at which point they are stored as USER_STATEMENT edges.

### 2.1 Tier 1 — Storable Predicates

These are the valid values of the `RelationshipType` enum.

| Predicate | Direction | Reciprocal | Notes |
|-----------|-----------|-----------|-------|
| PARENT_OF | FORWARD | CHILD_OF | A is the parent of B. |
| CHILD_OF | FORWARD | PARENT_OF | A is the child of B. |
| SIBLING_OF | BIDIRECTIONAL | SIBLING_OF | Symmetric. A and B are siblings. |
| SPOUSE_OF | BIDIRECTIONAL | SPOUSE_OF | Symmetric. A and B are spouses. |
| FRIEND_OF | BIDIRECTIONAL | FRIEND_OF | Symmetric. |
| PET_OF | FORWARD | OWNER_OF | A is the pet of B. |
| OWNER_OF | FORWARD | PET_OF | A is the owner of B. |
| STEP_PARENT_OF | FORWARD | STEP_CHILD_OF | Stored only when user-stated. |
| STEP_CHILD_OF | FORWARD | STEP_PARENT_OF | Stored only when user-stated. |
| AUNT_OF | FORWARD | NIECE_OR_NEPHEW_OF | Stored only when user-stated. |
| UNCLE_OF | FORWARD | NIECE_OR_NEPHEW_OF | Stored only when user-stated. |
| NIECE_OR_NEPHEW_OF | FORWARD | AUNT_OF or UNCLE_OF | Stored only when user-stated. |
| COUSIN_OF | BIDIRECTIONAL | COUSIN_OF | Stored only when user-stated. |
| SIBLING_IN_LAW_OF | BIDIRECTIONAL | SIBLING_IN_LAW_OF | Stored only when user-stated. |
| EMPLOYER_OF | FORWARD | EMPLOYEE_OF | A employs B. |
| EMPLOYEE_OF | FORWARD | EMPLOYER_OF | A works for B. |
| COLLEAGUE_OF | BIDIRECTIONAL | COLLEAGUE_OF | Symmetric. |
| PRIMARY_BOND | BIDIRECTIONAL | PRIMARY_BOND | Exists exactly once per graph, between SELF and primary user PERSON entity only. `bondCharacter` attribute on edge defaults to COMPANION_OF. Source is always SYSTEM. Not subject to IR-01 or IR-02. |
| KNOWS_ABOUT | FORWARD | none | Available from SELF entity only. Written by system when Zola creates or becomes aware of any entity. Carries `firstMentionedAt` (Long) and `mentionCount` (Int) as edge attributes. Never user-stated. Source is always SYSTEM. Not subject to inference rules IR-01 or IR-02. |

### 2.2 Tier 2 — Read-Time Only Predicates

These relationship types are never stored. They are produced by traversal at read
time and returned as query results with a confidence score and traversal path.

| Predicate | Traversal Path | Confidence |
|-----------|---------------|-----------|
| STEP_PARENT_OF | SPOUSE_OF → PARENT_OF (subject's spouse is parent of entity) | 0.85 |
| STEP_CHILD_OF | PARENT_OF → SPOUSE_OF (subject's parent's spouse) | 0.85 |
| AUNT_OF | PARENT_OF → SIBLING_OF (subject's parent's sibling) | 0.80 |
| UNCLE_OF | PARENT_OF → SIBLING_OF (subject's parent's sibling) | 0.80 |
| NIECE_OR_NEPHEW_OF | SIBLING_OF → CHILD_OF (subject's sibling's child) | 0.80 |
| COUSIN_OF | PARENT_OF → SIBLING_OF → CHILD_OF | 0.70 |
| SIBLING_IN_LAW_OF | SIBLING_OF → SPOUSE_OF or SPOUSE_OF → SIBLING_OF | 0.75 |
| GRANDPARENT_OF | PARENT_OF → PARENT_OF | 0.90 |
| GRANDCHILD_OF | CHILD_OF → CHILD_OF | 0.90 |

Note: Tier 2 predicates that have been explicitly stated by the user are promoted
to Tier 1 and stored as USER_STATEMENT edges. The Tier 2 designation applies only
to system behavior — users may always state any relationship directly.

### 2.3 Canonical Direction Convention

All edges are stored as directed edges from subject to object. BIDIRECTIONAL
predicates produce two edge documents: one in each direction. This means a
SIBLING_OF relationship between Jake and Cole is stored as two documents:
Jake → Cole: SIBLING_OF and Cole → Jake: SIBLING_OF.

This convention ensures that graph traversal from any entity finds its relationships
without needing to query both directions. The cost is two writes per bidirectional
edge. This is acceptable — relationship writes are low-frequency events.

---

## Section 3 — Write-Time Inference Rules

### 3.1 When Inference Runs

The inference pass runs synchronously after every primary relationship write commits.
It runs before the write transaction returns to the caller. By the time the caller
receives confirmation that a relationship was written, all inferred edges derived
from that write already exist in Firestore.

The inference pass is triggered by writes to the `users/{userId}/relationships/`
collection regardless of the write path (Live session, correction, manual write).
It is not triggered by inference writes themselves — inference does not chain.

### 3.2 Inference Rules

**Rule IR-01 — Reciprocal edge creation.**
Every FORWARD predicate write produces a corresponding reciprocal edge in the
opposite direction. The reciprocal edge carries `source: SYSTEM_INFERRED` and
`derivedFrom: [primaryEdgeId]`.

Examples:
- Brian → Jake: PARENT_OF produces Jake → Brian: CHILD_OF (SYSTEM_INFERRED)
- Brian → Sarah: EMPLOYER_OF produces Sarah → Brian: EMPLOYEE_OF (SYSTEM_INFERRED)

BIDIRECTIONAL predicates (SIBLING_OF, SPOUSE_OF, FRIEND_OF, COLLEAGUE_OF,
COUSIN_OF, SIBLING_IN_LAW_OF) produce two USER_STATEMENT edges — one in each
direction — at write time. These are not inferred; both directions are
first-class USER_STATEMENT edges.

**Rule IR-02 — Sibling inference from shared parent.**
When a PARENT_OF edge is written from entity A to entity B, query all existing
CHILD_OF edges from any entity to entity A. For each entity C found (excluding B),
write SIBLING_OF edges between B and C in both directions:
- B → C: SIBLING_OF (SYSTEM_INFERRED, derivedFrom: [B→A:PARENT_OF, C→A:PARENT_OF])
- C → B: SIBLING_OF (SYSTEM_INFERRED, derivedFrom: [B→A:PARENT_OF, C→A:PARENT_OF])

This rule fires on every new PARENT_OF edge write, which means when a second child
is recorded for a parent, that child immediately acquires a sibling relationship with
all previously recorded children of the same parent.

**Rule IR-03 — No chained inference.**
Inference rules do not trigger other inference rules. IR-01 and IR-02 run once
against the primary write. The edges they produce are written to Firestore with
`source: SYSTEM_INFERRED` but do not themselves trigger further inference passes.
This prevents infinite loops and keeps the inference surface bounded and auditable.

### 3.3 The derivedFrom Field

Every SYSTEM_INFERRED edge carries a `derivedFrom` field containing the IDs of
the source edges that caused the inference. This is the mechanism by which truth
maintenance (Section 4) knows exactly which inferred edges to re-evaluate when
a source edge changes.

For IR-01 (reciprocal): `derivedFrom` contains the single primary edge ID.
For IR-02 (sibling): `derivedFrom` contains the IDs of both PARENT_OF edges
that established the shared parent relationship.

USER_STATEMENT edges never carry a `derivedFrom` value. It is always null for
user-stated edges regardless of whether those edges happen to be consistent with
what inference would have produced.

### 3.4 Idempotency

Inference writes are idempotent. Before writing any inferred edge, the inference
engine checks whether an edge with the same `fromEntityId`, `toEntityId`, and `type`
already exists. If it does:
- If the existing edge is SYSTEM_INFERRED, update its `derivedFrom` and `updatedAt`.
- If the existing edge is USER_STATEMENT, do not modify it. User authority supersedes
  inference. Log the skip at DEBUG level.

This idempotency approach is a working example of the philosophy formalized in
`Zola_Firestore_Write_Safety_Architecture.md`, which that document should be treated
as the canonical pattern source going forward.

---

## Section 4 — Truth Maintenance Policy

### 4.1 What Truth Maintenance Means

Truth maintenance is the process of keeping the graph consistent when a source fact
changes. If Jake turns out to be Brian's stepson rather than his biological son,
the PARENT_OF edge changes character — and everything that was inferred from it
needs to be re-evaluated.

### 4.2 Triggers

Truth maintenance runs when any of the following events occur:
- A USER_STATEMENT edge is deleted
- A USER_STATEMENT edge has its `type` predicate changed
- A USER_STATEMENT edge has its `fromEntityId` or `toEntityId` changed
- An edge is reclassified from USER_STATEMENT to a lower authority

Truth maintenance does not run when only metadata fields change (confidence,
sourceText, updatedAt, display fields).

### 4.3 Retraction Process

When a truth maintenance trigger fires on edge E:

1. Query all edges where `derivedFrom` contains the ID of E.
2. For each inferred edge I found:
   a. Check whether I can still be derived from the remaining graph state
      (excluding E from the graph for the purpose of this check).
   b. If I can still be derived from other source edges, update I's `derivedFrom`
      to remove the reference to E. Update `updatedAt`.
   c. If I cannot be derived without E, delete I from Firestore.
3. Run the inference pass for the new state of E (if E was modified rather than
   deleted). This produces any new inferred edges warranted by E's new state.

### 4.4 User Statement Supersedes Inference

If a USER_STATEMENT edge is written for an entity pair and predicate that already
has a SYSTEM_INFERRED edge, the inferred edge is deleted immediately. The user's
statement is the authoritative version. The user does not need to know that an
inferred edge existed — the correction is silent from the user's perspective.

### 4.5 Correction Example

Before correction:
- Brian → Jake: PARENT_OF (USER_STATEMENT)
- Brian → Cole: PARENT_OF (USER_STATEMENT)
- Jake → Cole: SIBLING_OF (SYSTEM_INFERRED, derivedFrom: [Brian→Jake, Brian→Cole])
- Cole → Jake: SIBLING_OF (SYSTEM_INFERRED, derivedFrom: [Brian→Jake, Brian→Cole])

User tells Zola: "Actually Cole is my nephew, not my son."

System corrects: Brian → Cole: PARENT_OF is deleted (or reclassified).

Truth maintenance:
- Jake → Cole: SIBLING_OF — can this still be derived? No — Cole is no longer
  Brian's child. Delete.
- Cole → Jake: SIBLING_OF — same reasoning. Delete.
- If Cole has a stored PARENT_OF edge to another entity (Cole's actual parent),
  run IR-02 against that parent to produce any warranted sibling edges from
  that relationship.

Result: Jake and Cole are no longer siblings in Zola's world model, which is correct.

---

## Section 5 — Read-Time Traversal Rules

### 5.1 When Traversal Is Used

Read-time traversal is used for two purposes:

1. To compute Tier 2 extended relationships when a query asks about a relationship
   type that is not stored (e.g., "who is Jake's aunt").
2. To enrich context when Zola is about to mention an entity — she traverses one
   hop to surface directly connected entities that might be relevant.

### 5.2 Maximum Traversal Depth

The maximum traversal depth for read-time relationship computation is 3 hops.
Beyond 3 hops, the relationship is too distant to be reliably surfaced in
conversation without risk of error or confusion.

Depth examples:
- 1 hop: PARENT_OF → produces GRANDPARENT via parent's parent (depth 2, allowed)
- 2 hops: PARENT_OF → SIBLING_OF → produces AUNT/UNCLE (depth 2, allowed)
- 3 hops: PARENT_OF → SIBLING_OF → CHILD_OF → produces COUSIN (depth 3, allowed)
- 4 hops: not computed, not surfaced

### 5.3 Traversal Confidence Decay

Each hop beyond the first stored edge reduces the confidence of the result by 0.1,
with a floor of 0.5. This confidence value is attached to the traversal result
and is used by the RecallKernel to decide whether to surface the relationship
proactively or only when directly asked.

| Confidence Range | Surfacing Policy |
|-----------------|-----------------|
| 0.85–1.0 | Surface proactively when contextually relevant |
| 0.70–0.84 | Surface when directly relevant to the current topic |
| 0.50–0.69 | Surface only when directly asked |
| Below 0.50 | Do not surface |

### 5.4 Gender Disambiguation on Traversal Results

Extended relationship labels are gender-sensitive. When a traversal result produces
an AUNT_OF or UNCLE_OF relationship, the correct label depends on the gender of
the intermediate entity (the parent's sibling). If gender is known, use the specific
label. If gender is unknown, use a neutral label (e.g., "parent's sibling").

The RecallKernel is responsible for gender resolution. If the intermediate entity
has no gender attribute, the neutral form is always preferred over a guess.

---

## Section 6 — Legacy Deletion Scope

The following files and Firestore collections are deleted in Phase 19 Track 0.
This list is the authoritative deletion scope. Nothing outside this list is
removed as part of the legacy cleanup.

### 6.1 Kotlin Source Files Deleted

- `memory/DynamicMemory.kt` — contains legacy `Person`, `Relation`, `MemoryGraph`
  models
- `memory/HybridMemoryBridge.kt` — legacy bridge between structured and person
  graph systems
- Any file in `memory/relationship/` that exists only to support the legacy
  `people/` collection path — confirm against current directory listing

### 6.2 Firestore Collections Deleted

- `users/{userId}/people/` — legacy person document collection with embedded
  `relations` arrays

### 6.3 Callsites to Remove

- All callsites to `MemoryUtils.addRelationWithReciprocal` that route through
  the legacy `Person.relations` path. Callsites that have already been migrated
  to the structured `DurableWriteAuthority` path are retained.
- All reads from `users/{userId}/people/` anywhere in the codebase.
- `HybridMemoryBridge` injection points in any service or repository.

### 6.4 What Is Not Deleted

- `memory/relationship/RelationshipWriteGovernor.kt` — retained and extended
  as the inference engine entry point
- `memory/relationship/FamilyRelationshipMapper.kt` — retained for normalization
  of legacy predicate strings to canonical enum values; may be simplified once
  legacy paths are removed
- `memory/domain/Relationship.kt` — retained as the authoritative domain model;
  schema is extended per Section 1.2 of this document
- `users/{userId}/relationships/` Firestore collection — retained as the single
  authoritative relationship store

---

## Section 7 — Open Questions

**OQ-P19-REL-01 — FamilyRelationshipMapper disposition after legacy removal**
Once the legacy `people/` path is deleted, `FamilyRelationshipMapper` exists only
to normalize string predicates to enum values for incoming Live session writes.
Evaluate whether this logic should be absorbed into `RelationshipWriteGovernor`
or retained as a standalone normalizer. Decision required before Track 1 build.

**OQ-P19-REL-02 — COLLEAGUE_OF and non-family relationship inference**
The current inference rules (IR-01, IR-02) are family-focused. Non-family
relationships (COLLEAGUE_OF, FRIEND_OF) do not currently trigger any inference.
A future consideration: if A and B are both EMPLOYEE_OF the same entity, should
COLLEAGUE_OF be inferred? Not in scope for Phase 19 — flagged for future design.

**OQ-P19-REL-03 — Confidence calibration for IR-02 sibling inference**
The 0.85 default confidence for SYSTEM_INFERRED sibling edges is illustrative.
Calibration required after Phase 19 implementation against real session data.
See also OQ-MA1 (write threshold calibration).

---

*Document created: 2026-06-09*
*Phase: Pre-Phase 19 design — decisions locked, build plan not yet written*
*Next step: Audit 2 (entity schema and attribute structure), then Phase 19 build plan*
