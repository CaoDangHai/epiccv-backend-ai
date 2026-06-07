# Critical Gaps Fix Report

Date: 2026-06-07

## Issue

Analysis responses could show a low match score, such as 40%, while `missing_skills` was empty. The frontend reads Critical Gaps directly from `missing_skills`, so the UI had no critical gaps to display.

## Root Cause

`AnalysisService._sync_skill_lists()` only filtered the `missing_skills` returned by the LLM. If the LLM omitted a missing critical requirement, deterministic scoring still lowered the score, but no `SkillGap` object was created.

## Fixes

- Added deterministic gap creation from every JD requirement whose computed skill score is below `0.5`.
- Preserved or updated existing LLM-provided gaps when they match a low-scoring JD requirement.
- Removed low-scoring skills from `matched_skills` so a missing requirement is not shown as both matched and missing.
- Sorted missing skills by importance: `Critical`, `Essential`, then `Desirable`.
- Set `is_qualified` to `false` when any `Critical` or `Essential` gap remains.
- Added generated gap descriptions and recommendations so the roadmap generator has usable input.

## Verification

- Ran Python compile check: `.venv/Scripts/python.exe -m compileall app main.py`.
- Ran a deterministic service check with `score=40`, no initial missing skills, and a Critical JD requirement. The service now creates the Critical gap and marks the candidate as not qualified.
