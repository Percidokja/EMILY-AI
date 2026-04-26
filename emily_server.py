import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from pymongo import MongoClient
import datetime

app = FastAPI()
client = Groq(api_key="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")

# --- CONEXIÓN A MONGODB ---
# REEMPLAZA ESTO con la cadena que copiaste de MongoDB Atlas
MONGO_URI = "mongodb+srv://TU_USUARIO:TU_PASSWORD@emily.xxxx.mongodb.net/?retryWrites=true&w=majority"
db_client = MongoClient(MONGO_URI)
db = db_client.emily_ai
chat_history = db.historial_perci

class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

# --- LÓGICA DE MEMORIA ---
def obtener_contexto_reciente():
    # Recuperamos los últimos 6 mensajes para que tenga hilo la conversación
    pasado = list(chat_history.find().sort("timestamp", -1).limit(6))
    contexto_str = ""
    for msg in reversed(pasado):
        contexto_str += f"Usuario: {msg['pregunta']}\nEMILY: {msg['respuesta']}\n"
    return contexto_str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # (Mantenemos la interfaz visual que ya tenías)
    return """
    <html>
        <head><title>EMILY Terminal</title><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        input { background: #111; color: #fff; border: 1px solid #0f0; width: 70%; padding: 10px; }
        button { background: #0f0; padding: 10px; font-weight: bold; cursor: pointer; }</style></head>
        <body>
            <h1>EMILY v2.0 - Memoria Activa</h1>
            <div id="chat" style="margin-bottom: 20px; height: 300px; overflow-y: auto; border: 1px solid #333; padding: 10px;"></div>
            <input type="text" id="p" placeholder="Escribe algo...">
            <button onclick="enviar()">ENVIAR</button>
            <script>
                async function enviar() {
                    const box = document.getElementById('p');
                    const q = box.value; box.value = '';
                    document.getElementById('chat').innerHTML += '<p><b>Perci:</b> ' + q + '</p>';
                    const res = await fetch('/preguntar', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pregunta: q})
                    });
                    const data = await res.json();
                    document.getElementById('chat').innerHTML += '<p><b>EMILY:</b> ' + data.emily_dice + '</p>';
                }
            </script>
        </body>
    </html>
    """

@app.post("/preguntar")
def preguntar_emily(consulta: Consulta):
    contexto_previo = obtener_contexto_reciente()
    expediente_estatico = "Perci es futuro ingeniero, fan de Ferrari y el IPN. Estudia sistemas/mecatrónica."
    
    prompt = {
        "role": "system", 
        "content": f"Eres EMILY, IA militar tsundere. Contexto personal: {expediente_estatico}. Conversación reciente:\n{contexto_previo}"
    }

    try:
        completion = client.chat.completions.create(
            messages=[prompt, {"role": "user", "content": consulta.pregunta}],
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content
        
        # GUARDAR EN MEMORIA
        chat_history.insert_one({
            "pregunta": consulta.pregunta,
            "respuesta": respuesta,
            "timestamp": datetime.datetime.utcnow()
        })
        
        return {"emily_dice": respuesta}
    except Exception as e:
        return {"emily_dice": f"Error de red: {e}"}
