import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from database import init_db, get_connection

init_db()

app = FastAPI(title="Gerenciador de Tarefas - API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmpresaCreate(BaseModel):
    nome: str
    documento: str

    @field_validator("nome")
    def validar_nome(cls, v: str):
        v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("O nome da empresa deve ter pelo menos 2 caracteres.")
        return v

    @field_validator("documento")
    def validar_documento(cls, v: str):
        limpo = re.sub(r"\D", "", v)
        if len(limpo) not in (11, 14):
            raise ValueError("Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos).")
        return v.strip()

@app.get("/api/empresas")
def listar_empresas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, documento, criado_em FROM empresas ORDER BY id DESC")
    rows = cursor.fetchall()
    empresas = [dict(row) for row in rows]
    conn.close()
    return empresas

@app.post("/api/empresas", status_code=201)
def criar_empresa(empresa: EmpresaCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO empresas (nome, documento) VALUES (?, ?)",
        (empresa.nome, empresa.documento)
    )
    novo_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT id, nome, documento, criado_em FROM empresas WHERE id = ?", (novo_id,))
    nova_empresa = dict(cursor.fetchone())
    conn.close()
    return nova_empresa

@app.get("/api/empresas/{empresa_id}")
def obter_empresa(empresa_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, documento, criado_em FROM empresas WHERE id = ?", (empresa_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return dict(row)

@app.delete("/api/empresas/{empresa_id}", status_code=204)
def excluir_empresa(empresa_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    conn.commit()
    conn.close()
    return None
