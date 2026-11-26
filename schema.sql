-- Portfolio database schema (SQLite).
-- build.py reads these tables to generate the website.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- projects

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL CHECK (length(title) BETWEEN 1 AND 80),
    summary     TEXT    NOT NULL CHECK (length(summary) BETWEEN 1 AND 200),
    details     TEXT    NOT NULL DEFAULT '' CHECK (length(details) <= 4000),
    role        TEXT    NOT NULL DEFAULT '',
    dates       TEXT    NOT NULL DEFAULT '',
    link        TEXT    NOT NULL DEFAULT '' CHECK (link = '' OR link LIKE 'https://%'),
    repo        TEXT    NOT NULL DEFAULT '' CHECK (repo = '' OR repo LIKE 'https://%'),
    featured    INTEGER NOT NULL DEFAULT 0 CHECK (featured IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Each skill/technology is stored once and shared across projects.
CREATE TABLE IF NOT EXISTS tags (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- Many-to-many: which skills each project used. `position` keeps the order you typed them.
CREATE TABLE IF NOT EXISTS project_tags (
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id)     ON DELETE CASCADE,
    position    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (project_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_project_tags_tag ON project_tags(tag_id);

-- ---------------------------------------------------------------- experience

CREATE TABLE IF NOT EXISTS experience (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    organization  TEXT    NOT NULL,
    location      TEXT    NOT NULL DEFAULT '',
    start_label   TEXT    NOT NULL,          -- e.g. 'Jul 2026'
    end_label     TEXT    NOT NULL DEFAULT '', -- '' when current
    is_current    INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
    sort_order    INTEGER NOT NULL DEFAULT 0  -- higher shows first
);

CREATE TABLE IF NOT EXISTS experience_bullets (
    experience_id  INTEGER NOT NULL REFERENCES experience(id) ON DELETE CASCADE,
    position       INTEGER NOT NULL,
    text           TEXT    NOT NULL,
    PRIMARY KEY (experience_id, position)
);

-- ---------------------------------------------------------------- education

CREATE TABLE IF NOT EXISTS education (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    degree      TEXT NOT NULL,
    school      TEXT NOT NULL,
    date_label  TEXT NOT NULL DEFAULT '',
    detail      TEXT NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------- views

-- How many projects use each skill.
CREATE VIEW IF NOT EXISTS skill_usage AS
SELECT t.name AS skill, COUNT(pt.project_id) AS project_count
FROM tags t
LEFT JOIN project_tags pt ON pt.tag_id = t.id
GROUP BY t.id
ORDER BY project_count DESC, t.name;
