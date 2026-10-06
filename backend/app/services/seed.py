"""Idempotent seeding of the reference dataset.

`seed_reference_data` only inserts what is missing, so it is safe to run on every
startup. `seed_demo_accounts` is opt-in through the `SEED_DEMO_ACCOUNTS` environment
variable and creates a ready-to-demo student, mentor, administrator and company set.
"""

from sqlalchemy.orm import Session

from ..models import (
    Difficulty,
    InterviewCategory,
    InterviewQuestion,
    LearningResource,
    Priority,
    ProficiencyLevel,
    RoleProfile,
    RoleSkill,
)
from .seed_data import INTERVIEW_QUESTIONS, LEARNING_RESOURCES, ROLE_CATALOG


def seed_reference_data(db: Session) -> dict[str, int]:
    """Insert missing role profiles, role skills, learning resources and questions."""

    created = {"roles": 0, "role_skills": 0, "resources": 0, "questions": 0}

    existing_roles = {role.name: role for role in db.query(RoleProfile).all()}
    for role_name, payload in ROLE_CATALOG.items():
        role = existing_roles.get(role_name)
        if role is None:
            role = RoleProfile(
                name=role_name,
                category=payload["category"],
                description=payload["description"],
            )
            db.add(role)
            db.flush()
            existing_roles[role_name] = role
            created["roles"] += 1

        existing_skills = {
            row.skill_name for row in db.query(RoleSkill).filter(RoleSkill.role_profile_id == role.id).all()
        }
        for order, (skill_name, priority, level) in enumerate(payload["skills"]):
            if skill_name in existing_skills:
                continue
            db.add(
                RoleSkill(
                    role_profile_id=role.id,
                    role_name=role.name,
                    skill_name=skill_name,
                    priority=Priority(priority),
                    target_proficiency=ProficiencyLevel(level),
                    display_order=order,
                )
            )
            created["role_skills"] += 1

    existing_resources = {
        (row.skill_name, row.title) for row in db.query(LearningResource).all()
    }
    for skill_name, title, provider, url, resource_type, difficulty, hours in LEARNING_RESOURCES:
        if (skill_name, title) in existing_resources:
            continue
        db.add(
            LearningResource(
                skill_name=skill_name,
                title=title,
                provider=provider,
                url=url,
                resource_type=resource_type,
                difficulty=Difficulty(difficulty),
                estimated_hours=hours,
                description=f"Recommended material for {skill_name}.",
            )
        )
        created["resources"] += 1

    existing_questions = {row.question for row in db.query(InterviewQuestion).all()}
    for category, target_role, difficulty, question, guidance, tags in INTERVIEW_QUESTIONS:
        if question in existing_questions:
            continue
        db.add(
            InterviewQuestion(
                category=InterviewCategory(category),
                target_role=target_role,
                difficulty=Difficulty(difficulty),
                question=question,
                guidance=guidance,
                skill_tags=tags,
            )
        )
        created["questions"] += 1

    db.commit()
    return created
