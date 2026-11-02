# The Concordance — Mimisbrunnr 500 ⨯ All-Features 272

*One page where both of Volmarr's roads for Mythic Agent Coder can be read
together. Written for slice M-002 of the All-Features Roadmap
(`docs/MYTHIC_CODER_FEATURE_ROADMAP_2026-10-30.md` in the campaign shelf;
repo copy filed by the parent push), against Volmarr's own
`MYTHIC_AGENT_CODER_CLI_500_SLICE_ULTIMATE_MIMISBRUNNR_ROADMAP.md`
(437,402 bytes, 20 campaigns × 25 slices = 500 slices, read in full
structure — every campaign and slice title — on 2026-10-30).*

*Rule of this page: conflicts are listed, never silently resolved.
Where a resolution is recorded, it names its authority.*

---

## 1. The two roads, as they stand

**The Mimisbrunnr road (Volmarr's own, the elder road).** 500 slices in
20 campaigns of 25, each campaign closing on a Gate slice. Its own laws
travel with it: Mission, Prime Directives, a Universal Slice Definition
of Done, the Anti-Placeholder Law, the Campaign Gate Law.

**Its measured progress (in-repo evidence):** slices **001–050 are
DONE**, forged 2026-10-10/11 by the dawn and dusk forge runs and
receipted in `docs/FORGE_RECEIPT_021_025.md` (Bedrock Gate review:
slices 001–025 banked, 026–040 in flight) and
`docs/FORGE_RECEIPT_041_050.md` (slices 041–050, Pantheon Gate; suite at
that gate: **1147 passed, 2 skipped, 0 failed**). No receipts exist
beyond slice 050: **slices 051–500 are carved but unstarted in-repo.**

**The All-Features road (the younger road, 2026-10-30).** 272 slices in
11 parts (M-001–M-272), commissioned to absorb the whole CLI-coding-app
field's feature canon in its kindest form, with Mythic Engineering as
the method. It opens with this concordance precisely so the elder road
is honoured, not paved over.

**Numbering discipline (binding):** the elder road's slices are cited
**MIM-001…MIM-500**; the younger road's are **M-001…M-272**. Bare
numbers are forbidden in campaign records from this page on — MIM-050
(Pantheon Gate) and M-050 (LSP navigation) are different slices.

## 2. The mapping — every Mimisbrunnr campaign onto the new road

| Mimisbrunnr campaign | Slices | Lands in (All-Features) | Verdict |
|---|---|---|---|
| C01 Bedrock Truth | MIM-001–025 | Part I (M-001, M-003, M-009–M-013) + Part XI | **ABSORBED** — the census/audit body is Part I's own work; its gate discipline feeds Part XI's regression court (M-257) |
| C02 Provider Pantheon | MIM-026–050 | Part II (M-019–M-042) | **DIRECT MAP, DONE** — banked; see §3 |
| C03 Context Forge | MIM-051–075 | Part VII (M-147–M-170); instruction precedence → M-149; untrusted-content boundaries → Part V | **DIRECT MAP** |
| C04 Memory of Muninn | MIM-076–100 | Part VII (M-150, M-154–M-157, M-164–M-166, M-168) | **DIRECT MAP + ANNEX** — Muninn's memory taxonomy (episodic/semantic/procedural/decision/failure/preference/convention) is finer than Part VII's grain and stands as its annex |
| C05 Tool Forge | MIM-101–125 | Part III (M-047, M-048, M-058, M-059) + Part IV (M-071–M-073) + Part V (M-095, M-096) | **SPREAD MAP** |
| C06 Safe Execution Citadel | MIM-126–150 | Part V (M-095–M-120) | **DIRECT MAP, one slice SUPERSEDED** — see Conflict 1 |
| C07 Edit Intelligence | MIM-151–175 | Part IV (M-071–M-094); AST edits → M-048; format/encoding preservation → M-053 | **DIRECT MAP** |
| C08 Repository Mind | MIM-176–200 | Part III (M-044–M-046, M-062, M-069); map explainability → M-045 | **DIRECT MAP** |
| C09 Mythic Engineering Orchestrator | MIM-201–225 | Part VI (M-121–M-127) + Part IX (M-201–M-205) | **DIRECT MAP** — the offices' home is VI; their protocol's home is IX |
| C10 Autonomous Swarm | MIM-226–250 | Part VI (M-124–M-146); budgets → M-107; leases/heartbeats → M-104, M-207 | **DIRECT MAP** |
| C11 Roadmap Devourer | MIM-251–275 | Part IX (M-201–M-232) | **DIRECT MAP** — the Method Engine's direct ancestor; M-218 loads the elder road itself as a campaign through this concordance |
| C12 Verification Engine | MIM-276–300 | Part XI (M-255–M-257, M-260) + the Auditor's gate (M-130, M-205) | **DIRECT MAP** |
| C13 Debugging Oracle | MIM-301–325 | Part III (M-054, M-055) | **MAP + ANNEX** — the DAP debugger maps; the Oracle's hypothesis/repair loop (MIM-307–322) has no M-slice and stands as Part III's deepening annex; Doctor V2 (MIM-323) → M-039, M-168 |
| C14 Code Intelligence | MIM-326–350 | Part III (M-043–M-053, M-063, M-064); language packs → M-068 | **DIRECT MAP** |
| C15 Testsmith | MIM-351–375 | Part III (M-056, M-057) + Part XI | **MAP + ANNEX** — test intelligence maps; test *generation* (MIM-354–358) stands as annex depth |
| C16 Git Collaboration Forge | MIM-376–400 | Part IV (M-078–M-085) + Part X (M-246, M-247) | **DIRECT MAP** |
| C17 MCP Machine API | MIM-401–425 | Part X (M-233–M-235); headless face → M-106 | **DIRECT MAP + ANNEX** — the Python/TypeScript client SDKs (MIM-421–422) stand as Part X annex |
| C18 TUI Valhalla | MIM-426–450 | Part VIII (M-171–M-200) | **DIRECT MAP** |
| C19 Multimodal Forge | MIM-451–475 | Part II (M-037) + Part VII (M-148) + Part VIII (M-180) | **SPREAD MAP + ANNEX** — screenshot-reasoning workflows (MIM-455, 464, 465) stand as annex |
| C20 Local Sovereignty | MIM-476–500 | Part II (M-023–M-025, M-040) + Part XI (M-258, M-259) | **DIRECT MAP** |

## 3. What the banked elder work (MIM-001–050) counts for

The All-Features road does not re-carve proven stone:

- **MIM-001–025 (Bedrock Truth)** is the elder road's own census of
  this repo. Part I's census (M-001) and audits (M-003, M-009–M-013)
  must *start* from it and M-001's feature census is the one genuinely
  new instrument (it faces outward, at the field). Bedrock's evidence
  stands; Part I re-proves only what has drifted since 2026-10-11.
- **MIM-026–050 (Provider Pantheon)** is DONE and is Part II's
  foundation evidence: provider contract, per-adapter hardening
  (OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, Ollama,
  llama.cpp, LM Studio), capability/cost/health/failover, conformance
  suite. It does **not** bank M-019–M-042: the younger road changes
  the *shape* (registry-as-data, M-019; the universal adapter, M-020;
  Aesir as provider, M-025; Kista key custody, M-032) — Part II's
  slices remain to build, standing on Pantheon's proven contracts.
- **MIM-035 (vLLM adapter)** has no M-slice: it stands as a named
  extra under Part II, kept, not lost.

## 4. Territory only the younger road holds

No Mimisbrunnr ancestor: the feature census itself (M-001) and this
concordance (M-002); Project Aesir as a provider (M-025); Kista key
custody (M-032, M-244); the Samverk bridge (M-242); the Samtal bridge
(M-243); the WYRD seam (M-249); the README guardian as an edit-layer
refusal (M-079 — Volmarr's standing law, now machinery); Jarl mode,
the plain-language skin (M-182); standing orders kept by the app
(M-226 — *never make the user say it twice*, as a feature); rival
importers (M-241, from M-014's study); the Stranger Test gates
(M-200, M-266).

## 5. Territory only the elder road holds (preserved, not dropped)

Kept as named annexes under their mapped parts: Muninn's memory
taxonomy (C04); the Debugging Oracle's hypothesis-and-repair loop
(C13); Testsmith's test generation (C15); the Pantheon's vLLM adapter
(MIM-035); the client SDKs (MIM-421–422); the Citadel's escape-attempt
suite (MIM-149 — feeds the younger road's red-team pack, M-118);
Local Sovereignty's Pi/Jetson research profiles (MIM-495–496 — feed
M-258's measured budgets). An annex is a promise: when its part is
built, the annex is read before the part's gate can pass.

## 6. Conflicts — listed, with their resolutions and authorities

1. **The container slice vs the no-Docker law.** MIM-142 (Container
   Sandbox Adapter) contradicts the younger road's Law 3 and §6
   (no Docker, ever; sandboxing is native or honestly absent) and
   M-097 (native OS sandbox). **Resolution: the younger road wins** —
   it is the later carving, and it carries Volmarr's standing
   no-Docker law with it. MIM-142 is SUPERSEDED as a build slice; its
   boundary/interface thinking may be read as design input to M-097.
   MIM-141 (Temporary Sandbox Adapter) is unaffected and maps to
   M-097's road.
2. **Numbering collision.** Both roads number from 001. Resolved by
   the prefix discipline in §1 (MIM-### vs M-###) — a citation rule,
   not a renumbering: neither file is edited.
3. **Two gate philosophies.** The elder road gates every 25 slices
   (Campaign Gate Law); the younger road gates per part. **Both
   stand**: part gates adopt the campaign-gate form (a named gate
   slice with evidence), and within Part IX, campaigns loaded via
   M-218 keep their own 25-slice gates.
4. **Two provider shapes.** Pantheon's per-adapter code slices vs
   the Provider Ocean's registry-as-data (M-019). **Resolution: the
   younger road's shape governs new work** (later carving); the
   Pantheon's banked adapters and conformance suite are the
   acceptance depth each registry entry must meet.

*No other conflicts were found in the titles-and-laws reading. A
slice-body-level conflict, if one surfaces while building, is added
here before it is acted on — never resolved in silence.*

## 7. How the binding works from here

- The campaign state file (`CAMPAIGN_STATE.md`, repo root) carries
  both roads' totals and this concordance's verdict; the keeper
  resumes from it.
- When Part IX (M-218) loads the elder road as a campaign, it loads
  it *through* this page: a Mimisbrunnr slice is offered for work
  only with its mapped M-part named beside it.
- Banked elder slices (MIM-001–050) are evidence, not currency: they
  prove foundations; they do not mark M-slices done.
- This page is amended, never rewritten: new findings append dated
  lines under §6.

*Carved 2026-10-30, campaign opening, branch
`yrsa/feature-roadmap-build`.*
