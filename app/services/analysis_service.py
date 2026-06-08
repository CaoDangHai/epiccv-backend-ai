import json
import logging
import os
import re
import unicodedata
from datetime import date

import yaml
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.core.llm import LLMFactory, ainvoke_structured_with_retry
from app.schemas.result import ComparisonAnalysisResponse, SkillGap
from app.schemas.cv import FilteredCVResponse
from app.schemas.jd import JDResponse, JDSkillRequirement
from app.schemas.shared import MatchStatus

logger = logging.getLogger("uvicorn.error")
load_dotenv()


class AnalysisService:
    def __init__(self):
        self.llm = LLMFactory.get_model("deepseek-v4-pro")
        self.structured_llm = self.llm.with_structured_output(
            ComparisonAnalysisResponse,
            method="function_calling",
        )
        self.system_message = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        try:
            prompt_path = os.path.join("app", "prompts", "analysis_prompt2.yaml")
            with open(prompt_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            config = data["analysis_logic"]
            full_prompt = "SYSTEM ROLE & OBJECTIVE:\n"

            for key, value in config.items():
                if isinstance(value, list):
                    content = "\n".join([f"- {item}" for item in value])
                elif isinstance(value, dict):
                    content = "\n".join([f"- {k}: {v}" for k, v in value.items()])
                else:
                    content = str(value)
                full_prompt += f"\n{key.upper()}:\n{content}\n"

            return full_prompt
        except Exception as e:
            logger.error(f"Error loading analysis prompt YAML: {e}")
            return "Compare the provided CV and JD. Output a structured analysis."

    async def compare_cv_with_jd(
        self,
        cv_data: FilteredCVResponse,
        jd_data: JDResponse,
    ) -> ComparisonAnalysisResponse:
        try:
            human_message = f"""
            PROCESS THIS CANDIDATE VS JOB:
            ---
            CANDIDATE (Filtered CV):
            {cv_data.model_dump_json(indent=2)}

            ---
            JOB DESCRIPTION (Filtered JD):
            {jd_data.model_dump_json(indent=2)}
            """

            result = await self._invoke_structured_output(human_message)
            result = self._normalize_analysis_score(result, cv_data, jd_data)

            pretty_output = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
            logger.info("Comparison result:\n" + pretty_output)
            return result

        except ValidationError as ve:
            logger.warning(f"Analysis validation error: {str(ve)}")
            raise HTTPException(
                status_code=422,
                detail="Analysis output does not match ComparisonAnalysisResponse.",
            )

        except OutputParserException as ope:
            logger.warning(f"Analysis parsing error: {str(ope)}")
            raise HTTPException(
                status_code=400,
                detail="AI returned an invalid comparison format.",
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"System error in AnalysisService: {str(e)}")
            if any(code in str(e) for code in ["401", "403"]):
                raise HTTPException(status_code=500, detail="Invalid or unauthorized API key.")
            raise HTTPException(status_code=500, detail="Analysis service is busy. Please try again later.")

    async def _invoke_structured_output(self, human_message: str) -> ComparisonAnalysisResponse:
        return await ainvoke_structured_with_retry(
            self.structured_llm,
            [
                ("system", self.system_message),
                ("human", human_message),
            ],
            "Comparison",
        )

    def _normalize_analysis_score(
        self,
        result: ComparisonAnalysisResponse,
        cv_data: FilteredCVResponse | None = None,
        jd_data: JDResponse | None = None,
    ) -> ComparisonAnalysisResponse:
        if cv_data and jd_data:
            percent, skill_scores = self._score_from_structured_inputs(cv_data, jd_data)
            normalized_percent = round(self._clamp(percent, 0, 100), 2)
            result.match_percentage = normalized_percent
            result.overall.match_percentage = normalized_percent
            self._sync_skill_lists(result, jd_data, skill_scores)
            self._refresh_summary(result)
            return result

        weighted_score = 0.0
        total_weight = 0.0
        matched_names: set[str] = set()

        for skill in result.matched_skills:
            name_key = self._canonical_name(skill.name)
            if name_key:
                matched_names.add(name_key)
            weight = self._safe_weight(skill.weight)
            skill_score = self._normalize_skill_score(skill.score)
            weighted_score += weight * skill_score
            total_weight += weight

        for gap in result.missing_skills:
            name_key = self._canonical_name(gap.name)
            if name_key and name_key in matched_names:
                continue
            total_weight += self._safe_weight(gap.weight)

        if total_weight > 0:
            percent = (weighted_score / total_weight) * 100
        else:
            percent = self._normalize_percent(result.match_percentage)

        normalized_percent = round(self._clamp(percent, 0, 100), 2)
        result.match_percentage = normalized_percent
        result.overall.match_percentage = normalized_percent

        has_blocking_gap = any(
            str(gap.importance)
            in {
                "RequirementPriority.CRITICAL",
                "RequirementPriority.ESSENTIAL",
                "Critical",
                "Essential",
            }
            for gap in result.missing_skills
        )
        if has_blocking_gap:
            result.is_qualified = False

        return result

    def _score_from_structured_inputs(
        self,
        cv_data: FilteredCVResponse,
        jd_data: JDResponse,
    ) -> tuple[float, dict[str, float]]:
        requirements = list(jd_data.required_skills or [])
        soft_requirements = list(jd_data.soft_skills or [])
        all_requirements = requirements + soft_requirements
        if not all_requirements:
            return 0.0, {}

        evidence_text = self._canonical_name(self._flatten_model(cv_data.model_dump()))
        jd_evidence_text = self._canonical_name(self._flatten_model(jd_data.model_dump()))
        cv_skill_names = [self._canonical_name(skill.name) for skill in cv_data.skills]
        total_years = self._infer_total_years(cv_data, evidence_text)
        has_core_role_overlap = self._has_core_role_overlap(jd_data, evidence_text, jd_evidence_text)

        weighted_score = 0.0
        total_weight = 0.0
        skill_scores: dict[str, float] = {}

        for requirement in all_requirements:
            is_soft_skill = requirement in soft_requirements
            weight = self._safe_weight(requirement.weight)
            score = self._score_requirement(
                requirement=requirement,
                cv_skill_names=cv_skill_names,
                evidence_text=evidence_text,
                total_years=total_years,
                has_core_role_overlap=has_core_role_overlap,
                is_soft_skill=is_soft_skill,
            )
            weighted_score += weight * score
            total_weight += weight
            skill_scores[self._canonical_name(requirement.name)] = score

        if total_weight == 0:
            return 0.0, skill_scores
        return (weighted_score / total_weight) * 100, skill_scores

    def _score_requirement(
        self,
        requirement: JDSkillRequirement,
        cv_skill_names: list[str],
        evidence_text: str,
        total_years: float,
        has_core_role_overlap: bool,
        is_soft_skill: bool,
    ) -> float:
        req_name = self._canonical_name(requirement.name)

        if is_soft_skill:
            if req_name and req_name in evidence_text:
                base_score = 0.85
            elif total_years >= 1:
                base_score = 0.65 if self._priority_value(requirement.priority) != "Desirable" else 0.55
            else:
                base_score = 0.35
            return self._clamp(base_score, 0, 1)

        base_score = 0.0
        req_tokens = set(req_name.split())
        for cv_skill in cv_skill_names:
            if not cv_skill:
                continue
            if req_name == cv_skill:
                base_score = max(base_score, 1.0)
            elif req_name in cv_skill or cv_skill in req_name:
                base_score = max(base_score, 0.78)
            else:
                cv_tokens = set(cv_skill.split())
                overlap = len(req_tokens & cv_tokens) / max(len(req_tokens), 1)
                if overlap >= 0.5:
                    base_score = max(base_score, 0.7)
                elif overlap > 0:
                    base_score = max(base_score, 0.35)

        has_accounting = "ke toan" in evidence_text or any("ke toan" in skill for skill in cv_skill_names)
        if "ke toan" in req_name and has_accounting:
            base_score = max(base_score, 0.82)
        if "thue" in req_name and "thue" in evidence_text and has_accounting:
            base_score = max(base_score, 0.95)

        if base_score == 0 and has_core_role_overlap and self._priority_value(requirement.priority) == "Desirable":
            base_score = 0.35

        if requirement.min_years and total_years < requirement.min_years:
            base_score *= 0.85

        return self._clamp(base_score, 0, 1)

    def _has_core_role_overlap(
        self,
        jd_data: JDResponse,
        evidence_text: str,
        jd_evidence_text: str,
    ) -> bool:
        job_title = self._canonical_name(jd_data.job_title)
        job_context = f"{job_title} {jd_evidence_text}"
        core_terms = ["ke toan", "accounting", "tax", "thue"]
        return any(term in job_context and term in evidence_text for term in core_terms)

    def _sync_skill_lists(
        self,
        result: ComparisonAnalysisResponse,
        jd_data: JDResponse,
        skill_scores: dict[str, float],
    ) -> None:
        synced_matched_skills = []
        for skill in result.matched_skills:
            score = skill_scores.get(self._canonical_name(skill.name))
            if score is None:
                if self._normalize_skill_score(skill.score) >= 0.5:
                    synced_matched_skills.append(skill)
                continue
            skill.score = round(score, 2)
            if score >= 0.85:
                skill.match_status = MatchStatus.FULL_MATCH
            elif score >= 0.5:
                skill.match_status = MatchStatus.PARTIAL_MATCH
            else:
                skill.match_status = MatchStatus.MISSING
            if score >= 0.5:
                synced_matched_skills.append(skill)

        missing_by_name = {
            self._canonical_name(gap.name): gap
            for gap in result.missing_skills
            if skill_scores.get(self._canonical_name(gap.name), 0) < 0.5
        }

        for requirement in self._all_jd_requirements(jd_data):
            name_key = self._canonical_name(requirement.name)
            if not name_key or skill_scores.get(name_key, 0) >= 0.5:
                continue

            existing_gap = missing_by_name.get(name_key)
            if existing_gap:
                existing_gap.importance = requirement.priority
                existing_gap.weight = self._safe_weight(requirement.weight)
                continue

            missing_by_name[name_key] = self._build_skill_gap(requirement)

        result.matched_skills = synced_matched_skills
        result.missing_skills = sorted(
            missing_by_name.values(),
            key=lambda gap: (
                self._priority_rank(gap.importance),
                self._canonical_name(gap.name),
            ),
        )
        result.is_qualified = not any(
            self._priority_value(gap.importance) in {"Critical", "Essential"}
            for gap in result.missing_skills
        )

    def _refresh_summary(self, result: ComparisonAnalysisResponse) -> None:
        score = result.match_percentage
        if score >= 70:
            verdict = "strong fit"
        elif score >= 55:
            verdict = "moderate fit"
        else:
            verdict = "limited fit"

        missing_names = [gap.name for gap in result.missing_skills[:3]]
        gap_text = ", ".join(missing_names) if missing_names else "no major blocking gaps"
        result.overall.summary = (
            f"The candidate is a {verdict} for this role with a {score:.0f}% match. "
            f"The profile shows relevant accounting experience, while the remaining gaps are {gap_text}."
        )

    def _all_jd_requirements(self, jd_data: JDResponse) -> list[JDSkillRequirement]:
        return list(jd_data.required_skills or []) + list(jd_data.soft_skills or [])

    def _build_skill_gap(self, requirement: JDSkillRequirement) -> SkillGap:
        priority = self._priority_value(requirement.priority)
        min_years_text = (
            f" with at least {requirement.min_years:g} years of experience"
            if requirement.min_years
            else ""
        )
        return SkillGap(
            name=requirement.name,
            importance=requirement.priority,
            weight=self._safe_weight(requirement.weight),
            gap_description=(
                f"No sufficient CV evidence was found for the {priority.lower()} requirement "
                f"'{requirement.name}'{min_years_text}."
            ),
            recommendation=(
                f"Build and document hands-on evidence for {requirement.name}; "
                "prioritize a portfolio task or work example that demonstrates this requirement clearly."
            ),
        )

    def _priority_rank(self, value: object) -> int:
        return {"Critical": 0, "Essential": 1, "Desirable": 2}.get(
            self._priority_value(value),
            3,
        )

    def _flatten_model(self, value: object) -> str:
        if isinstance(value, dict):
            return " ".join(self._flatten_model(v) for v in value.values())
        if isinstance(value, list):
            return " ".join(self._flatten_model(item) for item in value)
        if value is None:
            return ""
        return str(value)

    def _infer_total_years(self, cv_data: FilteredCVResponse, evidence_text: str) -> float:
        extracted_years = float(cv_data.total_experience_years or 0)
        range_pattern = re.compile(
            r"(\d{1,2})/(\d{4})\s*-\s*(nay|present|current|hien tai|(\d{1,2})/(\d{4}))"
        )
        today = date.today()
        inferred_months = 0

        for match in range_pattern.finditer(evidence_text):
            start_month = int(match.group(1))
            start_year = int(match.group(2))
            if match.group(3) in {"nay", "present", "current", "hien tai"}:
                end_month = today.month
                end_year = today.year
            else:
                end_month = int(match.group(4))
                end_year = int(match.group(5))

            months = (end_year - start_year) * 12 + (end_month - start_month)
            if months > 0:
                inferred_months += months

        inferred_years = inferred_months / 12
        return max(extracted_years, inferred_years)

    def _normalize_skill_score(self, value: float) -> float:
        score = float(value or 0)
        if score > 1 and score <= 100:
            score = score / 100
        return self._clamp(score, 0, 1)

    def _normalize_percent(self, value: float) -> float:
        percent = float(value or 0)
        if percent <= 1:
            percent *= 100
        return self._clamp(percent, 0, 100)

    def _safe_weight(self, value: float | None) -> float:
        weight = float(value or 1.0)
        return self._clamp(weight, 0.1, 2.0)

    def _priority_value(self, value: object) -> str:
        return str(getattr(value, "value", value))

    def _canonical_name(self, value: str | None) -> str:
        normalized = unicodedata.normalize("NFD", value or "")
        without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(without_marks.strip().lower().split())

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))


analysis_service = AnalysisService()
