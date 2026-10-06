"""Insert a realistic demo dataset for showcasing the platform.

Run from the `backend` folder after installing requirements:

    python -m scripts.seed_demo

Creates idempotently:
    * admin@campus.edu         / Admin@12345
    * mentor@campus.edu        / Mentor@12345
    * mentor2@campus.edu       / Mentor@12345
    * albin@vitstudent.ac.in   / Student@12345   (full profile, resume, applications)
    * priya@vitstudent.ac.in   / Student@12345   (thinner profile for gap analysis)
    * two companies, two job postings, two open drives and one pending application
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Account,
    Administrator,
    Application,
    ApplicationStatus,
    Certification,
    Company,
    DriveStatus,
    JobPosting,
    JobPostingStatus,
    Mentor,
    MentorAssignment,
    PlacementDrive,
    ProficiencyLevel,
    Project,
    Resume,
    ResumeStatus,
    Skill,
    Student,
    UserRole,
)
from app.security import hash_password  # noqa: E402
from app.services.seed import seed_reference_data  # noqa: E402


def get_or_create_account(
    db, *, email: str, full_name: str, role: UserRole, password: str
) -> Account:
    account = db.query(Account).filter(Account.email == email).one_or_none()
    if account is not None:
        return account
    account = Account(full_name=full_name, email=email, role=role, password_hash=hash_password(password))
    db.add(account)
    db.flush()
    return account


def seed_people(db) -> dict:
    admin = get_or_create_account(
        db,
        email="admin@campus.edu",
        full_name="Placement Cell Admin",
        role=UserRole.administrator,
        password="Admin@12345",
    )
    if admin.administrator is None:
        db.add(Administrator(account_id=admin.id, staff_code="ADM001", office="Placement Cell"))

    mentor = get_or_create_account(
        db,
        email="mentor@campus.edu",
        full_name="Dr. Meera Krishnan",
        role=UserRole.mentor,
        password="Mentor@12345",
    )
    if mentor.mentor is None:
        db.add(Mentor(account_id=mentor.id, employee_code="EMP001", department="CSE"))

    mentor2 = get_or_create_account(
        db,
        email="mentor2@campus.edu",
        full_name="Prof. Arun Das",
        role=UserRole.mentor,
        password="Mentor@12345",
    )
    if mentor2.mentor is None:
        db.add(Mentor(account_id=mentor2.id, employee_code="EMP002", department="IT"))
    db.flush()

    albin = get_or_create_account(
        db,
        email="albin@vitstudent.ac.in",
        full_name="Albin Thomas Jiji",
        role=UserRole.student,
        password="Student@12345",
    )
    priya = get_or_create_account(
        db,
        email="priya@vitstudent.ac.in",
        full_name="Priya Nair",
        role=UserRole.student,
        password="Student@12345",
    )
    db.flush()

    return {
        "admin": admin,
        "mentor": mentor,
        "mentor2": mentor2,
        "albin": albin,
        "priya": priya,
    }


def seed_student_profiles(db, people: dict) -> None:
    albin = people["albin"]
    priya = people["priya"]

    if albin.student is None:
        student = Student(
            account_id=albin.id,
            registration_number="24BCE1141",
            program="B.Tech Computer Science and Engineering",
            degree="B.Tech",
            department="CSE",
            graduation_year=2027,
            cgpa=8.7,
            phone="9876543210",
            location="Vellore",
            bio="Final-year CSE student focused on full-stack and applied AI projects.",
            target_role="Full-Stack Developer",
            target_roles=["Full-Stack Developer", "Backend Developer"],
            career_interests=["Web development", "Applied AI"],
            preferred_locations=["Bengaluru", "Chennai"],
            github_url="https://github.com/Albin5jiji",
            linkedin_url="https://www.linkedin.com/in/example",
            portfolio_url="https://portfolio.example.com/albin",
        )
        db.add(student)
        db.flush()
        for name, level in [
            ("React", ProficiencyLevel.advanced),
            ("JavaScript", ProficiencyLevel.advanced),
            ("Python", ProficiencyLevel.intermediate),
            ("FastAPI", ProficiencyLevel.intermediate),
            ("PostgreSQL", ProficiencyLevel.intermediate),
            ("HTML/CSS", ProficiencyLevel.intermediate),
        ]:
            db.add(Skill(student_id=student.id, name=name, proficiency=level))
        db.add(
            Project(
                student_id=student.id,
                title="AI Career Intelligence Platform",
                description="FastAPI + React platform that scores placement readiness and tracks applications.",
                tech_stack=["React", "TypeScript", "FastAPI", "PostgreSQL"],
                repo_url="https://github.com/Albin5jiji/AI-Carrer-Platform",
            )
        )
        db.add(
            Project(
                student_id=student.id,
                title="Resume Analyzer",
                description="Parses resumes and highlights missing keywords for a target role.",
                tech_stack=["Python", "FastAPI"],
                repo_url="https://github.com/Albin5jiji/resume-analyzer",
            )
        )
        db.add(
            Certification(
                student_id=student.id,
                name="Front End Development Libraries",
                issuer="freeCodeCamp",
                issued_year=2025,
                skill_tags=["React", "JavaScript"],
            )
        )
        db.add(
            Resume(
                student_id=student.id,
                version_number=1,
                version_name="Resume v1",
                title="Full-Stack Developer Resume",
                target_role="Full-Stack Developer",
                summary="CSE student with two production style web projects and internship exposure.",
                content={
                    "education": ["B.Tech CSE, VIT, 2023-2027, CGPA 8.7"],
                    "skills": ["React", "TypeScript", "FastAPI", "PostgreSQL"],
                    "projects": ["AI Career Intelligence Platform", "Resume Analyzer"],
                    "experience": ["Web development intern, 3 months"],
                    "achievements": ["Smart India Hackathon finalist"],
                    "links": ["https://github.com/Albin5jiji"],
                },
                status=ResumeStatus.approved,
            )
        )

    if priya.student is None:
        student2 = Student(
            account_id=priya.id,
            registration_number="24BCE1207",
            program="B.Tech Information Technology",
            degree="B.Tech",
            department="IT",
            graduation_year=2027,
            cgpa=7.4,
            target_role="Data Analyst",
            target_roles=["Data Analyst"],
        )
        db.add(student2)
        db.flush()
        for name, level in [("SQL", ProficiencyLevel.intermediate), ("Excel", ProficiencyLevel.beginner)]:
            db.add(Skill(student_id=student2.id, name=name, proficiency=level))

    db.flush()

    pairs = [
        (people["mentor"].mentor, albin.student),
        (people["mentor2"].mentor, priya.student),
    ]
    for mentor_profile, student_profile in pairs:
        if mentor_profile is None or student_profile is None:
            continue
        exists = (
            db.query(MentorAssignment)
            .filter(
                MentorAssignment.mentor_id == mentor_profile.id,
                MentorAssignment.student_id == student_profile.id,
            )
            .count()
        )
        if not exists:
            db.add(MentorAssignment(mentor_id=mentor_profile.id, student_id=student_profile.id))


def seed_placement(db, people: dict) -> None:
    admin = people["admin"]

    company = db.query(Company).filter(Company.name == "Northwind Technologies").one_or_none()
    if company is None:
        company = Company(
            name="Northwind Technologies",
            industry="Software Product",
            website="https://example.com/northwind",
            location="Bengaluru",
            contact_person="Talent Acquisition",
            contact_email="careers@example.com",
            description="Product company hiring full-stack and back-end engineers.",
        )
        db.add(company)

    analytics = db.query(Company).filter(Company.name == "Datawave Analytics").one_or_none()
    if analytics is None:
        analytics = Company(
            name="Datawave Analytics",
            industry="Analytics",
            website="https://example.com/datawave",
            location="Chennai",
            description="Analytics consultancy hiring data analysts.",
        )
        db.add(analytics)
    db.flush()

    job = db.query(JobPosting).filter(JobPosting.title == "Graduate Full-Stack Engineer").one_or_none()
    if job is None:
        job = JobPosting(
            company_id=company.id,
            title="Graduate Full-Stack Engineer",
            description="Build and ship features across React and FastAPI services.",
            required_skills=["React", "JavaScript", "FastAPI", "PostgreSQL"],
            min_cgpa=7.5,
            eligible_departments=["CSE", "IT"],
            graduation_years=[2026, 2027],
            job_type="full_time",
            location="Bengaluru",
            salary_range="8-12 LPA",
            application_deadline=date.today() + timedelta(days=21),
            status=JobPostingStatus.published,
            created_by_account_id=admin.id,
        )
        db.add(job)

    analyst_job = db.query(JobPosting).filter(JobPosting.title == "Junior Data Analyst").one_or_none()
    if analyst_job is None:
        analyst_job = JobPosting(
            company_id=analytics.id,
            title="Junior Data Analyst",
            description="Own reporting, dashboards and ad hoc analysis for client teams.",
            required_skills=["SQL", "Power BI", "Excel", "Statistics"],
            min_cgpa=7.0,
            eligible_departments=["CSE", "IT", "ECE"],
            graduation_years=[2026, 2027],
            job_type="full_time",
            location="Chennai",
            salary_range="5-7 LPA",
            application_deadline=date.today() + timedelta(days=10),
            status=JobPostingStatus.published,
            created_by_account_id=admin.id,
        )
        db.add(analyst_job)
    db.flush()

    drive = db.query(PlacementDrive).filter(PlacementDrive.name == "Northwind Campus Drive 2026").one_or_none()
    if drive is None:
        drive = PlacementDrive(
            company_id=company.id,
            job_posting_id=job.id,
            name="Northwind Campus Drive 2026",
            description="Two technical rounds followed by an HR discussion.",
            drive_date=date.today() + timedelta(days=28),
            application_deadline=date.today() + timedelta(days=21),
            min_cgpa=7.5,
            eligible_departments=["CSE", "IT"],
            graduation_years=[2026, 2027],
            required_skills=["React", "JavaScript", "FastAPI"],
            location="Bengaluru",
            requires_mentor_approval=True,
            status=DriveStatus.open,
            created_by_account_id=admin.id,
        )
        db.add(drive)

    analyst_drive = (
        db.query(PlacementDrive).filter(PlacementDrive.name == "Datawave Analyst Drive 2026").one_or_none()
    )
    if analyst_drive is None:
        analyst_drive = PlacementDrive(
            company_id=analytics.id,
            job_posting_id=analyst_job.id,
            name="Datawave Analyst Drive 2026",
            drive_date=date.today() + timedelta(days=18),
            application_deadline=date.today() + timedelta(days=10),
            min_cgpa=7.0,
            eligible_departments=["CSE", "IT", "ECE"],
            graduation_years=[2026, 2027],
            required_skills=["SQL", "Power BI"],
            location="Chennai",
            requires_mentor_approval=True,
            status=DriveStatus.open,
            created_by_account_id=admin.id,
        )
        db.add(analyst_drive)
    db.flush()

    priya_student = people["priya"].student
    mentor2 = people["mentor2"].mentor
    if priya_student is None or mentor2 is None:
        return

    already = (
        db.query(Application)
        .filter(Application.student_id == priya_student.id, Application.drive_id == analyst_drive.id)
        .count()
    )
    if not already:
        db.add(
            Application(
                code=f"APP-{analyst_drive.id:04d}-{priya_student.id:05d}",
                student_id=priya_student.id,
                drive_id=analyst_drive.id,
                company_id=analytics.id,
                job_posting_id=analyst_job.id,
                eligibility_status="eligible",
                status=ApplicationStatus.pending_mentor_approval,
                mentor_id=mentor2.id,
                note_to_mentor="Please review my dashboard project before approving.",
            )
        )


def main() -> None:
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_reference_data(db)
        people = seed_people(db)
        seed_student_profiles(db, people)
        seed_placement(db, people)
        db.commit()

        print("Demo dataset ready.")
        print("  admin@campus.edu        / Admin@12345")
        print("  mentor@campus.edu       / Mentor@12345")
        print("  mentor2@campus.edu      / Mentor@12345")
        print("  albin@vitstudent.ac.in  / Student@12345")
        print("  priya@vitstudent.ac.in  / Student@12345")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()



