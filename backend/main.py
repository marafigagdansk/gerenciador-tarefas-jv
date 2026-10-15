import re
import sqlite3
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from database import init_db, get_connection
from security import create_token, decode_token, hash_password, verify_password

init_db()

app = FastAPI(title="Gerenciador de Tarefas - API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Role = Literal["master", "collaborator"]
Status = Literal["todo", "in_progress", "blocked", "done"]
Priority = Literal["low", "medium", "high"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Validadores / utilitários
# ---------------------------------------------------------------------------
def _clean_name(v: str, label: str, min_len: int = 2) -> str:
    v = v.strip()
    if len(v) < min_len:
        raise ValueError(f"{label} deve ter pelo menos {min_len} caracteres.")
    return v


def _clean_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("E-mail inválido.")
    return v


def _clean_password(v: str) -> str:
    if len(v) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    return v


def _clean_cnpj(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if len(digits) not in (11, 14):
        raise ValueError("Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos).")
    return digits


# ---------------------------------------------------------------------------
# Dependências
# ---------------------------------------------------------------------------
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def current_user(authorization: Optional[str] = Header(None), db=Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado.")
    user_id = decode_token(authorization[7:].strip())
    if user_id is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    user = db.execute(
        "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return dict(user)


def member_ctx(company_id: int, user=Depends(current_user), db=Depends(get_db)):
    """Resolve o activeMembership do usuário na empresa da rota. Todas as permissões partem daqui."""
    row = db.execute(
        """SELECT m.id, m.company_id, m.user_id, m.role, u.name
           FROM company_memberships m JOIN users u ON u.id = m.user_id
           WHERE m.company_id = ? AND m.user_id = ? AND m.is_active = 1""",
        (company_id, user["id"]),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Você não pertence a esta empresa.")
    return dict(row)


def master_ctx(m=Depends(member_ctx)):
    if m["role"] != "master":
        raise HTTPException(status_code=403, detail="Ação restrita ao Master da empresa.")
    return m


# ---------------------------------------------------------------------------
# Auth / Setup
# ---------------------------------------------------------------------------
class SetupIn(BaseModel):
    name: str
    email: str
    password: str
    company_name: str
    cnpj: str

    _n = field_validator("name")(lambda cls, v: _clean_name(v, "O nome"))
    _e = field_validator("email")(lambda cls, v: _clean_email(v))
    _p = field_validator("password")(lambda cls, v: _clean_password(v))
    _cn = field_validator("company_name")(lambda cls, v: _clean_name(v, "O nome da empresa"))
    _c = field_validator("cnpj")(lambda cls, v: _clean_cnpj(v))


class LoginIn(BaseModel):
    email: str
    password: str


def user_payload(db, user: dict):
    rows = db.execute(
        """SELECT m.id AS membership_id, m.role, c.id AS company_id, c.name AS company_name, c.cnpj
           FROM company_memberships m JOIN companies c ON c.id = m.company_id
           WHERE m.user_id = ? AND m.is_active = 1 ORDER BY c.name""",
        (user["id"],),
    ).fetchall()
    memberships = [dict(r) for r in rows]
    return {
        "user": user,
        "memberships": memberships,
        "can_create_company": any(m["role"] == "master" for m in memberships),
    }


@app.get("/api/setup/status")
def setup_status(db=Depends(get_db)):
    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    return {"needs_setup": count == 0}


@app.post("/api/setup", status_code=201)
def setup(data: SetupIn, db=Depends(get_db)):
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        raise HTTPException(status_code=403, detail="O sistema já foi configurado.")
    cur = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (data.name, data.email, hash_password(data.password)),
    )
    user_id = cur.lastrowid
    cur = db.execute(
        "INSERT INTO companies (name, cnpj, created_by_user_id) VALUES (?, ?, ?)",
        (data.company_name, data.cnpj, user_id),
    )
    db.execute(
        "INSERT INTO company_memberships (company_id, user_id, role) VALUES (?, ?, 'master')",
        (cur.lastrowid, user_id),
    )
    db.commit()
    user = {"id": user_id, "name": data.name, "email": data.email}
    return {"token": create_token(user_id), **user_payload(db, user)}


@app.post("/api/auth/login")
def login(data: LoginIn, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (data.email.strip().lower(),),
    ).fetchone()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    user = {"id": row["id"], "name": row["name"], "email": row["email"]}
    return {"token": create_token(row["id"]), **user_payload(db, user)}


@app.get("/api/auth/me")
def me(user=Depends(current_user), db=Depends(get_db)):
    return user_payload(db, user)


# ---------------------------------------------------------------------------
# Empresas
# ---------------------------------------------------------------------------
class CompanyIn(BaseModel):
    name: str
    cnpj: str

    _n = field_validator("name")(lambda cls, v: _clean_name(v, "O nome da empresa"))
    _c = field_validator("cnpj")(lambda cls, v: _clean_cnpj(v))


@app.post("/api/companies", status_code=201)
def create_company(data: CompanyIn, user=Depends(current_user), db=Depends(get_db)):
    is_master = db.execute(
        "SELECT 1 FROM company_memberships WHERE user_id = ? AND role = 'master' AND is_active = 1 LIMIT 1",
        (user["id"],),
    ).fetchone()
    if not is_master:
        raise HTTPException(status_code=403, detail="Apenas Masters podem criar empresas.")
    try:
        cur = db.execute(
            "INSERT INTO companies (name, cnpj, created_by_user_id) VALUES (?, ?, ?)",
            (data.name, data.cnpj, user["id"]),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Já existe uma empresa com este CPF/CNPJ.")
    db.execute(
        "INSERT INTO company_memberships (company_id, user_id, role) VALUES (?, ?, 'master')",
        (cur.lastrowid, user["id"]),
    )
    db.commit()
    return user_payload(db, user)


@app.get("/api/companies/{company_id}")
def get_company(company_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    c = db.execute("SELECT id, name, cnpj FROM companies WHERE id = ?", (company_id,)).fetchone()
    return {**dict(c), "membership": {"id": m["id"], "role": m["role"], "name": m["name"]}}


# ---------------------------------------------------------------------------
# Membros
# ---------------------------------------------------------------------------
class MemberLookupOut(BaseModel):
    exists: bool
    name: Optional[str] = None
    already_member: bool = False


class MemberIn(BaseModel):
    email: str
    role: Role
    name: Optional[str] = None
    password: Optional[str] = None

    _e = field_validator("email")(lambda cls, v: _clean_email(v))


class MemberPatch(BaseModel):
    role: Optional[Role] = None
    is_active: Optional[bool] = None


@app.get("/api/companies/{company_id}/members")
def list_members(company_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    rows = db.execute(
        """SELECT m.id, m.role, m.is_active, u.name, u.email
           FROM company_memberships m JOIN users u ON u.id = m.user_id
           WHERE m.company_id = ? ORDER BY u.name""",
        (company_id,),
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["is_active"] = bool(d["is_active"])
        if m["role"] != "master":
            if not d["is_active"]:
                continue
            d.pop("email")
        result.append(d)
    return result


@app.get("/api/companies/{company_id}/members/lookup", response_model=MemberLookupOut)
def lookup_member(company_id: int, email: str, m=Depends(master_ctx), db=Depends(get_db)):
    email = email.strip().lower()
    user = db.execute("SELECT id, name FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return MemberLookupOut(exists=False)
    ms = db.execute(
        "SELECT is_active FROM company_memberships WHERE company_id = ? AND user_id = ?",
        (company_id, user["id"]),
    ).fetchone()
    return MemberLookupOut(exists=True, name=user["name"], already_member=bool(ms and ms["is_active"]))


@app.post("/api/companies/{company_id}/members", status_code=201)
def add_member(company_id: int, data: MemberIn, m=Depends(master_ctx), db=Depends(get_db)):
    user = db.execute("SELECT id FROM users WHERE email = ?", (data.email,)).fetchone()
    user_created = False
    if user:
        # Cenário B: usuário existente. A senha atual NUNCA é alterada.
        user_id = user["id"]
        existing = db.execute(
            "SELECT id, is_active FROM company_memberships WHERE company_id = ? AND user_id = ?",
            (company_id, user_id),
        ).fetchone()
        if existing and existing["is_active"]:
            raise HTTPException(status_code=409, detail="Este usuário já é membro da empresa.")
        if existing:
            db.execute(
                "UPDATE company_memberships SET is_active = 1, role = ? WHERE id = ?",
                (data.role, existing["id"]),
            )
            db.commit()
            return {"user_created": False, "reactivated": True}
    else:
        # Cenário A: novo usuário, exige nome e senha inicial.
        try:
            name = _clean_name(data.name or "", "O nome completo")
            password = _clean_password(data.password or "")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, data.email, hash_password(password)),
        )
        user_id = cur.lastrowid
        user_created = True
    db.execute(
        "INSERT INTO company_memberships (company_id, user_id, role) VALUES (?, ?, ?)",
        (company_id, user_id, data.role),
    )
    db.commit()
    return {"user_created": user_created, "reactivated": False}


@app.patch("/api/companies/{company_id}/members/{membership_id}")
def update_member(
    company_id: int, membership_id: int, data: MemberPatch,
    m=Depends(master_ctx), db=Depends(get_db),
):
    target = db.execute(
        "SELECT id, role, is_active FROM company_memberships WHERE id = ? AND company_id = ?",
        (membership_id, company_id),
    ).fetchone()
    if not target:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")
    new_role = data.role if data.role is not None else target["role"]
    new_active = int(data.is_active) if data.is_active is not None else target["is_active"]
    loses_master = target["role"] == "master" and target["is_active"] and (
        new_role != "master" or not new_active
    )
    if loses_master:
        others = db.execute(
            """SELECT COUNT(*) FROM company_memberships
               WHERE company_id = ? AND role = 'master' AND is_active = 1 AND id != ?""",
            (company_id, membership_id),
        ).fetchone()[0]
        if others == 0:
            raise HTTPException(status_code=400, detail="A empresa precisa ter ao menos um Master ativo.")
    db.execute(
        "UPDATE company_memberships SET role = ?, is_active = ? WHERE id = ?",
        (new_role, new_active, membership_id),
    )
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Projetos
# ---------------------------------------------------------------------------
class ProjectIn(BaseModel):
    name: str
    description: str = ""
    visible_to: list[int] = []

    _n = field_validator("name")(lambda cls, v: _clean_name(v, "O nome do projeto"))


class ProjectPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["active", "archived"]] = None


class VisibilityIn(BaseModel):
    membership_ids: list[int]


def can_access_project(db, m, project_id: int) -> bool:
    if m["role"] == "master":
        return True
    return bool(db.execute(
        "SELECT 1 FROM project_visibilities WHERE project_id = ? AND membership_id = ?",
        (project_id, m["id"]),
    ).fetchone())


def get_project_or_404(db, company_id: int, project_id: int):
    p = db.execute(
        "SELECT * FROM projects WHERE id = ? AND company_id = ?", (project_id, company_id)
    ).fetchone()
    if not p:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    return p


def valid_collaborator_ids(db, company_id: int, ids: list[int]) -> list[int]:
    ids = list(dict.fromkeys(ids))
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = db.execute(
        f"""SELECT id FROM company_memberships
            WHERE company_id = ? AND is_active = 1 AND role = 'collaborator' AND id IN ({marks})""",
        (company_id, *ids),
    ).fetchall()
    return [r["id"] for r in rows]


def set_visibility(db, project_id: int, granted_by: int, company_id: int, ids: list[int]):
    valid = valid_collaborator_ids(db, company_id, ids)
    db.execute("DELETE FROM project_visibilities WHERE project_id = ?", (project_id,))
    for mid in valid:
        db.execute(
            """INSERT INTO project_visibilities (project_id, membership_id, granted_by_membership_id)
               VALUES (?, ?, ?)""",
            (project_id, mid, granted_by),
        )
    return valid


@app.get("/api/companies/{company_id}/projects")
def list_projects(company_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    if m["role"] == "master":
        rows = db.execute(
            "SELECT id, name, description, status FROM projects WHERE company_id = ? ORDER BY name",
            (company_id,),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT p.id, p.name, p.description, p.status FROM projects p
               JOIN project_visibilities v ON v.project_id = p.id
               WHERE p.company_id = ? AND v.membership_id = ? ORDER BY p.name""",
            (company_id, m["id"]),
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/companies/{company_id}/projects", status_code=201)
def create_project(company_id: int, data: ProjectIn, m=Depends(master_ctx), db=Depends(get_db)):
    cur = db.execute(
        """INSERT INTO projects (company_id, name, description, created_by_membership_id)
           VALUES (?, ?, ?, ?)""",
        (company_id, data.name, data.description.strip(), m["id"]),
    )
    set_visibility(db, cur.lastrowid, m["id"], company_id, data.visible_to)
    db.commit()
    p = db.execute(
        "SELECT id, name, description, status FROM projects WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return dict(p)


@app.get("/api/companies/{company_id}/projects/{project_id}")
def get_project(company_id: int, project_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    p = get_project_or_404(db, company_id, project_id)
    if not can_access_project(db, m, project_id):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
    return {k: p[k] for k in ("id", "name", "description", "status")}


@app.patch("/api/companies/{company_id}/projects/{project_id}")
def update_project(
    company_id: int, project_id: int, data: ProjectPatch,
    m=Depends(master_ctx), db=Depends(get_db),
):
    p = get_project_or_404(db, company_id, project_id)
    name = p["name"]
    if data.name is not None:
        try:
            name = _clean_name(data.name, "O nome do projeto")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    description = data.description.strip() if data.description is not None else p["description"]
    status = data.status or p["status"]
    db.execute(
        "UPDATE projects SET name = ?, description = ?, status = ? WHERE id = ?",
        (name, description, status, project_id),
    )
    db.commit()
    return {"id": project_id, "name": name, "description": description, "status": status}


@app.get("/api/companies/{company_id}/projects/{project_id}/visibility")
def get_visibility(company_id: int, project_id: int, m=Depends(master_ctx), db=Depends(get_db)):
    get_project_or_404(db, company_id, project_id)
    rows = db.execute(
        "SELECT membership_id FROM project_visibilities WHERE project_id = ?", (project_id,)
    ).fetchall()
    return {"membership_ids": [r["membership_id"] for r in rows]}


@app.put("/api/companies/{company_id}/projects/{project_id}/visibility")
def put_visibility(
    company_id: int, project_id: int, data: VisibilityIn,
    m=Depends(master_ctx), db=Depends(get_db),
):
    get_project_or_404(db, company_id, project_id)
    valid = set_visibility(db, project_id, m["id"], company_id, data.membership_ids)
    db.commit()
    return {"membership_ids": valid}


# ---------------------------------------------------------------------------
# Tarefas
# ---------------------------------------------------------------------------
class TaskIn(BaseModel):
    title: str
    description: str = ""
    priority: Priority = "medium"
    project_id: Optional[int] = None
    assignee_ids: list[int] = []

    _t = field_validator("title")(lambda cls, v: _clean_name(v, "O título", 2))


class TaskPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    project_id: Optional[int] = None  # distinguimos "ausente" de null via model_fields_set


class AssigneesIn(BaseModel):
    membership_ids: list[int]


class SubtaskIn(BaseModel):
    title: str

    _t = field_validator("title")(lambda cls, v: _clean_name(v, "O título da sub-tarefa", 1))


class SubtaskPatch(BaseModel):
    is_completed: bool


def get_task_or_404(db, company_id: int, task_id: int):
    t = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND company_id = ?", (task_id, company_id)
    ).fetchone()
    if not t:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return t


def ensure_can_see_task(db, m, task):
    # Tarefa Geral: pública na empresa. Tarefa de Projeto: restrita a quem tem acesso ao projeto.
    if task["project_id"] is not None and not can_access_project(db, m, task["project_id"]):
        raise HTTPException(status_code=403, detail="Você não tem acesso a esta tarefa.")


def is_assignee(db, task_id: int, membership_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM task_assignees WHERE task_id = ? AND membership_id = ?",
        (task_id, membership_id),
    ).fetchone())


def serialize_task(db, task) -> dict:
    t = dict(task)
    assignees = db.execute(
        """SELECT a.membership_id, u.name FROM task_assignees a
           JOIN company_memberships m ON m.id = a.membership_id
           JOIN users u ON u.id = m.user_id
           WHERE a.task_id = ? ORDER BY a.assigned_at, a.id""",
        (t["id"],),
    ).fetchall()
    subtasks = db.execute(
        """SELECT s.id, s.title, s.is_completed, s.created_by_membership_id, u.name AS created_by_name
           FROM subtasks s
           JOIN company_memberships m ON m.id = s.created_by_membership_id
           JOIN users u ON u.id = m.user_id
           WHERE s.task_id = ? ORDER BY s.id""",
        (t["id"],),
    ).fetchall()
    creator = db.execute(
        """SELECT u.name FROM company_memberships m JOIN users u ON u.id = m.user_id WHERE m.id = ?""",
        (t["created_by_membership_id"],),
    ).fetchone()
    project_name = None
    if t["project_id"] is not None:
        project_name = db.execute(
            "SELECT name FROM projects WHERE id = ?", (t["project_id"],)
        ).fetchone()["name"]
    t["assignees"] = [dict(a) for a in assignees]
    t["subtasks"] = [{**dict(s), "is_completed": bool(s["is_completed"])} for s in subtasks]
    t["created_by_name"] = creator["name"] if creator else None
    t["project_name"] = project_name
    return t


def touch_task(db, task_id: int):
    db.execute("UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))


def valid_member_ids(db, company_id: int, ids: list[int]) -> list[int]:
    ids = list(dict.fromkeys(ids))
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = db.execute(
        f"SELECT id FROM company_memberships WHERE company_id = ? AND is_active = 1 AND id IN ({marks})",
        (company_id, *ids),
    ).fetchall()
    return [r["id"] for r in rows]


@app.get("/api/companies/{company_id}/tasks")
def list_tasks(
    company_id: int, project_id: Optional[int] = None,
    m=Depends(member_ctx), db=Depends(get_db),
):
    """Sem project_id: mural de Tarefas Gerais. Com project_id: tarefas do projeto (se houver acesso)."""
    if project_id is None:
        rows = db.execute(
            "SELECT * FROM tasks WHERE company_id = ? AND project_id IS NULL ORDER BY id DESC",
            (company_id,),
        ).fetchall()
    else:
        get_project_or_404(db, company_id, project_id)
        if not can_access_project(db, m, project_id):
            raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
        rows = db.execute(
            "SELECT * FROM tasks WHERE company_id = ? AND project_id = ? ORDER BY id DESC",
            (company_id, project_id),
        ).fetchall()
    return [serialize_task(db, r) for r in rows]


@app.post("/api/companies/{company_id}/tasks", status_code=201)
def create_task(company_id: int, data: TaskIn, m=Depends(member_ctx), db=Depends(get_db)):
    if m["role"] == "master":
        project_id = data.project_id
        if project_id is not None:
            project = get_project_or_404(db, company_id, project_id)
            if project["status"] == "archived":
                raise HTTPException(status_code=400, detail="Projeto arquivado não aceita novas tarefas.")
        assignees = valid_member_ids(db, company_id, data.assignee_ids)
    else:
        # Colaborador: sempre Tarefa Geral, auto-atribuída a si mesmo, sem atribuir a terceiros.
        project_id = None
        assignees = [m["id"]]
    cur = db.execute(
        """INSERT INTO tasks (company_id, project_id, title, description, priority, created_by_membership_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (company_id, project_id, data.title, data.description.strip(), data.priority, m["id"]),
    )
    for mid in assignees:
        db.execute("INSERT INTO task_assignees (task_id, membership_id) VALUES (?, ?)", (cur.lastrowid, mid))
    db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, cur.lastrowid))


@app.patch("/api/companies/{company_id}/tasks/{task_id}")
def update_task(
    company_id: int, task_id: int, data: TaskPatch,
    m=Depends(member_ctx), db=Depends(get_db),
):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    fields = data.model_fields_set
    is_master = m["role"] == "master"

    if not is_master:
        if fields - {"status"}:
            raise HTTPException(status_code=403, detail="Colaboradores só podem alterar o status.")
        if "status" in fields and not is_assignee(db, task_id, m["id"]):
            raise HTTPException(status_code=403, detail="Você precisa estar atribuído à tarefa para alterar o status.")

    updates = {}
    try:
        if "title" in fields and data.title is not None:
            updates["title"] = _clean_name(data.title, "O título", 2)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if "description" in fields and data.description is not None:
        updates["description"] = data.description.strip()
    if "priority" in fields and data.priority is not None:
        updates["priority"] = data.priority
    if "status" in fields and data.status is not None:
        updates["status"] = data.status  # sem trava de sub-tarefas em aberto
    if "project_id" in fields:
        if data.project_id is not None:
            project = get_project_or_404(db, company_id, data.project_id)
            if project["status"] == "archived":
                raise HTTPException(status_code=400, detail="Projeto arquivado não aceita novas tarefas.")
        updates["project_id"] = data.project_id

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        db.execute(f"UPDATE tasks SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (*updates.values(), task_id))
        db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, task_id))


@app.post("/api/companies/{company_id}/tasks/{task_id}/claim")
def claim_task(company_id: int, task_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    db.execute(
        "INSERT OR IGNORE INTO task_assignees (task_id, membership_id) VALUES (?, ?)",
        (task_id, m["id"]),
    )
    touch_task(db, task_id)
    db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, task_id))


@app.put("/api/companies/{company_id}/tasks/{task_id}/assignees")
def set_assignees(
    company_id: int, task_id: int, data: AssigneesIn,
    m=Depends(master_ctx), db=Depends(get_db),
):
    get_task_or_404(db, company_id, task_id)
    valid = valid_member_ids(db, company_id, data.membership_ids)
    if valid:
        db.execute(
            "DELETE FROM task_assignees WHERE task_id = ? AND membership_id NOT IN (%s)"
            % ",".join("?" * len(valid)),
            (task_id, *valid),
        )
    else:
        db.execute("DELETE FROM task_assignees WHERE task_id = ?", (task_id,))
    for mid in valid:
        db.execute("INSERT OR IGNORE INTO task_assignees (task_id, membership_id) VALUES (?, ?)", (task_id, mid))
    touch_task(db, task_id)
    db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, task_id))


@app.post("/api/companies/{company_id}/tasks/{task_id}/subtasks", status_code=201)
def create_subtask(
    company_id: int, task_id: int, data: SubtaskIn,
    m=Depends(member_ctx), db=Depends(get_db),
):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    if not is_assignee(db, task_id, m["id"]):
        raise HTTPException(status_code=403, detail="Clique em \"Pegar Tarefa\" para criar sub-tarefas.")
    db.execute(
        "INSERT INTO subtasks (task_id, title, created_by_membership_id) VALUES (?, ?, ?)",
        (task_id, data.title, m["id"]),
    )
    touch_task(db, task_id)
    db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, task_id))


@app.patch("/api/companies/{company_id}/tasks/{task_id}/subtasks/{subtask_id}")
def update_subtask(
    company_id: int, task_id: int, subtask_id: int, data: SubtaskPatch,
    m=Depends(member_ctx), db=Depends(get_db),
):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    if not is_assignee(db, task_id, m["id"]):
        raise HTTPException(status_code=403, detail="Clique em \"Pegar Tarefa\" para marcar sub-tarefas.")
    cur = db.execute(
        "UPDATE subtasks SET is_completed = ? WHERE id = ? AND task_id = ?",
        (int(data.is_completed), subtask_id, task_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sub-tarefa não encontrada.")
    touch_task(db, task_id)
    db.commit()
    return serialize_task(db, get_task_or_404(db, company_id, task_id))
