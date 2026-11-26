"""Manage portfolio projects in the SQLite database.

Usage:
    python manage.py list                 show all projects
    python manage.py add                  add a project (asks questions)
    python manage.py edit 3               edit project 3 (press Enter to keep a value)
    python manage.py delete 3             delete project 3
    python manage.py feature 3            toggle "featured" on project 3
    python manage.py skills               projects per skill (from the skill_usage view)
    python manage.py sql "SELECT ..."     run your own SQL query

After changing projects: python build.py, then commit and push.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys

import db

SKILL_HINT = ("Skill map names: Python, SQL, JavaScript, Java, Bash, TCP/IP, Routing, DHCP, "
              "Network Security, Linux, Windows, macOS, REST APIs, Gemini API, Log Analysis, "
              "AI Evaluation, Troubleshooting, Documentation, Excel")


def ask(label: str, current: str = "", required: bool = False) -> str:
    suffix = f" [{current}]" if current else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            value = current
        if value or not required:
            return value
        print("  This one is required.")


def ask_details(current: str = "") -> str:
    print("Details (what you built, how, and the result). Finish with an empty line."
          + (" Leave empty to keep the current text." if current else ""))
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    return "\n".join(lines) if lines else current


def ask_yes_no(label: str, current: bool = False) -> bool:
    default = "Y/n" if current else "y/N"
    value = input(f"{label} ({default}): ").strip().lower()
    return current if not value else value.startswith("y")


def prompt_project(existing: dict | None = None) -> dict:
    e = existing or {}
    print(SKILL_HINT)
    return {
        "title": ask("Title", e.get("title", ""), required=True),
        "summary": ask("One-line summary (shown on the card)", e.get("summary", ""), required=True),
        "details": ask_details(e.get("details", "")),
        "tags": [t.strip() for t in ask("Skills, comma separated", ", ".join(e.get("tags", []))).split(",") if t.strip()],
        "role": ask("Your role", e.get("role", "")),
        "dates": ask("Dates (e.g. Aug 2025 – Present)", e.get("dates", "")),
        "link": ask("Live link (https://… or blank)", e.get("link", "")),
        "repo": ask("Code link (https://… or blank)", e.get("repo", "")),
        "featured": ask_yes_no("Feature this project?", e.get("featured", False)),
    }


def cmd_list(conn, _args):
    projects = db.fetch_projects(conn)
    if not projects:
        print("No projects yet. Add one with: python manage.py add")
        return
    for p in projects:
        star = "★" if p["featured"] else " "
        print(f"{p['id']:>3} {star} {p['title']:<30} {p['dates']:<22} {', '.join(p['tags'])}")


def cmd_add(conn, _args):
    while True:
        data = prompt_project()
        try:
            pid = db.add_project(conn, data)
            print(f"Added project {pid}. Run 'python build.py' to rebuild the site.")
            return
        except (db.ValidationError, sqlite3.IntegrityError) as e:
            print(f"Not saved: {e}. Let's try again.\n")


def cmd_edit(conn, args):
    current = db.fetch_project(conn, args.id)
    if not current:
        sys.exit(f"No project with id {args.id}. See: python manage.py list")
    print(f"Editing '{current['title']}'. Press Enter to keep a value.")
    data = prompt_project(current)
    try:
        db.update_project(conn, args.id, data)
        print("Saved. Run 'python build.py' to rebuild the site.")
    except (db.ValidationError, sqlite3.IntegrityError) as e:
        sys.exit(f"Not saved: {e}")


def cmd_delete(conn, args):
    current = db.fetch_project(conn, args.id)
    if not current:
        sys.exit(f"No project with id {args.id}.")
    if input(f"Delete '{current['title']}'? Type yes to confirm: ").strip().lower() != "yes":
        print("Cancelled.")
        return
    db.delete_project(conn, args.id)
    print("Deleted.")


def cmd_feature(conn, args):
    current = db.fetch_project(conn, args.id)
    if not current:
        sys.exit(f"No project with id {args.id}.")
    current["featured"] = not current["featured"]
    db.update_project(conn, args.id, current)
    print(f"'{current['title']}' is now {'featured' if current['featured'] else 'not featured'}.")


def cmd_skills(conn, _args):
    rows = db.fetch_skill_usage(conn)
    if not rows:
        print("No skills tagged yet.")
    for skill, count in rows:
        print(f"{skill:<22} {count}")


def cmd_sql(conn, args):
    try:
        cur = conn.execute(args.query)
    except sqlite3.Error as e:
        sys.exit(f"SQL error: {e}")
    if cur.description:
        cols = [d[0] for d in cur.description]
        print(" | ".join(cols))
        for row in cur.fetchall():
            print(" | ".join("" if v is None else str(v) for v in row))
    conn.commit()
    if not args.query.lstrip().lower().startswith("select"):
        db.write_dump(conn)
        print(f"Done. {cur.rowcount} row(s) affected.")


def main():
    parser = argparse.ArgumentParser(description="Manage portfolio projects.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    sub.add_parser("add").set_defaults(fn=cmd_add)
    for name, fn in (("edit", cmd_edit), ("delete", cmd_delete), ("feature", cmd_feature)):
        p = sub.add_parser(name)
        p.add_argument("id", type=int)
        p.set_defaults(fn=fn)
    sub.add_parser("skills").set_defaults(fn=cmd_skills)
    p = sub.add_parser("sql")
    p.add_argument("query")
    p.set_defaults(fn=cmd_sql)

    args = parser.parse_args()
    conn = db.connect()
    try:
        args.fn(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
