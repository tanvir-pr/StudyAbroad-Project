from datetime import date
from decimal import Decimal

from app.modules.match.engine import (
    MatchWeights,
    ProgramMatchInput,
    StudentMatchInput,
    band_for_score,
    hard_filter,
    match_programs,
    score_cgpa,
    score_deadline,
    score_ielts,
    score_program,
)


TODAY = date(2026, 3, 1)
WEIGHTS = MatchWeights()


def _program(**overrides) -> ProgramMatchInput:
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        name="Computer Science MSc",
        degree="Master",
        language="English",
        tuition_eur=Decimal("0"),
        min_cgpa=Decimal("3.00"),
        min_ielts=Decimal("6.5"),
        intake_deadline=date(2026, 5, 31),
        scholarship=True,
        university_name="TUM",
        city_name="Munich",
        country_code="DE",
        monthly_living_cost=Decimal("1450"),
    )
    base.update(overrides)
    return ProgramMatchInput(**base)


def _student(**overrides) -> StudentMatchInput:
    base = dict(
        cgpa=Decimal("3.20"),
        ielts=Decimal("6.5"),
        budget_eur=Decimal("20000"),
        target_degree="Master",
    )
    base.update(overrides)
    return StudentMatchInput(**base)


def test_hard_filter_degree_mismatch():
    assert (
        hard_filter(
            _student(target_degree="Bachelor"), _program(), today=TODAY
        )
        == "degree_mismatch"
    )


def test_hard_filter_deadline_passed():
    assert (
        hard_filter(
            _student(),
            _program(intake_deadline=date(2026, 2, 1)),
            today=TODAY,
        )
        == "deadline_passed"
    )


def test_hard_filter_ielts_required():
    assert (
        hard_filter(_student(ielts=None), _program(), today=TODAY)
        == "ielts_required"
    )


def test_cgpa_below_min_has_reason():
    score, reasons = score_cgpa(
        Decimal("2.50"), Decimal("3.00"), full_margin=0.5
    )
    assert score < 50
    assert any("কম" in r for r in reasons)


def test_cgpa_strong_margin_near_100():
    score, _ = score_cgpa(Decimal("3.60"), Decimal("3.00"), full_margin=0.5)
    assert score == 100.0


def test_ielts_shortfall_reason():
    score, reasons = score_ielts(Decimal("6.0"), Decimal("6.5"))
    assert score is not None and score < 50
    assert any("IELTS 0.5 কম" in r for r in reasons)


def test_ielts_skipped_when_not_required():
    score, reasons = score_ielts(None, Decimal("0.0"))
    assert score is None
    assert reasons == []


def test_deadline_near_reduces_score():
    score, reasons = score_deadline(
        date(2026, 3, 15), today=TODAY, full_days=30
    )
    assert score < 100
    assert any("কাছে" in r for r in reasons)


def test_bands():
    assert band_for_score(80, WEIGHTS) == "Safe"
    assert band_for_score(60, WEIGHTS) == "Target"
    assert band_for_score(40, WEIGHTS) == "Reach"


def test_strong_profile_lands_safe():
    result = score_program(
        _student(cgpa=Decimal("3.50"), ielts=Decimal("7.0"), budget_eur=Decimal("25000")),
        _program(),
        weights=WEIGHTS,
        today=TODAY,
    )
    assert result is not None
    assert result.band == "Safe"
    assert result.score >= 75


def test_match_programs_groups_and_sorts():
    student = _student(cgpa=Decimal("3.40"), ielts=Decimal("7.0"), budget_eur=Decimal("30000"))
    programs = [
        _program(id="a", name="A Program", tuition_eur=Decimal("0")),
        _program(
            id="b",
            name="B Program",
            min_cgpa=Decimal("3.30"),
            tuition_eur=Decimal("5000"),
            monthly_living_cost=Decimal("900"),
        ),
        _program(
            id="c",
            name="Skipped Bachelor",
            degree="Bachelor",
        ),
    ]
    grouped = match_programs(student, programs, weights=WEIGHTS, today=TODAY)
    matched_ids = {
        r.program_id
        for band in grouped.values()
        for r in band
    }
    assert "c" not in matched_ids
    assert "a" in matched_ids
    # Highest score first within combined ordering used by match_programs
    all_sorted = grouped["Safe"] + grouped["Target"] + grouped["Reach"]
    scores = [r.score for r in all_sorted]
    assert scores == sorted(scores, reverse=True)
