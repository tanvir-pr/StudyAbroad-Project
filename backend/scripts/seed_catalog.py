"""Seed catalog: 3 countries, 7 cities, 15 universities, ~48 programs, templates.

Usage (from backend/):
    uv run python scripts/seed_catalog.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Allow `python scripts/seed_catalog.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.db import AsyncSessionLocal
from app.modules.catalog.models import (
    City,
    Country,
    DocumentTemplate,
    Program,
    ProgramCourse,
    University,
)

COUNTRIES = [
    {
        "code": "HU",
        "name": "Hungary",
        "work_hours_limit": 30,
        "work_hours_limit_holiday": 40,
        "limit_period": "week",
        "post_study_visa_months": 9,
        "required_funds_eur": Decimal("8500"),
        "avg_living_cost": Decimal("650"),
    },
    {
        "code": "DE",
        "name": "Germany",
        "work_hours_limit": 20,
        "work_hours_limit_holiday": 40,
        "limit_period": "week",
        "post_study_visa_months": 18,
        "required_funds_eur": Decimal("11904"),
        "avg_living_cost": Decimal("950"),
    },
    {
        "code": "IT",
        "name": "Italy",
        "work_hours_limit": 20,
        "work_hours_limit_holiday": 40,
        "limit_period": "week",
        "post_study_visa_months": 12,
        "required_funds_eur": Decimal("7200"),
        "avg_living_cost": Decimal("800"),
    },
]

CITIES = [
    ("HU", "Budapest", "450", "180", "40"),
    ("HU", "Debrecen", "320", "150", "30"),
    ("DE", "Berlin", "900", "250", "80"),
    ("DE", "Munich", "1100", "280", "70"),
    ("DE", "Aachen", "650", "220", "55"),
    ("IT", "Milan", "850", "240", "60"),
    ("IT", "Rome", "780", "230", "55"),
]

UNIVERSITIES = [
    ("Budapest", "Eötvös Loránd University", "https://www.elte.hu", "admission@elte.hu"),
    ("Budapest", "Budapest University of Technology and Economics", "https://www.bme.hu", "admission@bme.hu"),
    ("Budapest", "Corvinus University of Budapest", "https://www.uni-corvinus.hu", "admission@uni-corvinus.hu"),
    ("Debrecen", "University of Debrecen", "https://www.edu.unideb.hu", "admission@edu.unideb.hu"),
    ("Debrecen", "Debrecen Reformed Theological University", "https://drhe.hu", "info@drhe.hu"),
    ("Berlin", "Technical University of Berlin", "https://www.tu.berlin", "admission@tu.berlin"),
    ("Berlin", "Humboldt University of Berlin", "https://www.hu-berlin.de", "admission@hu-berlin.de"),
    ("Berlin", "Free University of Berlin", "https://www.fu-berlin.de", "admission@fu-berlin.de"),
    ("Munich", "Technical University of Munich", "https://www.tum.de", "studium@tum.de"),
    ("Munich", "Ludwig Maximilian University of Munich", "https://www.lmu.de", "international@lmu.de"),
    ("Aachen", "RWTH Aachen University", "https://www.rwth-aachen.de", "international@rwth-aachen.de"),
    ("Milan", "Politecnico di Milano", "https://www.polimi.it", "international@polimi.it"),
    ("Milan", "University of Milan", "https://www.unimi.it", "international@unimi.it"),
    ("Rome", "Sapienza University of Rome", "https://www.uniroma1.it", "international@uniroma1.it"),
    ("Rome", "Roma Tre University", "https://www.uniroma3.it", "international@uniroma3.it"),
]

# (university_name, program_name, degree, language, tuition, cgpa, ielts, deadline, scholarship)
PROGRAM_SPECS = [
    ("Eötvös Loránd University", "Computer Science MSc", "Master", "English", "3200", "3.00", "6.5", "2027-06-30", True),
    ("Eötvös Loránd University", "Data Science MSc", "Master", "English", "3400", "3.00", "6.5", "2027-06-30", True),
    ("Eötvös Loránd University", "Biology BSc", "Bachelor", "English", "2800", "2.80", "6.0", "2027-05-15", False),
    ("Budapest University of Technology and Economics", "Computer Engineering BSc", "Bachelor", "English", "3200", "2.80", "6.0", "2027-05-31", False),
    ("Budapest University of Technology and Economics", "Electrical Engineering MSc", "Master", "English", "3500", "3.00", "6.5", "2027-06-15", True),
    ("Budapest University of Technology and Economics", "Architecture MSc", "Master", "English", "3800", "3.00", "6.5", "2027-06-15", False),
    ("Corvinus University of Budapest", "International Business MSc", "Master", "English", "3600", "3.00", "6.5", "2027-07-01", True),
    ("Corvinus University of Budapest", "Finance BSc", "Bachelor", "English", "3000", "2.80", "6.0", "2027-05-20", False),
    ("University of Debrecen", "Computer Science Engineering BSc", "Bachelor", "English", "6500", "2.70", "5.5", "2027-06-15", False),
    ("University of Debrecen", "Public Health MSc", "Master", "English", "7000", "2.90", "6.0", "2027-06-15", True),
    ("University of Debrecen", "Business Administration BSc", "Bachelor", "English", "6000", "2.70", "5.5", "2027-06-01", False),
    ("University of Debrecen", "Mechanical Engineering MSc", "Master", "English", "7200", "3.00", "6.0", "2027-06-15", False),
    ("Debrecen Reformed Theological University", "Theology BA", "Bachelor", "English", "2500", "2.50", "5.5", "2027-08-01", False),
    ("Technical University of Berlin", "Computer Science MSc", "Master", "English", "0", "3.00", "6.5", "2027-03-15", True),
    ("Technical University of Berlin", "Industrial Engineering BSc", "Bachelor", "German", "0", "2.80", "0.0", "2027-07-15", False),
    ("Technical University of Berlin", "ICT Innovation MSc", "Master", "English", "0", "3.00", "6.5", "2027-03-01", True),
    ("Humboldt University of Berlin", "Economics MSc", "Master", "English", "0", "3.00", "6.5", "2027-04-30", True),
    ("Humboldt University of Berlin", "Social Sciences BA", "Bachelor", "German", "0", "2.70", "0.0", "2027-07-15", False),
    ("Free University of Berlin", "Bioinformatics MSc", "Master", "English", "0", "3.00", "6.5", "2027-04-15", True),
    ("Free University of Berlin", "North American Studies MA", "Master", "English", "0", "2.90", "6.5", "2027-05-01", False),
    ("Technical University of Munich", "Informatics MSc", "Master", "English", "0", "3.20", "6.5", "2027-05-31", True),
    ("Technical University of Munich", "Robotics MSc", "Master", "English", "0", "3.20", "6.5", "2027-05-31", True),
    ("Technical University of Munich", "Management BSc", "Bachelor", "English", "0", "3.00", "6.5", "2027-07-15", False),
    ("Ludwig Maximilian University of Munich", "Data Science MSc", "Master", "English", "0", "3.00", "6.5", "2027-06-01", True),
    ("Ludwig Maximilian University of Munich", "Physics BSc", "Bachelor", "German", "0", "2.80", "0.0", "2027-07-15", False),
    ("RWTH Aachen University", "Computer Science MSc", "Master", "English", "0", "3.00", "6.5", "2027-03-01", True),
    ("RWTH Aachen University", "Automotive Engineering MSc", "Master", "English", "0", "3.00", "6.5", "2027-03-01", True),
    ("RWTH Aachen University", "Mechanical Engineering BSc", "Bachelor", "German", "0", "2.80", "0.0", "2027-07-15", False),
    ("Politecnico di Milano", "Computer Science and Engineering MSc", "Master", "English", "3900", "3.00", "6.0", "2027-05-02", True),
    ("Politecnico di Milano", "Management Engineering MSc", "Master", "English", "3900", "3.00", "6.0", "2027-05-02", True),
    ("Politecnico di Milano", "Architectural Design BSc", "Bachelor", "English", "3700", "2.80", "6.0", "2027-07-01", False),
    ("Politecnico di Milano", "Cybersecurity MSc", "Master", "English", "3900", "3.00", "6.5", "2027-05-02", True),
    ("University of Milan", "Biotechnology MSc", "Master", "English", "3500", "2.90", "6.0", "2027-06-30", False),
    ("University of Milan", "International Relations BA", "Bachelor", "English", "3200", "2.70", "6.0", "2027-07-15", False),
    ("University of Milan", "Medical Biotechnology MSc", "Master", "English", "3800", "3.00", "6.5", "2027-06-30", True),
    ("Sapienza University of Rome", "Artificial Intelligence and Robotics MSc", "Master", "English", "2900", "3.00", "6.5", "2027-04-29", True),
    ("Sapienza University of Rome", "Economics BA", "Bachelor", "English", "2700", "2.70", "6.0", "2027-07-15", False),
    ("Sapienza University of Rome", "Data Science MSc", "Master", "English", "3000", "3.00", "6.5", "2027-04-29", True),
    ("Sapienza University of Rome", "Engineering Sciences BSc", "Bachelor", "English", "2800", "2.80", "6.0", "2027-07-01", False),
    ("Roma Tre University", "International Studies MA", "Master", "English", "2500", "2.80", "6.0", "2027-06-15", False),
    ("Roma Tre University", "Computer Science BSc", "Bachelor", "Italian", "2400", "2.70", "0.0", "2027-08-01", False),
    ("Roma Tre University", "Business Management MSc", "Master", "English", "2600", "2.90", "6.0", "2027-06-15", True),
    ("Corvinus University of Budapest", "Marketing MSc", "Master", "English", "3500", "3.00", "6.5", "2027-07-01", False),
    ("Free University of Berlin", "Public Economics MSc", "Master", "English", "0", "3.00", "6.5", "2027-04-15", False),
    ("Humboldt University of Berlin", "Information Systems MSc", "Master", "English", "0", "3.00", "6.5", "2027-04-30", True),
    ("Technical University of Munich", "Sustainable Management MSc", "Master", "English", "0", "3.00", "6.5", "2027-05-31", False),
    ("Eötvös Loránd University", "Psychology BA", "Bachelor", "English", "3000", "2.80", "6.0", "2027-05-15", False),
    ("University of Debrecen", "Nursing BSc", "Bachelor", "English", "6500", "2.70", "5.5", "2027-06-01", False),
]

DEFAULT_COURSES = [
    ("Core Foundations", 1, "6.0"),
    ("Research Methods", 1, "5.0"),
    ("Advanced Topics", 2, "6.0"),
    ("Capstone Project", 2, "10.0"),
]

DOC_TEMPLATES = [
    ("Master", "Passport", True, 7, False),
    ("Master", "Bachelor Degree Certificate", True, 21, True),
    ("Master", "Academic Transcript", True, 21, True),
    ("Master", "Motivation Letter / SOP", True, 14, False),
    ("Master", "CV / Resume", True, 7, False),
    ("Master", "IELTS / Language Certificate", True, 14, False),
    ("Master", "Recommendation Letter", False, 14, False),
    ("Bachelor", "Passport", True, 7, False),
    ("Bachelor", "Higher Secondary Certificate", True, 21, True),
    ("Bachelor", "Academic Transcript", True, 21, True),
    ("Bachelor", "Motivation Letter / SOP", True, 14, False),
    ("Bachelor", "CV / Resume", True, 7, False),
    ("Bachelor", "IELTS / Language Certificate", True, 14, False),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Country))
        if existing and existing > 0:
            print(f"Catalog already seeded ({existing} countries). Skipping.")
            return

        countries: dict[str, Country] = {}
        for row in COUNTRIES:
            c = Country(**row)
            session.add(c)
            countries[row["code"]] = c
        await session.flush()

        cities: dict[str, City] = {}
        for code, name, rent, food, transport in CITIES:
            city = City(
                country_id=countries[code].id,
                name=name,
                rent_avg=Decimal(rent),
                food_avg=Decimal(food),
                transport_avg=Decimal(transport),
            )
            session.add(city)
            cities[name] = city
        await session.flush()

        universities: dict[str, University] = {}
        for city_name, name, website, email in UNIVERSITIES:
            uni = University(
                city_id=cities[city_name].id,
                name=name,
                website=website,
                admission_email=email,
            )
            session.add(uni)
            universities[name] = uni
        await session.flush()

        for spec in PROGRAM_SPECS:
            (
                uni_name,
                pname,
                degree,
                language,
                tuition,
                cgpa,
                ielts,
                deadline,
                scholarship,
            ) = spec
            program = Program(
                university_id=universities[uni_name].id,
                name=pname,
                degree=degree,
                language=language,
                tuition_eur=Decimal(tuition),
                min_cgpa=Decimal(cgpa),
                min_ielts=Decimal(ielts),
                intake_deadline=date.fromisoformat(deadline),
                scholarship=scholarship,
                courses=[
                    ProgramCourse(
                        name=cname,
                        semester=sem,
                        credits=Decimal(credits),
                    )
                    for cname, sem, credits in DEFAULT_COURSES
                ],
            )
            session.add(program)
        await session.flush()

        for code, country in countries.items():
            for degree, name, required, lead, attest in DOC_TEMPLATES:
                session.add(
                    DocumentTemplate(
                        country_id=country.id,
                        degree=degree,
                        name=name,
                        is_required=required,
                        lead_days=lead,
                        needs_attestation=attest,
                    )
                )

        await session.commit()
        print(
            f"Seeded {len(countries)} countries, {len(cities)} cities, "
            f"{len(universities)} universities, {len(PROGRAM_SPECS)} programs, "
            f"{len(countries) * len(DOC_TEMPLATES)} document templates."
        )


if __name__ == "__main__":
    asyncio.run(seed())
