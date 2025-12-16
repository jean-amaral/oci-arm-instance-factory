from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from oci_factory.core.state import FactoryState
import os
import subprocess
import logging

app = FastAPI()

templates = Jinja2Templates(directory="oci_factory/web/templates")
STATE_FILE = "/home/ubuntu/oci-factory/state.json"

def get_current_state():
    default_state = {
        "nodes": {},
        "logs": [],
        "last_update": "",
        "status": "Iniciando..."
    }
    if os.path.exists(STATE_FILE):
        try:
            loaded = FactoryState.load()
            if loaded:
                return loaded
        except:
            pass
    return default_state

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar comando: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "state": get_current_state()
    })

@app.get("/api/status")
async def api_status():
    return JSONResponse(content=get_current_state())

# --- ROTAS DE CONTROLE ---

@app.post("/api/control/restart")
async def restart_factory():
    success = run_command("sudo systemctl restart oci-factory.service")
    if success:
        return {"message": "Comando de reinício enviado com sucesso."}
    raise HTTPException(status_code=500, detail="Falha ao reiniciar o serviço.")

@app.post("/api/control/stop")
async def stop_factory():
    success = run_command("sudo systemctl stop oci-factory.service")
    if success:
        return {"message": "Comando de parada enviado com sucesso."}
    raise HTTPException(status_code=500, detail="Falha ao parar o serviço.")