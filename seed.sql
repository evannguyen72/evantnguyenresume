-- Starting data, loaded once when the database is first created.

-- ---------------------------------------------------------------- projects
INSERT INTO projects (id, title, summary, details, role, dates, link, repo, featured, created_at) VALUES (
    1,
    'ClassClips',
    'A collaborative note-sharing web app with AI summarization, user accounts and like-based ranking that helps students study faster.',
    'Built with a team. Students upload and share class notes, and the Gemini API generates summaries so classmates can skim before they dive in. A like-based system brings the most useful notes to the top.' || char(10) || char(10) ||
    'I integrated the external APIs, built user authentication, and developed scalable frontend and backend features alongside the rest of the team.',
    'Team project · full-stack',
    'Aug 2025 – Present',
    '',
    '',
    1,
    '2025-09-01 00:00:00'
);

INSERT INTO tags (name) VALUES ('JavaScript'), ('Gemini API'), ('REST APIs'), ('Documentation');

INSERT INTO project_tags (project_id, tag_id, position)
SELECT 1, id, CASE name
    WHEN 'JavaScript'    THEN 0
    WHEN 'Gemini API'    THEN 1
    WHEN 'REST APIs'     THEN 2
    WHEN 'Documentation' THEN 3
END
FROM tags
WHERE name IN ('JavaScript', 'Gemini API', 'REST APIs', 'Documentation');

-- ---------------------------------------------------------------- experience
INSERT INTO experience (id, title, organization, location, start_label, end_label, is_current, sort_order) VALUES
    (1, 'Network Security Technical Support', 'Barracuda Networks', 'Alpharetta, GA', 'Jul 2026', '', 1, 30),
    (2, 'AI Trainer & Developer', 'Handshake AI Training & Evaluation', 'Remote', 'Oct 2025', 'Jul 2026', 0, 20),
    (3, 'CIPHER IT Technician', 'Georgia Tech Research Institute (GTRI)', 'Atlanta, GA', 'Jun 2022', 'Jan 2024', 0, 10);

INSERT INTO experience_bullets (experience_id, position, text) VALUES
    (1, 0, 'Resolve high-volume customer issues over phone, email and chat across network and security products.'),
    (1, 1, 'Work daily with TCP/IP, routing and DHCP, and use Bash, shell and Python scripts to speed up resolution.'),
    (1, 2, 'Write and publish internal and public product solutions, and document and escalate software bugs to senior engineering.'),
    (2, 0, 'Evaluated model outputs and flagged logical inconsistencies and potential issues.'),
    (2, 1, 'Sharpened analytical thinking, debugging and technical documentation.'),
    (3, 0, 'Supported enterprise systems in high-reliability environments, focused on performance and stability.'),
    (3, 1, 'Diagnosed system, application and connectivity issues across Linux, macOS and Windows.'),
    (3, 2, 'Analyzed logs and system behavior to find root causes, and documented every resolution clearly.'),
    (3, 3, 'Worked with cross-functional teams to keep operations running under competing priorities.');

-- ---------------------------------------------------------------- education
INSERT INTO education (degree, school, date_label, detail) VALUES (
    'B.S. Computer Science',
    'University of Georgia',
    'Dec 2025',
    'Franklin College of Arts and Sciences. Coursework in algorithms, data structures, computer networks, cybersecurity, software engineering, biomedical image analysis and web programming.'
);
