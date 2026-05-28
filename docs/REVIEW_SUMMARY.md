# OpenNarrator Spec Plan Review Summary

**Reviewer:** AI Agent (intelligent-workflow skill)  
**Date:** 2026-05-27  
**Scope:** Complete review and improvement of specification, implementation plan, and supporting documentation

---

## Executive Summary

Conducted a comprehensive review of the OpenNarrator spec plan, identifying critical gaps, inconsistencies, and risks. The most significant finding is that **voice quality is the #1 risk** — Piper's `en_US-lessac` voice failed the quality gate (testers would not listen to a 10-hour book in this voice), and this risk was not adequately addressed in the original spec.

**Key Improvements:**
- Added Phase 0 (Engine Selection & Voice Quality Gate) before implementation begins
- Resolved all 8 open questions in SPEC.md
- Fixed TTS engine priority inconsistency (Piper first, not F5-TTS)
- Added comprehensive voice quality testing methodology
- Expanded risk mitigation strategies with concrete response plans
- Added detailed pyproject.toml requirements
- Fixed spike verdict inconsistency (PARTIAL, not VALIDATED)
- Addressed MacBook Neo hardware constraints (A18 Pro, no MPS GPU)

**Files Modified:** 6 documents  
**Total Changes:** 50+ edits across all files

---

## Files Modified

### 1. `/docs/SPEC.md` — Core Specification

**Major Improvements:**

#### Fixed TTS Engine Priority (Critical Inconsistency)
- **Before:** Tech stack listed F5-TTS as "Primary" and Piper as "Fallback"
- **After:** Corrected to reflect actual strategy: Piper v0.1 (validates pipeline), F5-TTS v0.2 (quality + cloning)
- **Rationale:** Implementation plan said Piper first, spec said F5-TTS first — this was a major contradiction

#### Resolved All Open Questions
- **Before:** 8 open questions (name, first engine, distribution, commercial use, target OS, cover art, SSML, voice sample length)
- **After:** All questions answered and documented in "Decisions Made" section
- **Rationale:** These were already decided in IMPLEMENTATION_PLAN.md but not reflected in SPEC.md

#### Added Voice Quality Gate (Decision 6)
- **What:** Explicit go/no-go criteria before committing to any TTS engine
- **Why:** Voice quality is the #1 risk. If voices sound robotic, users won't listen for hours
- **Criteria:** 2+ testers listen to 5-minute sample, answer "Would you listen to a 10-hour book in this voice?" (≥50% must say "Yes")
- **Impact:** Prevents shipping with unacceptable voice quality

#### Added Voice Quality Requirements Section
- **Voice Candidates:** `en_US-lessac` (failed), `en_US-libritts` (testing), Kokoro (testing)
- **Quality Gate Criteria:** Listening test methodology, pass threshold, alternative MOS scoring
- **Fallback Strategy:** What to do if all CPU-friendly engines fail (accept GPU requirement, pivot, or defer)

#### Improved Success Criteria
- **Added:** Voice consistency, GPU support, voice cloning requirements
- **Clarified:** Test coverage targets, documentation requirements

#### Enhanced Testing Strategy
- **Added:** Voice Quality Testing section with 5 methodologies:
  1. **Quality Gate Test** (manual, required for v0.1)
  2. **MOS Testing** (optional, more rigorous)
  3. **A/B Testing** (comparing engines)
  4. **Performance Benchmarks** (RTF measurement)
  5. **Regression Tests** (automated, catch quality degradation)
- **Added:** Voice quality test fixtures (Pride and Prejudice, technical text, dialogue)

---

### 2. `/docs/IMPLEMENTATION_PLAN.md` — Task Breakdown

**Major Improvements:**

#### Added Phase 0: Engine Selection & Voice Quality Gate (CRITICAL)
- **Why:** Cannot commit to implementation until voice quality is validated
- **Tasks:**
  - Task 0.1: Test Piper `en_US-libritts` voice (audiobook-trained)
  - Task 0.2: Test Kokoro on MacBook Neo
  - Task 0.3: Validate F5-TTS CPU performance on A18 Pro (no MPS GPU)
  - Task 0.4: Make final engine decision with explicit decision tree
- **Checkpoint:** Voice quality gate passed, engine choice documented
- **Impact:** Prevents building v0.1 with unacceptable voice quality

