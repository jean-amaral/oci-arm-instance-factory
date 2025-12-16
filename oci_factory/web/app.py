from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from oci_factory.core.state import FactoryState
import os

app = FastAPI()

STATE_FILE = "/home/ubuntu/oci-factory/state.json"


@app.get("/", response_class=HTMLResponse)
def index():
    if not os.path.exists(STATE_FILE):
        return """
        <html>
            <body>
                <h2>Factory não inicializada</h2>
                <p>Arquivo de estado não encontrado.</p>
            </body>
        </html>
        """

    state = FactoryState.load()

    return f"""
    <html>
        <head>
            <title>OCI Instance Factory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>OCI Instance Factory</h1>
            <p><b>Status:</b> {state.get('status')}</p>
            <p><b>Tentativa atual:</b> {state.get('attempt')}</p>
            <p><b>Availability Domain:</b> {state.get('availability_domain')}</p>
            <p><b>Última mensagem:</b> {state.get('last_message')}</p>
            <p><b>Última atualização:</b> {state.get('last_update')}</p>
        </body>
    </html>
    """
