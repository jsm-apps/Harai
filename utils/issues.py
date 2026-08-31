import sqlite3
import uuid

DB_FILE = "issues.db"

def _get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            risk_rating INTEGER NOT NULL,
            details TEXT NOT NULL,
            notes TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def list_issues():
    """
    Return all issues as a list of dictionaries.
    """
    init_db()

    conn = _get_connection()

    cursor = conn.execute(
        """
        SELECT
            id,
            title,
            risk_rating,
            details,
            notes
        FROM issues
        ORDER BY risk_rating DESC
        """
    )

    issues = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return issues


def show_issue(issue_id):
    """
    Return a single issue by ID.

    Returns None if the issue does not exist.
    """
    init_db()

    conn = _get_connection()

    cursor = conn.execute(
        """
        SELECT
            id,
            title,
            risk_rating,
            details,
            notes
        FROM issues
        WHERE id = ?
        """,
        (str(issue_id),)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def add_issue(title, risk_rating, details, notes):
    """
    Add a new security issue.

    Args:
        title: Issue title.
        risk_rating: Risk rating between 0 and 100.
        details: Issue details.

    Returns:
        The newly created issue as a dictionary.
    """

    if title is None or not title.strip():
        raise ValueError("title cannot be empty")

    if details is None or not details.strip():
        raise ValueError("details cannot be empty")

    if notes is None or not notes.strip():
            raise ValueError("notes cannot be empty")

    try:
        risk_rating = int(risk_rating)
    except (TypeError, ValueError):
        raise ValueError(
            "risk_rating must be an integer between 0 and 100"
        )

    if risk_rating < 0 or risk_rating > 100:
        raise ValueError(
            "risk_rating must be between 0 and 100"
        )

    init_db()

    issue_id = str(uuid.uuid4())

    conn = _get_connection()

    conn.execute(
        """
        INSERT INTO issues (
            id,
            title,
            risk_rating,
            details,
            notes
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            issue_id,
            title.strip(),
            risk_rating,
            details.strip(),
            notes.strip()
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": issue_id,
        "title": title.strip(),
        "risk_rating": risk_rating,
        "details": details.strip(),
        "notes": notes.strip()
    }





