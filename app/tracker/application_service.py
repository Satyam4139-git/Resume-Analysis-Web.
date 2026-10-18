from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.tracker.database import (
    get_connection,
    initialize_database,
)


class ApplicationService:

    STATUSES = [
        "Saved",
        "Applied",
        "Screening",
        "Interview",
        "Offer",
        "Rejected",
        "Withdrawn",
    ]

    def __init__(self):

        initialize_database()

    # ==========================================================
    # CREATE
    # ==========================================================

    def create(
        self,
        user_id: str,
        company: str,
        role: str,
        job_url: Optional[str] = None,
        status: str = "Applied",
        applied_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:

        if not company.strip():
            raise ValueError(
                "Company is required."
            )

        if not role.strip():
            raise ValueError(
                "Role is required."
            )

        if status not in self.STATUSES:
            status = "Applied"

        connection = get_connection()

        try:

            cursor = connection.execute(
                """
                INSERT INTO applications
                (
                    user_id,
                    company,
                    role,
                    job_url,
                    status,
                    applied_date,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    company.strip(),
                    role.strip(),
                    job_url,
                    status,
                    applied_date,
                    notes,
                ),
            )

            connection.commit()

            application_id = cursor.lastrowid

        finally:

            connection.close()

        return self.get(user_id, application_id)

    # ==========================================================
    # GET ONE
    # ==========================================================

    def get(
        self,
        user_id: str,
        application_id: int,
    ) -> Dict[str, Any]:

        connection = get_connection()

        try:

            row = connection.execute(
                """
                SELECT *
                FROM applications
                WHERE id = ? AND user_id = ?
                """,
                (application_id, user_id),
            ).fetchone()

        finally:

            connection.close()

        if row is None:
            raise ValueError(
                "Application not found."
            )

        return dict(row)

    # ==========================================================
    # GET ALL
    # ==========================================================

    def get_all(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        connection = get_connection()

        try:

            if status:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM applications
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                    """,
                    (user_id, status),
                ).fetchall()

            else:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM applications
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                ).fetchall()

        finally:

            connection.close()

        return [
            dict(row)
            for row in rows
        ]

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(
        self,
        user_id: str,
        application_id: int,
        company: Optional[str] = None,
        role: Optional[str] = None,
        job_url: Optional[str] = None,
        status: Optional[str] = None,
        applied_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:

        existing = self.get(user_id, application_id)

        company = (
            company
            if company is not None
            else existing["company"]
        )

        role = (
            role
            if role is not None
            else existing["role"]
        )

        job_url = (
            job_url
            if job_url is not None
            else existing["job_url"]
        )

        status = (
            status
            if status is not None
            else existing["status"]
        )

        applied_date = (
            applied_date
            if applied_date is not None
            else existing["applied_date"]
        )

        notes = (
            notes
            if notes is not None
            else existing["notes"]
        )

        if status not in self.STATUSES:
            raise ValueError(
                f"Invalid status: {status}"
            )

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE applications
                SET
                    company = ?,
                    role = ?,
                    job_url = ?,
                    status = ?,
                    applied_date = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (
                    company,
                    role,
                    job_url,
                    status,
                    applied_date,
                    notes,
                    application_id,
                    user_id,
                ),
            )

            connection.commit()

        finally:

            connection.close()

        return self.get(user_id, application_id)

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete(
        self,
        user_id: str,
        application_id: int,
    ) -> bool:

        connection = get_connection()

        try:

            cursor = connection.execute(
                """
                DELETE FROM applications
                WHERE id = ? AND user_id = ?
                """,
                (application_id, user_id),
            )

            connection.commit()

            deleted = cursor.rowcount > 0

        finally:

            connection.close()

        return deleted

    # ==========================================================
    # STATISTICS
    # ==========================================================

    def statistics(self, user_id: str):

        applications = self.get_all(user_id)

        total = len(applications)

        statistics = {
            "total": total,
            "saved": 0,
            "applied": 0,
            "screening": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
            "withdrawn": 0,
        }

        for application in applications:

            status = (
                application["status"]
                .lower()
            )

            if status in statistics:
                statistics[status] += 1

        return statistics