#### Expanded Risk Mitigation Strategies
- **Before:** 5 risks listed with brief mitigations
- **After:** 3 categories of risks with detailed response plans:
  - **Critical Risks** (block v0.1): Voice quality, MacBook Neo GPU, Kokoro Python 3.13
  - **Technical Risks** (manageable): Piper subprocess changes, ffmpeg not installed, EPUB structure varies
  - **Strategic Risks** (product-market fit): Voice quality never reaches "good enough", users expect ElevenLabs quality, TTS landscape changes
- **Added:** Risk Response Plan with 3 options if voice quality gate fails (accept GPU, pivot, defer)

#### Added Detailed pyproject.toml Requirements (Task 1)
- **Complete pyproject.toml template** with:
  - Build system (hatchling)
  - Project metadata (name, version, dependencies)
  - Optional dependencies (dev, piper)
  - Entry points (`opennarrator` CLI command)
  - Tool configurations (ruff, mypy, pytest)
- **Added:** Directory structure specification
- **Added:** Setup commands with verification steps
- **Rationale:** Task 1 said "create pyproject.toml" but didn't specify what should be in it

#### Updated Overview
- **Before:** "Build the core audiobook pipeline with Piper as the first TTS engine"
- **After:** "Build the core audiobook pipeline with a quality-validated TTS engine (Piper, Kokoro, or F5-TTS — see Phase 0)"
- **Rationale:** Engine choice is not yet committed; depends on voice quality gate

---

### 3. `/docs/TTS_ENGINES.md` — Engine Comparison

**Major Improvements:**

#### Updated Comparison Matrix with Real Spike Data
- **Before:** Theoretical comparison with no benchmark data
- **After:** Includes actual RTF measurements from Piper spike (0.1-0.2x on Pi 5)
- **Added:** Quality indicators (⚠️ for voices that failed quality gate)
- **Added:** "Speed (CPU)" column to clarify CPU-only performance

#### Updated Support Roadmap
- **Before:** Piper as "Primary" for v0.1
- **After:** Piper as "Testing" (libritts voice), Kokoro as "Testing" (pending MacBook Neo), F5-TTS as "Fallback" (CPU perf unvalidated)
- **Added:** Current status note referencing Phase 0

#### Added Comprehensive Spike Results Section
- **Spike 001 (Piper):**
  - Benchmark results: RTF 0.1-0.2x on Pi 5
  - What worked: Speed, API, voice downloads, subprocess isolation
  - What failed: Voice quality (lessac robotic, failed quality gate)
  - API quirks: wave.Wave_write requirement
  - Untested: libritts voice, high-quality model tier
  - Verdict: PARTIAL (technically excellent, quality unvalidated)

- **Spike 002 (Kokoro):**
  - Status: Blocked on Pi (Python 3.13), pending on MacBook Neo
  - Why it matters: Apache 2.0, reportedly more natural, small model
  - Risk: If Kokoro also fails, may need to accept F5-TTS GPU requirement

- **Spike 003 (F5-TTS CPU Performance):**
  - Status: Not started
  - Test plan: Synthesize 1-minute sample, measure RTF
  - Acceptable: RTF < 0.5x
  - Impact if too slow: Accept GPU requirement, pivot, or defer

#### Added Voice Quality Gate Section
- **Test Methodology:** 5-minute sample, 2+ testers, yes/no question
- **Current Status:** lessac failed, libritts untested, Kokoro untested
- **Why This Matters:** Voice quality is the #1 risk for long-form listening

#### Updated "Why Piper First?" Section
- **Before:** "Piper first" with no caveats
- **After:** "Piper first (with caveats)" — engine is right, but voice quality unvalidated
- **Added:** Fallback strategy if Piper libritts fails (test Kokoro, validate F5-TTS, pivot or defer)

---

### 4. `/spikes/001-piper-feasibility/README.md` — Piper Spike Report

**Critical Fix:**

#### Fixed Verdict from VALIDATED to PARTIAL
- **Before:** "Verdict: VALIDATED ✅" (misleading)
- **After:** "Verdict: PARTIAL ✅⚠️" (honest)
- **Rationale:** Spike validated speed and API, but voice quality failed quality gate. Calling it "VALIDATED" implied the spike was complete, when in fact the most important criterion (voice quality for long-form listening) was not met.
- **Added:** Clear separation of what was validated (speed, API, downloads) vs what failed (voice quality)
- **Added:** Recommendation to test libritts voice and Kokoro before committing to Piper

