from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from oci_factory.core.state import FactoryState
import os

app = FastAPI()

templates = Jinja2Templates(directory="oci_factory/web/templates")
STATE_FILE = "/home/ubuntu/oci-factory/state.json"

def get_current_state():
    """Função auxiliar para ler o estado de forma segura"""
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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Renderiza a carga inicial (Server Side Rendering)
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "state": get_current_state()
    })

@app.get("/api/status")
async def api_status():
    # Rota que o JavaScript vai chamar a cada X segundos
    return JSONResponse(content=get_current_state())