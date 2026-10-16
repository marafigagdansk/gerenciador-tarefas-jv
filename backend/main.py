import datetime
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


def _clean_date(v: Optional[str]) -> Optional[str]:
    """Aceita data ISO (AAAA-MM-DD); vazio vira None."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        raise ValueError("Data inválida. Use o formato AAAA-MM-DD.")
    return v


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
        "SELECT id, name, email, is_master, must_change_password FROM users WHERE id = ?", (user_id,)
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
    user_row = db.execute(
        "SELECT id, name, email, is_master, must_change_password FROM users WHERE id = ?", (user["id"],)
    ).fetchone()
    is_master_user = bool(user_row["is_master"]) if user_row and "is_master" in user_row.keys() else False
    must_change = bool(user_row["must_change_password"]) if user_row and "must_change_password" in user_row.keys() else False

    rows = db.execute(
        """SELECT m.id AS membership_id, m.role, c.id AS company_id, c.name AS company_name, c.cnpj
           FROM company_memberships m JOIN companies c ON c.id = m.company_id
           WHERE m.user_id = ? AND m.is_active = 1 ORDER BY c.name""",
        (user["id"],),
    ).fetchall()
    memberships = [dict(r) for r in rows]
    can_create = is_master_user or any(m["role"] == "master" for m in memberships)

    if any(m["role"] == "master" for m in memberships) and not is_master_user:
        db.execute("UPDATE users SET is_master = 1 WHERE id = ?", (user["id"],))
        db.commit()
        is_master_user = True
        can_create = True

    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "is_master": can_create,
            "must_change_password": must_change,
        },
        "memberships": memberships,
        "can_create_company": can_create,
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
        "INSERT INTO users (name, email, password_hash, is_master) VALUES (?, ?, ?, 1)",
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
    user = {"id": user_id, "name": data.name, "email": data.email, "is_master": 1}
    return {"token": create_token(user_id), **user_payload(db, user)}


@app.post("/api/auth/login")
def login(data: LoginIn, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, name, email, is_master, password_hash FROM users WHERE email = ?",
        (data.email.strip().lower(),),
    ).fetchone()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    user = {"id": row["id"], "name": row["name"], "email": row["email"], "is_master": row["is_master"]}
    return {"token": create_token(row["id"]), **user_payload(db, user)}


@app.get("/api/auth/me")
def me(user=Depends(current_user), db=Depends(get_db)):
    return user_payload(db, user)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str

    _p = field_validator("new_password")(lambda cls, v: _clean_password(v))


@app.post("/api/auth/change-password")
def change_password(data: ChangePasswordIn, user=Depends(current_user), db=Depends(get_db)):
    user_row = db.execute(
        "SELECT id, name, email, is_master, password_hash FROM users WHERE id = ?",
        (user["id"],),
    ).fetchone()
    if not user_row or not verify_password(data.current_password, user_row["password_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    if data.current_password == data.new_password:
        raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da senha provisória.")
    db.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
        (hash_password(data.new_password), user["id"]),
    )
    db.commit()
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
    user_row = db.execute(
        "SELECT is_master FROM users WHERE id = ?", (user["id"],)
    ).fetchone()
    is_user_master = bool(user_row and user_row["is_master"])
    is_member_master = db.execute(
        "SELECT 1 FROM company_memberships WHERE user_id = ? AND role = 'master' AND is_active = 1 LIMIT 1",
        (user["id"],),
    ).fetchone()
    if not (is_user_master or is_member_master):
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
    db.execute("UPDATE users SET is_master = 1 WHERE id = ?", (user["id"],))
    db.commit()
    return user_payload(db, user)


@app.get("/api/companies/{company_id}")
def get_company(company_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    c = db.execute("SELECT id, name, cnpj FROM companies WHERE id = ?", (company_id,)).fetchone()
    return {**dict(c), "membership": {"id": m["id"], "role": m["role"], "name": m["name"]}}


class CompanyPatch(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None

    _n = field_validator("name")(lambda cls, v: _clean_name(v, "O nome da empresa") if v is not None else v)
    _c = field_validator("cnpj")(lambda cls, v: _clean_cnpj(v) if v is not None else v)


@app.patch("/api/companies/{company_id}")
def update_company(
    company_id: int,
    data: CompanyPatch,
    m=Depends(master_ctx),
    user=Depends(current_user),
    db=Depends(get_db),
):
    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.cnpj is not None:
        updates["cnpj"] = data.cnpj
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        try:
            db.execute(f"UPDATE companies SET {sets} WHERE id = ?", (*updates.values(), company_id))
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Já existe uma empresa com este CPF/CNPJ.")
    return user_payload(db, user)


@app.delete("/api/companies/{company_id}")
def delete_company(
    company_id: int,
    m=Depends(master_ctx),
    user=Depends(current_user),
    db=Depends(get_db),
):
    db.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    db.commit()
    return user_payload(db, user)



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
            if data.role == "master":
                db.execute("UPDATE users SET is_master = 1 WHERE id = ?", (user_id,))
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
            "INSERT INTO users (name, email, password_hash, is_master, must_change_password) VALUES (?, ?, ?, ?, 1)",
            (name, data.email, hash_password(password), 1 if data.role == "master" else 0),
        )
        user_id = cur.lastrowid
        user_created = True
    db.execute(
        "INSERT INTO company_memberships (company_id, user_id, role) VALUES (?, ?, ?)",
        (company_id, user_id, data.role),
    )
    if data.role == "master":
        db.execute("UPDATE users SET is_master = 1 WHERE id = ?", (user_id,))
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
    if new_role == "master" and new_active:
        db.execute(
            "UPDATE users SET is_master = 1 WHERE id = (SELECT user_id FROM company_memberships WHERE id = ?)",
            (membership_id,),
        )
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Projetos
# ---------------------------------------------------------------------------
class VisibilityItemIn(BaseModel):
    membership_id: int
    can_create_tasks: bool = False


class VisibilityIn(BaseModel):
    membership_ids: Optional[list[int]] = None
    items: Optional[list[VisibilityItemIn]] = None


class ProjectIn(BaseModel):
    name: str
    description: str = ""
    due_date: Optional[str] = None
    visible_to: list[int] = []
    visibility_items: list[VisibilityItemIn] = []

    _n = field_validator("name")(lambda cls, v: _clean_name(v, "O nome do projeto"))
    _d = field_validator("due_date")(lambda cls, v: _clean_date(v))


class ProjectPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["active", "archived"]] = None
    due_date: Optional[str] = None  # distinguimos "ausente" de null via model_fields_set

    _d = field_validator("due_date")(lambda cls, v: _clean_date(v))


def can_access_project(db, m, project_id: int) -> bool:
    if m["role"] == "master":
        return True
    return bool(db.execute(
        "SELECT 1 FROM project_visibilities WHERE project_id = ? AND membership_id = ?",
        (project_id, m["id"]),
    ).fetchone())


def can_create_task_in_project(db, m, project_id: int) -> bool:
    if m["role"] == "master":
        return True
    row = db.execute(
        "SELECT can_create_tasks FROM project_visibilities WHERE project_id = ? AND membership_id = ?",
        (project_id, m["id"]),
    ).fetchone()
    return bool(row and row["can_create_tasks"])


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


def set_visibility(db, project_id: int, granted_by: int, company_id: int, items_or_ids):
    items_to_set = []
    if items_or_ids:
        first = items_or_ids[0]
        if isinstance(first, int):
            valid_ids = valid_collaborator_ids(db, company_id, items_or_ids)
            items_to_set = [{"membership_id": mid, "can_create_tasks": False} for mid in valid_ids]
        else:
            raw_items = [
                i.model_dump() if hasattr(i, "model_dump") else (i.dict() if hasattr(i, "dict") else dict(i))
                for i in items_or_ids
            ]
            ids = [i["membership_id"] for i in raw_items]
            valid_ids = set(valid_collaborator_ids(db, company_id, ids))
            items_to_set = [
                {"membership_id": i["membership_id"], "can_create_tasks": bool(i.get("can_create_tasks", False))}
                for i in raw_items if i["membership_id"] in valid_ids
            ]

    db.execute("DELETE FROM project_visibilities WHERE project_id = ?", (project_id,))
    for it in items_to_set:
        db.execute(
            """INSERT INTO project_visibilities (project_id, membership_id, granted_by_membership_id, can_create_tasks)
               VALUES (?, ?, ?, ?)""",
            (project_id, it["membership_id"], granted_by, 1 if it["can_create_tasks"] else 0),
        )
    return [it["membership_id"] for it in items_to_set]


@app.get("/api/companies/{company_id}/projects")
def list_projects(company_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    if m["role"] == "master":
        rows = db.execute(
            "SELECT id, name, description, status, due_date FROM projects WHERE company_id = ? ORDER BY name",
            (company_id,),
        ).fetchall()
        return [{**dict(r), "can_create_tasks": True} for r in rows]
    else:
        rows = db.execute(
            """SELECT p.id, p.name, p.description, p.status, p.due_date, v.can_create_tasks FROM projects p
               JOIN project_visibilities v ON v.project_id = p.id
               WHERE p.company_id = ? AND v.membership_id = ? ORDER BY p.name""",
            (company_id, m["id"]),
        ).fetchall()
        return [{**dict(r), "can_create_tasks": bool(r["can_create_tasks"])} for r in rows]


@app.post("/api/companies/{company_id}/projects", status_code=201)
def create_project(company_id: int, data: ProjectIn, m=Depends(master_ctx), db=Depends(get_db)):
    cur = db.execute(
        """INSERT INTO projects (company_id, name, description, due_date, created_by_membership_id)
           VALUES (?, ?, ?, ?, ?)""",
        (company_id, data.name, data.description.strip(), data.due_date, m["id"]),
    )
    items = data.visibility_items if data.visibility_items else data.visible_to
    set_visibility(db, cur.lastrowid, m["id"], company_id, items)
    db.commit()
    p = db.execute(
        "SELECT id, name, description, status, due_date FROM projects WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return {**dict(p), "can_create_tasks": True}


@app.get("/api/companies/{company_id}/projects/{project_id}")
def get_project(company_id: int, project_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    p = get_project_or_404(db, company_id, project_id)
    if not can_access_project(db, m, project_id):
        raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
    data = {k: p[k] for k in ("id", "name", "description", "status", "due_date")}
    data["can_create_tasks"] = can_create_task_in_project(db, m, project_id)
    return data


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
    due_date = data.due_date if "due_date" in data.model_fields_set else p["due_date"]
    db.execute(
        "UPDATE projects SET name = ?, description = ?, status = ?, due_date = ? WHERE id = ?",
        (name, description, status, due_date, project_id),
    )
    db.commit()
    return {"id": project_id, "name": name, "description": description, "status": status, "due_date": due_date}


@app.get("/api/companies/{company_id}/projects/{project_id}/visibility")
def get_visibility(company_id: int, project_id: int, m=Depends(master_ctx), db=Depends(get_db)):
    get_project_or_404(db, company_id, project_id)
    rows = db.execute(
        "SELECT membership_id, can_create_tasks FROM project_visibilities WHERE project_id = ?", (project_id,)
    ).fetchall()
    return {
        "membership_ids": [r["membership_id"] for r in rows],
        "items": [{"membership_id": r["membership_id"], "can_create_tasks": bool(r["can_create_tasks"])} for r in rows],
    }


@app.put("/api/companies/{company_id}/projects/{project_id}/visibility")
def put_visibility(
    company_id: int, project_id: int, data: VisibilityIn,
    m=Depends(master_ctx), db=Depends(get_db),
):
    get_project_or_404(db, company_id, project_id)
    items = data.items if data.items is not None else (data.membership_ids or [])
    set_visibility(db, project_id, m["id"], company_id, items)
    db.commit()
    rows = db.execute(
        "SELECT membership_id, can_create_tasks FROM project_visibilities WHERE project_id = ?", (project_id,)
    ).fetchall()
    return {
        "membership_ids": [r["membership_id"] for r in rows],
        "items": [{"membership_id": r["membership_id"], "can_create_tasks": bool(r["can_create_tasks"])} for r in rows],
    }


@app.delete("/api/companies/{company_id}/projects/{project_id}")
def delete_project(
    company_id: int, project_id: int,
    m=Depends(master_ctx), db=Depends(get_db),
):
    get_project_or_404(db, company_id, project_id)
    db.execute("DELETE FROM projects WHERE id = ? AND company_id = ?", (project_id, company_id))
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Tarefas
# ---------------------------------------------------------------------------
class TaskIn(BaseModel):
    title: str
    description: str = ""
    priority: Priority = "medium"
    due_date: Optional[str] = None
    project_id: Optional[int] = None
    assignee_ids: list[int] = []

    _t = field_validator("title")(lambda cls, v: _clean_name(v, "O título", 2))


class TaskPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[str] = None
    project_id: Optional[int] = None  # distinguimos "ausente" de null via model_fields_set


class AssigneesIn(BaseModel):
    membership_ids: list[int]


class TaskOrderIn(BaseModel):
    status: Status
    task_ids: list[int]
    project_id: Optional[int] = None  # None = Tarefas Gerais


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
    if m["role"] == "master":
        return
    if task["project_id"] is not None:
        if not can_access_project(db, m, task["project_id"]):
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta tarefa.")
    else:
        # Tarefa Geral: visível apenas para quem criou ou quem está atribuído a ela
        if task["created_by_membership_id"] != m["id"] and not is_assignee(db, task["id"], m["id"]):
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
        p_row = db.execute(
            "SELECT name FROM projects WHERE id = ?", (t["project_id"],)
        ).fetchone()
        project_name = p_row["name"] if p_row else None
    t["assignees"] = [dict(a) for a in assignees]
    t["subtasks"] = [{**dict(s), "is_completed": bool(s["is_completed"])} for s in subtasks]
    t["created_by_name"] = creator["name"] if creator else None
    t["project_name"] = project_name
    return t


def touch_task(db, task_id: int):
    db.execute("UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))


def next_position(db, company_id: int, project_id: Optional[int], status: str) -> int:
    """Próxima posição (final da coluna) para o status dentro do escopo (Gerais ou projeto)."""
    row = db.execute(
        """SELECT COALESCE(MAX(position), 0) FROM tasks
           WHERE company_id = ? AND project_id IS ? AND status = ?""",
        (company_id, project_id, status),
    ).fetchone()
    return row[0] + 1


def list_scope_tasks(db, company_id: int, project_id: Optional[int], m=None) -> list[dict]:
    """Tarefas de um escopo:
    - Se project_id é especificado: tarefas daquele projeto específico.
    - Se project_id é None (Tarefas Gerais):
        - Para master: todas as tarefas da empresa (gerais e de qualquer projeto).
        - Para colaborador: tarefas gerais onde é criador/atribuído + tarefas dos projetos aos quais tem acesso.
    """
    if project_id is not None:
        rows = db.execute(
            "SELECT * FROM tasks WHERE company_id = ? AND project_id = ? ORDER BY position, id",
            (company_id, project_id),
        ).fetchall()
    else:
        if m and m["role"] != "master":
            rows = db.execute(
                """SELECT * FROM tasks
                   WHERE company_id = ? AND (
                       (
                           project_id IS NULL AND (
                               created_by_membership_id = ? OR
                               id IN (SELECT task_id FROM task_assignees WHERE membership_id = ?)
                           )
                       ) OR (
                           project_id IS NOT NULL AND
                           project_id IN (SELECT project_id FROM project_visibilities WHERE membership_id = ?)
                       )
                   )
                   ORDER BY position, id""",
                (company_id, m["id"], m["id"], m["id"]),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM tasks WHERE company_id = ? ORDER BY position, id",
                (company_id,),
            ).fetchall()
    return [serialize_task(db, r) for r in rows]


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
    """Sem project_id: mural de Tarefas Gerais (inclui tarefas de projetos com acesso). Com project_id: tarefas do projeto (se houver acesso)."""
    if project_id is not None:
        get_project_or_404(db, company_id, project_id)
        if not can_access_project(db, m, project_id):
            raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
    return list_scope_tasks(db, company_id, project_id, m=m)


@app.put("/api/companies/{company_id}/tasks/order")
def reorder_tasks(
    company_id: int, data: TaskOrderIn,
    m=Depends(member_ctx), db=Depends(get_db),
):
    """Define a ordem final de uma coluna do Kanban (Tarefas Gerais ou de um projeto).
    Tarefas vindas de outra coluna têm o status alterado, respeitando a mesma regra de permissão do PATCH."""
    if data.project_id is not None:
        get_project_or_404(db, company_id, data.project_id)
        if not can_access_project(db, m, data.project_id):
            raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
    ids = list(dict.fromkeys(data.task_ids))
    is_master = m["role"] == "master"
    changes = []
    for tid in ids:
        task = get_task_or_404(db, company_id, tid)
        if data.project_id is not None and task["project_id"] != data.project_id:
            raise HTTPException(status_code=400, detail="Tarefa não pertence a este quadro.")
        if data.project_id is None:
            if task["project_id"] is not None:
                if not can_access_project(db, m, task["project_id"]):
                    raise HTTPException(status_code=403, detail="Você não tem acesso ao projeto desta tarefa.")
            else:
                if not is_master and task["created_by_membership_id"] != m["id"] and not is_assignee(db, tid, m["id"]):
                    raise HTTPException(status_code=403, detail="Você não tem acesso a esta tarefa.")
        status_changed = task["status"] != data.status
        if status_changed and not is_master and not is_assignee(db, tid, m["id"]):
            raise HTTPException(status_code=403, detail="Você precisa estar atribuído à tarefa para alterar o status.")
        changes.append((tid, status_changed))
    for pos, (tid, status_changed) in enumerate(changes, start=1):
        if status_changed:
            db.execute(
                "UPDATE tasks SET status = ?, position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (data.status, pos, tid),
            )
        else:
            db.execute("UPDATE tasks SET position = ? WHERE id = ?", (pos, tid))
    db.commit()
    return list_scope_tasks(db, company_id, data.project_id, m=m)


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
        project_id = data.project_id
        if project_id is not None:
            project = get_project_or_404(db, company_id, project_id)
            if not can_access_project(db, m, project_id):
                raise HTTPException(status_code=403, detail="Você não tem acesso a este projeto.")
            if project["status"] == "archived":
                raise HTTPException(status_code=400, detail="Projeto arquivado não aceita novas tarefas.")
            if not can_create_task_in_project(db, m, project_id):
                raise HTTPException(status_code=403, detail="Você não tem permissão para criar tarefas neste projeto.")
            # Colaborador nunca pode atribuir a outro login. Pode apenas se auto-atribuir ou deixar livre para outros membros pegarem.
            assignees = [m["id"]] if (m["id"] in data.assignee_ids) else []
        else:
            # Tarefa Geral de colaborador é sempre pessoal
            assignees = [m["id"]]
    due_val = data.due_date.strip() if data.due_date and data.due_date.strip() else None
    cur = db.execute(
        """INSERT INTO tasks (company_id, project_id, title, description, priority, due_date, position, created_by_membership_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            company_id, project_id, data.title, data.description.strip(), data.priority, due_val,
            next_position(db, company_id, project_id, "todo"), m["id"],
        ),
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
    if "due_date" in fields:
        updates["due_date"] = data.due_date.strip() if data.due_date and data.due_date.strip() else None
    if "status" in fields and data.status is not None:
        updates["status"] = data.status  # sem trava de sub-tarefas em aberto
        if data.status != task["status"]:
            # Muda de coluna: vai para o final da coluna de destino
            target_project = data.project_id if "project_id" in fields else task["project_id"]
            updates["position"] = next_position(db, company_id, target_project, data.status)
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


@app.delete("/api/companies/{company_id}/tasks/{task_id}/claim")
def unclaim_task(company_id: int, task_id: int, m=Depends(member_ctx), db=Depends(get_db)):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    db.execute(
        "DELETE FROM task_assignees WHERE task_id = ? AND membership_id = ?",
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


@app.delete("/api/companies/{company_id}/tasks/{task_id}")
def delete_task(
    company_id: int, task_id: int,
    m=Depends(member_ctx), db=Depends(get_db),
):
    task = get_task_or_404(db, company_id, task_id)
    ensure_can_see_task(db, m, task)
    is_creator = task["created_by_membership_id"] == m["id"]
    is_master = m["role"] == "master"
    if not (is_creator or is_master):
        raise HTTPException(status_code=403, detail="Apenas o criador da tarefa ou um Master pode excluí-la.")

    db.execute("DELETE FROM task_assignees WHERE task_id = ?", (task_id,))
    db.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return {"ok": True, "message": "Tarefa e histórico excluídos com sucesso."}

