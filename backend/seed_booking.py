"""Seed Dundalk-specific booking configuration.

The generic template creates the database tables, but a no-website onboarding
site needs concrete appointment types and clinic hours before public booking can
show availability. This seed is intentionally idempotent: it only fills missing
booking rows and does not overwrite admin-edited values once they exist.
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from database import AsyncSessionLocal
from models import AppointmentType, ClinicHours, StaffConfig

logger = logging.getLogger(__name__)

# 0 = Monday ... 6 = Sunday. Minutes are local America/New_York wall time.
DUNDALK_HOURS = [
    (0, True, 8 * 60, 19 * 60 + 30),
    (1, True, 8 * 60, 18 * 60),
    (2, True, 8 * 60, 19 * 60 + 30),
    (3, True, 8 * 60, 19 * 60 + 30),
    (4, True, 8 * 60, 19 * 60 + 30),
    (5, True, 8 * 60, 15 * 60),
    (6, True, 8 * 60, 12 * 60 + 30),
]

DUNDALK_APPOINTMENT_TYPES = [
    {
        "name": "Wellness Visit",
        "description": "Routine exam, vaccines, parasite prevention, and preventive care planning.",
        "duration_mins": 30,
        "doctor_mins": 30,
        "tech_mins": 30,
        "color": "#109090",
        "sort_order": 10,
    },
    {
        "name": "Sick Pet Visit",
        "description": "Visit for illness, injury, discomfort, appetite changes, vomiting, diarrhea, limping, or similar concerns.",
        "duration_mins": 45,
        "doctor_mins": 35,
        "tech_mins": 45,
        "color": "#1A2B4C",
        "sort_order": 20,
    },
    {
        "name": "Dental Consultation",
        "description": "Dental exam, oral health discussion, and treatment planning.",
        "duration_mins": 30,
        "doctor_mins": 30,
        "tech_mins": 30,
        "color": "#DDEFEF",
        "sort_order": 30,
    },
    {
        "name": "Surgery Consultation",
        "description": "Consultation for surgical questions, estimates, and care planning.",
        "duration_mins": 45,
        "doctor_mins": 35,
        "tech_mins": 45,
        "color": "#EFE5CA",
        "sort_order": 40,
    },
    {
        "name": "Tech Appointment",
        "description": "Technician visit for services that do not require a full doctor exam.",
        "duration_mins": 20,
        "doctor_mins": 0,
        "tech_mins": 20,
        "color": "#576370",
        "sort_order": 50,
    },
]


async def seed_booking() -> None:
    async with AsyncSessionLocal() as db:
        staff_res = await db.execute(select(StaffConfig).limit(1))
        staff = staff_res.scalar_one_or_none()
        if not staff:
            db.add(StaffConfig(num_doctors=1, num_techs=2, slot_granularity_mins=30, booking_window_days=14, min_lead_time_hours=2))
            logger.info("Seeded Dundalk booking staff config")

        for day_of_week, is_open, open_minutes, close_minutes in DUNDALK_HOURS:
            res = await db.execute(select(ClinicHours).where(ClinicHours.day_of_week == day_of_week))
            existing = res.scalar_one_or_none()
            if existing:
                continue
            db.add(
                ClinicHours(
                    day_of_week=day_of_week,
                    is_open=is_open,
                    open_minutes=open_minutes,
                    close_minutes=close_minutes,
                )
            )
            logger.info("Seeded Dundalk booking hours for weekday %s", day_of_week)

        type_count_res = await db.execute(select(AppointmentType).limit(1))
        has_type = type_count_res.scalar_one_or_none() is not None
        if not has_type:
            for spec in DUNDALK_APPOINTMENT_TYPES:
                db.add(AppointmentType(**spec))
            logger.info("Seeded Dundalk appointment types")

        await db.commit()
