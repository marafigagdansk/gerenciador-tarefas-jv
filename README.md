# Gerenciador de Tarefas

Aplicação leve e de alta performance com banco de dados SQLite interno, backend em Python (FastAPI) e frontend em Vite + Vue.js 3.

---

## ⚙️ Configuração de Portas e Ambiente (.env)

O arquivo `.env` na raiz do projeto permite configurar as portas do backend e do frontend:

```env
# Configurações do Backend (Python)
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Configurações do Frontend (Vite)
FRONTEND_PORT=5173
VITE_API_URL=http://127.0.0.1:8000
```

---

## 🚀 Como Executar

### 1. Backend (Python)
No diretório `backend`:
```bash
cd backend
pip install -r requirements.txt
python run.py
```
*O `run.py` carregará automaticamente o `BACKEND_PORT` e `BACKEND_HOST` definidos no `.env`.*

### 2. Frontend (Vite + Vue 3)
No diretório `frontend`:
```bash
cd frontend
npm install
npm run dev
```
*O Vite lerá automaticamente a `FRONTEND_PORT` e direcionará o proxy para a porta do backend configurada no `.env`.*
