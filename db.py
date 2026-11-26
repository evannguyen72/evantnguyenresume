"""Database access for the portfolio (SQLite).

database/portfolio.db is the source of truth. It is created from schema.sql and
seed.sql the first time anything connects. manage.py edits it, build.py reads it.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "database"
DB_PATH = DB_DIR / "portfolio.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"
DUMP_PATH = DB_DIR / "dump.sql"

HTTPS_URL = re.compile(r"^https://\S+$", re.IGNORECASE)
MAX_TAGS = 12


class ValidationError(ValueError):
    """Raised when project data breaks a rule. The message is shown to the user."""


# --------------------------------------------------------------------------- connection

def connect() -> sqlite3.Connection:
    """Open the database, creating and seeding it first if it doesn't exist."""
    fresh = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    if fresh:
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
        conn.commit()
        write_dump(conn)
    return conn


def write_dump(conn: sqlite3.Connection) -> None:
    """Save a readable SQL copy of the whole database (handy for reviewing changes on GitHub)."""
    DUMP_PATH.write_text("\n".join(conn.iterdump()) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- reads

PROJECT_SELECT = """
SELECT p.id, p.title, p.summary, p.details, p.role, p.dates, p.link, p.repo,
       p.featured, p.created_at, p.updated_at,
       (SELECT json_group_array(name) FROM (
            SELECT t.name FROM project_tags pt
            JOIN tags t ON t.id = pt.tag_id
            WHERE pt.project_id = p.id
            ORDER BY pt.position)) AS tags
FROM projects p
"""


def _project(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "summary": row["summary"],
        "details": row["details"],
        "role": row["role"],
        "dates": row["dates"],
        "link": row["link"],
        "repo": row["repo"],
        "featured": bool(row["featured"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "tags": json.loads(row["tags"] or "[]"),
    }


def fetch_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(PROJECT_SELECT + " ORDER BY p.featured DESC, p.created_at DESC, p.id DESC").fetchall()
    return [_project(r) for r in rows]


def fetch_project(conn: sqlite3.Connection, project_id: int) -> dict | None:
    row = conn.execute(PROJECT_SELECT + " WHERE p.id = ?", (project_id,)).fetchone()
    return _project(row) if row else None


def fetch_experience(conn: sqlite3.Connection) -> list[dict]:
    jobs = conn.execute("SELECT * FROM experience ORDER BY sort_order DESC, id DESC").fetchall()
    out = []
    for j in jobs:
        bullets = [b["text"] for b in conn.execute(
            "SELECT text FROM experience_bullets WHERE experience_id = ? ORDER BY position", (j["id"],))]
        out.append({
            "title": j["title"],
            "organization": j["organization"],
            "location": j["location"],
            "start": j["start_label"],
            "end": j["end_label"],
            "current": bool(j["is_current"]),
            "bullets": bullets,
        })
    return out


def fetch_education(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT degree, school, date_label, detail FROM education ORDER BY id")]


def fetch_skill_usage(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    return [(r["skill"], r["project_count"]) for r in conn.execute("SELECT skill, project_count FROM skill_usage")]


# --------------------------------------------------------------------------- writes

def clean_project(data: dict) -> dict:
    """Validate and normalise project fields. Raises ValidationError with a readable message."""
    def text(key: str, limit: int) -> str:
        value = str(data.get(key, "") or "").strip()
        if len(value) > limit:
            raise ValidationError(f"{key} is too long ({len(value)} characters, max {limit}).")
        return value

    out = {
        "title": text("title", 80),
        "summary": text("summary", 200),
        "details": text("details", 4000),
        "role": text("role", 80),
        "dates": text("dates", 40),
        "link": text("link", 500),
        "repo": text("repo", 500),
        "featured": bool(data.get("featured", False)),
    }
    if not out["title"]:
        raise ValidationError("A title is required.")
    if not out["summary"]:
        raise ValidationError("A one-line summary is required.")
    for key in ("link", "repo"):
        if out[key] and not HTTPS_URL.match(out[key]):
            raise ValidationError(f"{key} must start with https://")

    tags, seen = [], set()
    for t in data.get("tags", []) or []:
        t = str(t).strip()[:40]
        if t and t.lower() not in seen:
            seen.add(t.lower())
            tags.append(t)
    out["tags"] = tags[:MAX_TAGS]
    return out


def _save_tags(conn: sqlite3.Connection, project_id: int, tags: list[str]) -> None:
    conn.execute("DELETE FROM project_tags WHERE project_id = ?", (project_id,))
    for position, name in enumerate(tags):
        conn.execute("INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (name,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO project_tags (project_id, tag_id, position) VALUES (?, ?, ?)",
            (project_id, tag_id, position),
        )
    _drop_unused_tags(conn)


def _drop_unused_tags(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM project_tags)")


def add_project(conn: sqlite3.Connection, data: dict) -> int:
    p = clean_project(data)
    with conn:
        cur = conn.execute(
            """INSERT INTO projects (title, summary, details, role, dates, link, repo, featured)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (p["title"], p["summary"], p["details"], p["role"], p["dates"], p["link"], p["repo"], int(p["featured"])),
        )
        _save_tags(conn, cur.lastrowid, p["tags"])
    write_dump(conn)
    return cur.lastrowid


def update_project(conn: sqlite3.Connection, project_id: int, data: dict) -> None:
    p = clean_project(data)
    with conn:
        cur = conn.execute(
            """UPDATE projects
               SET title = ?, summary = ?, details = ?, role = ?, dates = ?, link = ?, repo = ?,
                   featured = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (p["title"], p["summary"], p["details"], p["role"], p["dates"], p["link"], p["repo"],
             int(p["featured"]), project_id),
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No project with id {project_id}.")
        _save_tags(conn, project_id, p["tags"])
    write_dump(conn)


def delete_project(conn: sqlite3.Connection, project_id: int) -> None:
    with conn:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        if cur.rowcount == 0:
            raise ValidationError(f"No project with id {project_id}.")
        _drop_unused_tags(conn)
    write_dump(conn)
