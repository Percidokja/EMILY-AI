from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates") # Necesitarás crear esta carpeta
client = Groq(api_key="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")

def leer_expediente():
    if os.path.exists("memoria_emily.txt"):
        with open("memoria_emily.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "Perci, el novato de Ferrari."

# --- INTERFAZ VISUAL ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>EMILY Terminal</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { background: #0f0f0f; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
                input { background: #1a1a1a; color: #fff; border: 1px solid #00ff00; width: 80%; padding: 10px; }
                button { background: #00ff00; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; }
                #chat { margin-top: 20px; border-top: 1px dashed #00ff00; padding-top: 10px; }
            </style>
        </head>
        <body>
            <h1>EMILY v1.0 - Acceso Perci</h1>
            <input type="text" id="pregunta" placeholder="Escribe aquí, novato...">
            <button onclick="enviar()">ENVIAR</button>
            <div id="chat"></div>
            <script>
                async function enviar() {
                    const q = document.getElementById('pregunta').value;
                    const res = await fetch('/preguntar', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pregunta: q})
                    });
                    const data = await res.json();
                    document.getElementById('chat').innerHTML += '<p><b>Tú:</b> ' + q + '</p>';
                    document.getElementById('chat').innerHTML += '<p><b>EMILY:</b> ' + data.emily_dice + '</p>';
                    document.getElementById('pregunta').value = '';
                }
            </script>
        </body>
    </html>
    """

# --- LÓGICA DE LA API ---
class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

@app.post("/preguntar")
def preguntar_emily(consulta: Consulta):
    contexto = leer_expediente()
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Eres EMILY, IA militar y tsundere. Usuario: Perci. Contexto: {contexto}. Sé ácida y eficiente."},
                {"role": "user", "content": consulta.pregunta}
            ],
            model="llama-3.3-70b-versatile"
        )
        return {"emily_dice": completion.choices[0].message.content}
    except Exception as e:
        return {"emily_dice": f"¡Error en la matriz! {e}"}
