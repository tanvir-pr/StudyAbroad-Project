"""Rule-based program match engine (no LLM). Pure functions for easy unit tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class MatchWeights:
    cgpa: float = 0.35
    ielts: float = 0.25
    budget: float = 0.25
    deadline: float = 0.15
    safe_threshold: float = 75.0
    target_threshold: float = 50.0
    deadline_full_days: int = 30
    cgpa_full_margin: float = 0.5


@dataclass(frozen=True)
class StudentMatchInput:
    cgpa: Decimal
    ielts: Decimal | None
    budget_eur: Decimal
    target_degree: str
    subject: str | None = None


@dataclass(frozen=True)
class ProgramMatchInput:
    id: str
    name: str
    degree: str
    language: str
    tuition_eur: Decimal
    min_cgpa: Decimal
    min_ielts: Decimal
    intake_deadline: date
    scholarship: bool
    university_name: str
    city_name: str
    country_code: str
    monthly_living_cost: Decimal  # rent + food + transport


@dataclass(frozen=True)
class MatchResult:
    program_id: str
    program_name: str
    university_name: str
    city_name: str
    country_code: str
    degree: str
    language: str
    tuition_eur: Decimal
    intake_deadline: date
    scholarship: bool
    score: float
    band: str  # Safe | Target | Reach
    reasons: list[str]
    estimated_year_cost_eur: Decimal


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def hard_filter(
    student: StudentMatchInput,
    program: ProgramMatchInput,
    *,
    today: date,
) -> str | None:
    """Return skip reason if program should be excluded, else None."""
    if student.target_degree.lower() != program.degree.lower():
        return "degree_mismatch"
    if program.intake_deadline < today:
        return "deadline_passed"
    # Language / IELTS gate: English (or any) programs that require IELTS need a score.
    if program.min_ielts > 0 and student.ielts is None:
        return "ielts_required"
    return None


def score_cgpa(
    student_cgpa: Decimal,
    min_cgpa: Decimal,
    *,
    full_margin: float,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    margin = float(student_cgpa - min_cgpa)
    if margin < 0:
        # 1.0 CGPA short → 0; linear up to 0 margin → 50 baseline then margin boosts
        deficit = -margin
        score = _clamp(50.0 * (1.0 - min(deficit, 1.0)))
        reasons.append(f"CGPA {deficit:.2f} কম (min {min_cgpa})")
        return score, reasons
    if full_margin <= 0:
        return 100.0, reasons
    score = _clamp(50.0 + 50.0 * min(margin / full_margin, 1.0))
    if margin >= full_margin:
        reasons.append(f"CGPA ভালো মার্জিন (+{margin:.2f})")
    else:
        reasons.append(f"CGPA মার্জিন +{margin:.2f}")
    return score, reasons


def score_ielts(
    student_ielts: Decimal | None,
    min_ielts: Decimal,
) -> tuple[float | None, list[str]]:
    """Return None score when IELTS component should be skipped (not required)."""
    reasons: list[str] = []
    if min_ielts <= 0:
        return None, reasons
    if student_ielts is None:
        return 0.0, ["IELTS স্কোর নেই"]
    margin = float(student_ielts - min_ielts)
    if margin < 0:
        deficit = -margin
        score = _clamp(50.0 * (1.0 - min(deficit / 2.0, 1.0)))
        reasons.append(f"IELTS {deficit:.1f} কম (min {min_ielts})")
        return score, reasons
    # Full marks from +0.5 band upward
    score = _clamp(50.0 + 50.0 * min(margin / 0.5, 1.0))
    if margin >= 0.5:
        reasons.append(f"IELTS ভালো মার্জিন (+{margin:.1f})")
    else:
        reasons.append(f"IELTS মার্জিন +{margin:.1f}")
    return score, reasons


def score_budget(
    budget_eur: Decimal,
    tuition_eur: Decimal,
    monthly_living: Decimal,
) -> tuple[float, Decimal, list[str]]:
    year_cost = tuition_eur + (monthly_living * Decimal("12"))
    reasons: list[str] = []
    if year_cost <= 0:
        return 100.0, year_cost, reasons
    ratio = float(budget_eur / year_cost)
    if ratio >= 1.0:
        score = 100.0
        reasons.append(f"বাজেট যথেষ্ট (≈€{year_cost:.0f}/yr)")
    elif ratio >= 0.7:
        score = _clamp(50.0 + 50.0 * ((ratio - 0.7) / 0.3))
        reasons.append(f"বাজেট টাইট (≈€{year_cost:.0f}/yr লাগবে)")
    else:
        score = _clamp(50.0 * (ratio / 0.7))
        short = year_cost - budget_eur
        reasons.append(f"বাজেট ≈€{short:.0f} কম (≈€{year_cost:.0f}/yr)")
    return score, year_cost, reasons


def score_deadline(
    intake_deadline: date,
    *,
    today: date,
    full_days: int,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    days_left = (intake_deadline - today).days
    if days_left < 0:
        return 0.0, ["ডেডলাইন পেরিয়ে গেছে"]
    if days_left >= full_days:
        reasons.append(f"ডেডলাইনে {days_left} দিন বাকি")
        return 100.0, reasons
    score = _clamp(100.0 * days_left / full_days)
    reasons.append(f"ডেডলাইন কাছে ({days_left} দিন বাকি)")
    return score, reasons


def band_for_score(score: float, weights: MatchWeights) -> str:
    if score >= weights.safe_threshold:
        return "Safe"
    if score >= weights.target_threshold:
        return "Target"
    return "Reach"


def score_program(
    student: StudentMatchInput,
    program: ProgramMatchInput,
    *,
    weights: MatchWeights,
    today: date,
) -> MatchResult | None:
    skip = hard_filter(student, program, today=today)
    if skip is not None:
        return None

    reasons: list[str] = []
    cgpa_s, cgpa_r = score_cgpa(
        student.cgpa, program.min_cgpa, full_margin=weights.cgpa_full_margin
    )
    reasons.extend(cgpa_r)

    ielts_s, ielts_r = score_ielts(student.ielts, program.min_ielts)
    reasons.extend(ielts_r)

    budget_s, year_cost, budget_r = score_budget(
        student.budget_eur, program.tuition_eur, program.monthly_living_cost
    )
    reasons.extend(budget_r)

    deadline_s, deadline_r = score_deadline(
        program.intake_deadline,
        today=today,
        full_days=weights.deadline_full_days,
    )
    reasons.extend(deadline_r)

    # Renormalize weights when IELTS component is skipped.
    w_cgpa, w_ielts, w_budget, w_deadline = (
        weights.cgpa,
        weights.ielts,
        weights.budget,
        weights.deadline,
    )
    if ielts_s is None:
        remaining = w_cgpa + w_budget + w_deadline
        if remaining <= 0:
            remaining = 1.0
        w_cgpa, w_budget, w_deadline = (
            w_cgpa / remaining,
            w_budget / remaining,
            w_deadline / remaining,
        )
        w_ielts = 0.0
        ielts_component = 0.0
    else:
        ielts_component = ielts_s

    total = (
        cgpa_s * w_cgpa
        + ielts_component * w_ielts
        + budget_s * w_budget
        + deadline_s * w_deadline
    )
    total = round(_clamp(total), 1)
    return MatchResult(
        program_id=program.id,
        program_name=program.name,
        university_name=program.university_name,
        city_name=program.city_name,
        country_code=program.country_code,
        degree=program.degree,
        language=program.language,
        tuition_eur=program.tuition_eur,
        intake_deadline=program.intake_deadline,
        scholarship=program.scholarship,
        score=total,
        band=band_for_score(total, weights),
        reasons=reasons,
        estimated_year_cost_eur=year_cost,
    )


def match_programs(
    student: StudentMatchInput,
    programs: list[ProgramMatchInput],
    *,
    weights: MatchWeights | None = None,
    today: date | None = None,
) -> dict[str, list[MatchResult]]:
    weights = weights or MatchWeights()
    today = today or date.today()
    scored: list[MatchResult] = []
    for program in programs:
        result = score_program(student, program, weights=weights, today=today)
        if result is not None:
            scored.append(result)
    scored.sort(key=lambda r: (-r.score, r.program_name))
    return {
        "Safe": [r for r in scored if r.band == "Safe"],
        "Target": [r for r in scored if r.band == "Target"],
        "Reach": [r for r in scored if r.band == "Reach"],
    }