---

### 5. `/HANDOFF.md` — MacBook Neo Handoff Document

**Major Improvements:**

#### Updated Spike Results
- **Before:** "Spike 001 — Piper TTS (PARTIAL)" with no detail
- **After:** "Spike 001 — Piper TTS (PARTIAL — Technical ✅, Quality ⚠️)" with explicit breakdown
- **Added:** Quality gate failure explanation (testers would not listen to 10-hour book)
- **Added:** Next step (test libritts voice)

#### Added MacBook Neo Hardware Constraints (CRITICAL)
- **What:** MacBook Neo has A18 Pro with **no MPS GPU** — CPU-only for all TTS inference
- **Impact:** F5-TTS may require GPU for acceptable performance
- **Risk:** If F5-TTS too slow on CPU, must accept GPU requirement or pivot
- **Added:** This as "Known Gotcha" #5 with detailed explanation

#### Improved "Next Action" Section
- **Before:** 6 steps with no priority
- **After:** Priority-ordered with explicit decision tree:
  1. Test Piper libritts (if passes → Piper validated)
  2. If libritts fails → test Kokoro (if passes → Kokoro becomes v0.1 engine)
  3. If Kokoro fails → validate F5-TTS CPU performance (if acceptable → F5-TTS is v0.1 engine)
  4. If all fail → pivot or defer
- **Added:** Voice quality gate criteria summary

---

### 6. `/README.md` — Main Project README

**Major Improvements:**

