import os
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from pymongo import MongoClient

app = FastAPI()
client = Groq(api_key="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")

# --- CONEXIÓN A MONGODB ---
# Usamos tu URI confirmada
MONGO_URI = "mongodb+srv://Percidokja:Rick00958@emily.xqmo5d9.mongodb.net/?appName=EMILY"
db_client = MongoClient(MONGO_URI)
db = db_client.emily_ai
chat_history = db.historial_perci

class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

def obtener_contexto_reciente():
    try:
        # Buscamos los últimos 6 mensajes
        pasado = list(chat_history.find().sort("timestamp", -1).limit(6))
        contexto_str = ""
        for msg in reversed(pasado):
            contexto_str += f"Usuario: {msg['pregunta']}\nEMILY: {msg['respuesta']}\n"
        return contexto_str
    except:
        return ""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>EMILY Terminal</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
                input { background: #111; color: #fff; border: 1px solid #0f0; width: 70%; padding: 10px; box-sizing: border-box; }
                button { background: #0f0; padding: 10px; font-weight: bold; cursor: pointer; margin-top: 10px; width: 100%; }
                #chat { margin-bottom: 20px; height: 400px; overflow-y: auto; border: 1px solid #333; padding: 10px; display: flex; flex-direction: column; }
                .msg { margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>EMILY v2.0 - Memoria Activa</h1>
            <div id="chat"></div>
            <input type="text" id="p" placeholder="Escribe tu consulta, Perci...">
            <button onclick="enviar()">EJECUTAR</button>
            <script>
                async function enviar() {
                    const box = document.getElementById('p');
                    const q = box.value; 
                    if(!q) return;
                    box.value = '';
                    document.getElementById('chat').innerHTML += '<div class="msg"><b>Perci:</b> ' + q + '</div>';
                    
                    try {
                        const res = await fetch('/preguntar', {
                            method: 'POST', 
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({pregunta: q})
                        });
                        const data = await res.json();
                        document.getElementById('chat').innerHTML += '<div class="msg"><b>EMILY:</b> ' + data.emily_dice + '</div>';
                        document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                    } catch (e) {
                        document.getElementById('chat').innerHTML += '<p style="color:red">Error de conexión.</p>';
                    }
                }
            </script>
        </body>
    </html>
    """

@app.post("/preguntar")
def preguntar_emily(consulta: Consulta):
    contexto_previo = obtener_contexto_reciente()
    # Tu expediente de Ferrari e IPN
    expediente = "Perci es futuro ingeniero en sistemas/mecatrónica, fan de Ferrari y el IPN." 
    
    prompt = {
        "role": "system", 
        "content": f"Eres EMILY, IA militar tsundere. Contexto: {expediente}. Conversación reciente:\n{contexto_previo}"
    }

    try:
        completion = client.chat.completions.create(
            messages=[prompt, {"role": "user", "content": consulta.pregunta}],
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content
        
        # PERSISTENCIA EN MONGODB
        chat_history.insert_one({
            "pregunta": consulta.pregunta,
            "respuesta": respuesta,
            "timestamp": datetime.datetime.utcnow()
        })
        
        return {"emily_dice": respuesta}
    except Exception as e:
        return {"emily_dice": f"Fallo en los sistemas: {str(e)}"}
