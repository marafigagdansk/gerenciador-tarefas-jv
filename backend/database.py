import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dados.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_master INTEGER NOT NULL DEFAULT 0,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    created_by_user_id INTEGER NOT NULL REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS company_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('master', 'collaborator')),
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (company_id, user_id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    due_date TEXT DEFAULT NULL,
    created_by_membership_id INTEGER NOT NULL REFERENCES company_memberships(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_visibilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES company_memberships(id) ON DELETE CASCADE,
    granted_by_membership_id INTEGER NOT NULL REFERENCES company_memberships(id),
    can_create_tasks INTEGER NOT NULL DEFAULT 0,
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, membership_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'blocked', 'done')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    due_date TEXT DEFAULT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_by_membership_id INTEGER NOT NULL REFERENCES company_memberships(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_assignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    membership_id INTEGER NOT NULL REFERENCES company_memberships(id) ON DELETE CASCADE,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (task_id, membership_id)
);

CREATE TABLE IF NOT EXISTS subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_by_membership_id INTEGER NOT NULL REFERENCES company_memberships(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_company_project ON tasks(company_id, project_id);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON company_memberships(user_id);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    # A tabela legada "empresas" (versão anterior, sem usuários) não é alterada nem removida.
    conn = get_connection()
    conn.executescript(SCHEMA)

    # Migração: adiciona coluna due_date se a tabela tasks já existir sem ela
    cursor = conn.execute("PRAGMA table_info(tasks)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "due_date" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT DEFAULT NULL")

    # Migração: adiciona coluna position (ordem manual no Kanban); tarefas antigas seguem a ordem de criação
    if "position" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN position INTEGER NOT NULL DEFAULT 0")
        conn.execute("UPDATE tasks SET position = id")

    # Migração: adiciona coluna due_date (previsão de conclusão) em projects
    cursor = conn.execute("PRAGMA table_info(projects)")
    if "due_date" not in [row["name"] for row in cursor.fetchall()]:
        conn.execute("ALTER TABLE projects ADD COLUMN due_date TEXT DEFAULT NULL")

    # Migração: adiciona coluna can_create_tasks em project_visibilities
    cursor = conn.execute("PRAGMA table_info(project_visibilities)")
    if "can_create_tasks" not in [row["name"] for row in cursor.fetchall()]:
        conn.execute("ALTER TABLE project_visibilities ADD COLUMN can_create_tasks INTEGER NOT NULL DEFAULT 0")

    # Migração: adiciona coluna is_master se a tabela users já existir sem ela
    cursor = conn.execute("PRAGMA table_info(users)")
    user_cols = [row["name"] for row in cursor.fetchall()]
    if "is_master" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_master INTEGER NOT NULL DEFAULT 0")

    # Migração: adiciona coluna must_change_password se a tabela users já existir sem ela
    if "must_change_password" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")

    # Garante que o primeiro usuário (criador no setup) ou usuários com role master sejam identificados como masters
    conn.execute("UPDATE users SET is_master = 1 WHERE id = 1")
    conn.execute("""
        UPDATE users SET is_master = 1 WHERE id IN (
            SELECT user_id FROM company_memberships WHERE role = 'master'
            UNION
            SELECT created_by_user_id FROM companies
        )
    """)

    conn.commit()
    conn.close()
