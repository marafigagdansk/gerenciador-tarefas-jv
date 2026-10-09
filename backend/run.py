import os
import uvicorn
from dotenv import load_dotenv

# Carrega o .env da raiz do projeto ou da pasta backend
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

host = os.getenv("BACKEND_HOST", "127.0.0.1")
port = int(os.getenv("BACKEND_PORT", "8000"))

if __name__ == "__main__":
    print(f"🚀 Iniciando servidor backend em http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
