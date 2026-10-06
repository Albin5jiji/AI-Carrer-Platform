"""Student profile, skills, projects and certifications."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account, get_current_student, require_mentor_or_admin
from ..models import Account, Certification, Mentor, Project, RoleProfile, Skill, Student, UserRole
from ..schemas.common import Message
from ..schemas.student import (
    CertificationIn,
    CertificationOut,
    ProjectIn,
    ProjectOut,
    RoleProfileOut,
    SkillIn,
    SkillOut,
    StudentProfileOut,
    StudentProfileUpdate,
)
from ..services.audit import record_audit
from ..services.readiness import calculate_readiness
from .serializers import student_profile_out

router = APIRouter(prefix="/students", tags=["Student profile"])


def _sync_completion(db: Session, student: Student) -> None:
    """Refresh the completion percentage (and target role list) after a profile change.

    Flush + refresh so the recomputation sees the row that was just added or edited.
    """

    db.flush()
    db.refresh(student)
    calculate_readiness(db, student, persist=False)


@router.get("/roles", response_model=list[RoleProfileOut])
def list_target_roles(db: Session = Depends(get_db), _: Account = Depends(get_current_account)):
    """Target roles available for selection, backed by the role_profiles table."""

    return db.query(RoleProfile).filter(RoleProfile.is_active.is_(True)).order_by(RoleProfile.name).all()


@router.get("/me/profile", response_model=StudentProfileOut)
def read_my_profile(student: Student = Depends(get_current_student)) -> StudentProfileOut:
    return student_profile_out(student)


@router.patch("/me/profile", response_model=StudentProfileOut)
def update_my_profile(
    payload: StudentProfileUpdate,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> StudentProfileOut:
    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if field == "target_role" and value:
            exists = (
                db.query(RoleProfile).filter(RoleProfile.name == value, RoleProfile.is_active.is_(True)).count()
            )
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"'{value}' is not one of the supported target roles",
                )
            if value not in (student.target_roles or []):
                student.target_roles = [*(student.target_roles or []), value]
        setattr(student, field, value)

    _sync_completion(db, student)
    record_audit(
        db,
        actor=account,
        action="update_profile",
        entity_type="student",
        entity_id=student.id,
        summary="Student updated their career profile",
        meta={"fields": sorted(changes.keys())},
    )
    db.commit()
    db.refresh(student)
    return student_profile_out(student)


@router.get("/{student_id}/profile", response_model=StudentProfileOut)
def read_student_profile(
    student_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_mentor_or_admin),
) -> StudentProfileOut:
    """Mentors may read their assigned students only; administrators may read any student."""

    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if account.role == UserRole.mentor:
        mentor = db.query(Mentor).filter(Mentor.account_id == account.id).one_or_none()
        assigned = mentor is not None and any(
            assignment.student_id == student_id and assignment.is_active for assignment in mentor.assignments
        )
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="This student is not assigned to you"
            )

    return student_profile_out(student)


# --- skills ---------------------------------------------------------------------


@router.post("/me/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def add_skill(
    payload: SkillIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SkillOut:
    name = payload.name.strip()
    duplicate = db.query(Skill).filter(Skill.student_id == student.id, Skill.name.ilike(name)).count()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"'{name}' is already on your profile")

    skill = Skill(
        student_id=student.id,
        name=name,
        proficiency=payload.proficiency,
        years_experience=payload.years_experience,
    )
    db.add(skill)
    _sync_completion(db, student)
    db.commit()
    db.refresh(skill)
    return skill


@router.patch("/me/skills/{skill_id}", response_model=SkillOut)
def update_skill(
    skill_id: int,
    payload: SkillIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> SkillOut:
    skill = db.get(Skill, skill_id)
    if skill is None or skill.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    skill.name = payload.name.strip()
    skill.proficiency = payload.proficiency
    skill.years_experience = payload.years_experience
    _sync_completion(db, student)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/me/skills/{skill_id}", response_model=Message)
def delete_skill(
    skill_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Message:
    skill = db.get(Skill, skill_id)
    if skill is None or skill.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    db.delete(skill)
    _sync_completion(db, student)
    db.commit()
    return Message(message="Skill removed")


# --- projects -------------------------------------------------------------------


@router.post("/me/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def add_project(
    payload: ProjectIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = Project(student_id=student.id, **payload.model_dump())
    db.add(project)
    _sync_completion(db, student)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/me/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if project is None or project.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    for field, value in payload.model_dump().items():
        setattr(project, field, value)
    _sync_completion(db, student)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/me/projects/{project_id}", response_model=Message)
def delete_project(
    project_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Message:
    project = db.get(Project, project_id)
    if project is None or project.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    db.delete(project)
    _sync_completion(db, student)
    db.commit()
    return Message(message="Project removed")


# --- certifications -------------------------------------------------------------


@router.post("/me/certifications", response_model=CertificationOut, status_code=status.HTTP_201_CREATED)
def add_certification(
    payload: CertificationIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CertificationOut:
    certification = Certification(student_id=student.id, **payload.model_dump())
    db.add(certification)
    _sync_completion(db, student)
    db.commit()
    db.refresh(certification)
    return certification


@router.patch("/me/certifications/{certification_id}", response_model=CertificationOut)
def update_certification(
    certification_id: int,
    payload: CertificationIn,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> CertificationOut:
    certification = db.get(Certification, certification_id)
    if certification is None or certification.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")

    for field, value in payload.model_dump().items():
        setattr(certification, field, value)
    _sync_completion(db, student)
    db.commit()
    db.refresh(certification)
    return certification


@router.delete("/me/certifications/{certification_id}", response_model=Message)
def delete_certification(
    certification_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> Message:
    certification = db.get(Certification, certification_id)
    if certification is None or certification.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")

    db.delete(certification)
    _sync_completion(db, student)
    db.commit()
    return Message(message="Certification removed")


