"""Create validated AI skill-gap result storage.

Revision ID: 20260922_ai_skill_gap_results
Revises:
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260922_ai_skill_gap_results"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_skill_gap_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_role", sa.String(length=120), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("missing_skills", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("recommendations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("validation_status", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("is_outdated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_skill_gap_results_student_id", "ai_skill_gap_results", ["student_id"])
    op.create_index("ix_ai_skill_gap_results_target_role", "ai_skill_gap_results", ["target_role"])
    op.create_index("ix_ai_skill_gap_results_validation_status", "ai_skill_gap_results", ["validation_status"])
    op.create_index("ix_ai_skill_gap_results_is_outdated", "ai_skill_gap_results", ["is_outdated"])
    op.create_index(
        "ix_ai_skill_gap_results_student_role_created",
        "ai_skill_gap_results",
        ["student_id", "target_role", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_skill_gap_results_student_role_created", table_name="ai_skill_gap_results")
    op.drop_index("ix_ai_skill_gap_results_is_outdated", table_name="ai_skill_gap_results")
    op.drop_index("ix_ai_skill_gap_results_validation_status", table_name="ai_skill_gap_results")
    op.drop_index("ix_ai_skill_gap_results_target_role", table_name="ai_skill_gap_results")
    op.drop_index("ix_ai_skill_gap_results_student_id", table_name="ai_skill_gap_results")
    op.drop_table("ai_skill_gap_results")