#### Updated "Detailed v0.1.0 Plan" Table
- **Before:** 5 phases (Skeleton, Input Pipeline, TTS Integration, Audio Assembly, CLI & Ship)
- **After:** 6 phases with Phase 0 (Engine Selection) added
- **Added:** Explanation of why Phase 0 is first (voice quality is #1 risk)
- **Updated:** All phase statuses to reflect current state (Phase 0 in progress, others blocked)

#### Updated TTS Engine Strategy Table
- **Before:** Piper as "v0.1 baseline (spiked — robotic, exploring alternatives)"
- **After:** Piper as "v0.1 candidate (lessac robotic, testing libritts)"
- **Added:** Current status note explaining engine selection in progress
- **Added:** Link to Voice Quality Gate documentation

#### Updated Spike Results Table
- **Before:** Piper "PARTIAL" with brief note
- **After:** Piper "PARTIAL ✅⚠️" with explicit breakdown (Technical ✅, Quality ⚠️)
- **Added:** Voice Quality Gate explanation
- **Added:** Link to Voice Quality Requirements

#### Updated Project Structure
- **Before:** "Piper ✅, Kokoro 🔄"
- **After:** "Piper ⚠️, Kokoro 🔄" (Piper quality unvalidated)
- **Added:** Note explaining Piper spike is technically validated but voice quality unvalidated

#### Updated Quickstart
- **Before:** Voice download command used `en_US-lessac`
- **After:** Voice download command uses `en_US-libritts` (audiobook-trained, more natural)
- **Added:** Note that engine selection is in progress and voice choice may change
- **Added:** Voice quality explanation with link to documentation

---

## Key Findings & Recommendations

### Critical Risks Identified

1. **Voice Quality (BLOCKER)**
   - **Risk:** Piper's `en_US-lessac` voice failed quality gate (testers would not listen to 10-hour book)
   - **Impact:** If voice quality unacceptable, entire value proposition fails
   - **Mitigation:** Test `en_US-libritts` and Kokoro before committing to engine (Phase 0)
   - **Status:** In progress (Phase 0)

2. **MacBook Neo Has No MPS GPU (HIGH)**
   - **Risk:** F5-TTS may require GPU for acceptable performance
   - **Impact:** If F5-TTS too slow on CPU, must accept GPU requirement or pivot
   - **Mitigation:** Validate F5-TTS CPU performance early (Task 0.3)
   - **Status:** Not started

3. **Kokoro Blocked on Python 3.13 (MEDIUM)**
   - **Risk:** Cannot test Kokoro on Pi 5 (Python 3.13, misaki dependency incompatible)
   - **Impact:** Delays Kokoro testing
   - **Mitigation:** Test on MacBook Neo (likely Python 3.12)
   - **Status:** Pending (Task 0.2)

### Documentation Inconsistencies Fixed

1. **TTS Engine Priority:** SPEC said F5-TTS first, IMPLEMENTATION_PLAN said Piper first → Fixed to Piper first
2. **Spike Verdict:** Spike README said "VALIDATED", main README said "PARTIAL" → Fixed to PARTIAL (with explanation)
3. **Open Questions:** SPEC listed 8 open questions, IMPLEMENTATION_PLAN had answers → Resolved all in SPEC
4. **Phase 0 Missing:** IMPLEMENTATION_PLAN had 5 phases, README had 5 phases → Added Phase 0 to both
5. **Voice Quality Not Addressed:** No mention of voice quality risk in original spec → Added comprehensive voice quality section

### Recommendations for Next Steps

1. **Execute Phase 0 Immediately (CRITICAL)**
   - Test Piper `en_US-libritts` voice (Task 0.1)
   - If fails, test Kokoro on MacBook Neo (Task 0.2)
   - If fails, validate F5-TTS CPU performance (Task 0.3)
   - Make final engine decision (Task 0.4)
   - **Do not proceed to Phase 1 until voice quality gate passes**

2. **Set Up Development Environment**
   - Create pyproject.toml using template in IMPLEMENTATION_PLAN.md
   - Set up directory structure
   - Configure ruff, mypy, pytest
   - Verify setup with `ruff check src/ && mypy src/ && pytest`

3. **Prepare Voice Quality Test Materials**
   - Download Pride and Prejudice (Project Gutenberg, public domain)
   - Extract first chapter (~2,500 words, 5-minute sample)
   - Prepare listening test methodology (2+ testers, yes/no question)
   - Create results template (tests/voice_quality/results/)

4. **Validate F5-TTS CPU Performance Early**
   - Don't wait until Phase 0 Task 0.3
   - Test now to understand if GPU requirement is real
   - If F5-TTS too slow on CPU, adjust expectations and roadmap

5. **Communicate Voice Quality Risk to Stakeholders**
   - Update project status to reflect voice quality uncertainty
   - Set expectations: v0.1 may be delayed if no CPU-friendly engine passes quality gate
   - Be transparent: "We're testing voices to find one suitable for long-form listening"

---

## Conclusion

The OpenNarrator spec plan is now **significantly more robust, honest, and actionable**. The original spec was technically sound but glossed over the #1 risk: voice quality. By adding Phase 0 (Engine Selection & Voice Quality Gate), we ensure that v0.1 ships with a voice that users will actually want to listen to for hours.

**Key Achievements:**
- ✅ Identified and addressed critical voice quality risk
- ✅ Fixed all documentation inconsistencies
- ✅ Added comprehensive voice quality testing methodology
- ✅ Expanded risk mitigation with concrete response plans
- ✅ Clarified MacBook Neo hardware constraints
- ✅ Provided detailed pyproject.toml requirements
- ✅ Made spike verdict honest (PARTIAL, not VALIDATED)

**Next Action:** Execute Phase 0 immediately. Do not proceed to implementation until voice quality gate passes. The entire value proposition depends on finding a CPU-friendly voice that sounds good enough for long-form listening.

---

## Files Modified Summary

| File | Lines Modified | Key Changes |
|------|---------------|-------------|
| `/docs/SPEC.md` | ~150 lines | Added voice quality gate, resolved open questions, improved testing strategy |
| `/docs/IMPLEMENTATION_PLAN.md` | ~200 lines | Added Phase 0, expanded risks, added pyproject.toml requirements |
| `/docs/TTS_ENGINES.md` | ~180 lines | Added spike results, voice quality gate, updated roadmap |
| `/spikes/001-piper-feasibility/README.md` | ~20 lines | Fixed verdict (PARTIAL, not VALIDATED) |
| `/HANDOFF.md` | ~80 lines | Updated spike results, added hardware constraints, improved next actions |
| `/README.md` | ~100 lines | Updated roadmap, fixed inconsistencies, added voice quality notes |
| **Total** | **~730 lines** | **6 files modified, 50+ edits** |

---

**Review Completed:** 2026-05-27  
**Reviewer:** AI Agent (intelligent-workflow skill)  
**Status:** ✅ All 13 tasks completed
