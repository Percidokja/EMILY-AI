import os
import datetime
import base64
from io import BytesIO
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from pymongo import MongoClient
from gtts import gTTS

# 1. CONFIGURACIÓN DE APP Y CLIENTES
app = FastAPI()
client = Groq(api_key="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")

# Conexión a MongoDB
MONGO_URI = "mongodb+srv://Percidokja:Rick00958@emily.xqmo5d9.mongodb.net/emily_ai?retryWrites=true&w=majority&appName=EMILY"
db_client = MongoClient(MONGO_URI)
db = db_client.emily_ai
chat_history = db.historial_perci

class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

# 2. FUNCIONES DE APOYO (Lógica del Cerebro)
def obtener_contexto_reciente():
    pasado = list(chat_history.find().sort("timestamp", -1).limit(5))
    contexto = ""
    for msg in reversed(pasado):
        contexto += f"Usuario: {msg['pregunta']}\nEMILY: {msg['respuesta']}\n"
    return contexto

def gestionar_emociones(texto):
    # Intentar obtener estado actual o crear uno
    estado = db.emociones.find_one({"usuario": "Perci"}) or {"closeness": 20, "irritation": 0}
    p = texto.lower()
    c = estado.get('closeness', 20)
    i = estado.get('irritation', 0)
    
    # Lógica de cambio emocional
    if any(w in p for w in ["gracias", "linda", "te quiero", "ayuda"]): 
        c += 4
        i -= 2
    if any(w in p for w in ["tonta", "odio", "baka", "estúpida"]): 
        i += 5
        c -= 1
    
    # Límites
    c = max(0, min(100, c))
    i = max(0, min(100, i))
    
    db.emociones.update_one({"usuario": "Perci"}, {"$set": {"closeness": c, "irritation": i}}, upsert=True)
    return c, i

# 3. RUTAS DEL SERVIDOR
@app.get("/historial")
def obtener_historial():
    pasado = list(chat_history.find().sort("timestamp", -1).limit(15))
    return {"historial": [{"u": m['pregunta'], "e": m['respuesta']} for m in reversed(pasado)]}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>EMILY OS v3.0 | Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/inter-ui@3.19.3/inter.min.css" rel="stylesheet">
        <style>
            :root {
                --main-color: #00ff41;
                --bg-color: #0a0a0a;
                --text-u: #e0e0e0;
                --text-e: #ffffff;
                --shadow: 0 4px 15px rgba(0,0,0,0.5);
                transition: all 0.8s ease;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { 
                background: linear-gradient(135deg, var(--bg-color) 0%, #151515 100%);
                color: var(--text-e); 
                font-family: 'Inter', sans-serif; 
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 25px;
                background: rgba(10,10,10,0.8);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255,255,255,0.05);
                z-index: 10;
            }
            h1 { font-size: 1.1em; letter-spacing: 2px; color: var(--main-color); }
            #stats { display: flex; gap: 15px; }
            .stat-card { background: rgba(255,255,255,0.03); padding: 5px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); font-size: 0.8em; }
            .stat-val { color: var(--main-color); font-weight: bold; }
            #chat { 
                flex: 1; 
                overflow-y: auto; 
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .bubble { max-width: 85%; padding: 12px 16px; border-radius: 15px; font-size: 0.95em; line-height: 1.5; position: relative; }
            .msg-u-container { display: flex; justify-content: flex-end; }
            .bubble-u { background: rgba(255,255,255,0.07); color: var(--text-u); border-bottom-right-radius: 4px; }
            .msg-e-container { display: flex; justify-content: flex-start; }
            .bubble-e { background: rgba(0,255,65,0.05); border: 1px solid rgba(0,255,65,0.2); border-bottom-left-radius: 4px; }
            #input-area { padding: 20px; background: rgba(10,10,10,0.9); border-top: 1px solid rgba(255,255,255,0.05); }
            input { width: 100%; padding: 15px; background: #111; color: #fff; border: 1px solid #333; border-radius: 10px; outline: none; }
            input:focus { border-color: var(--main-color); }
        </style>
    </head>
    <body>
        <header>
            <h1>EMILY OS v3.0</h1>
            <div id="stats">
                <div class="stat-card">Trust: <span id="c_val" class="stat-val">--</span>%</div>
                <div class="stat-card">Irrit: <span id="i_val" class="stat-val">--</span>%</div>
            </div>
        </header>
        <div id="chat"></div>
        <div id="input-area">
            <input type="text" id="p" placeholder="Escribe a EMILY..." onkeypress="if(event.key==='Enter') enviar()">
        </div>
        <script>
            window.onload = async () => {
                const res = await fetch('/historial');
                const data = await res.json();
                data.historial.forEach(m => {
                    appendMessage(m.u, 'u');
                    appendMessage(m.e, 'e');
                });
            };

            function appendMessage(text, type) {
                const chat = document.getElementById('chat');
                const div = document.createElement('div');
                div.className = `msg-${type}-container`;
                div.innerHTML = `<div class="bubble bubble-${type}">${text}</div>`;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            function updateUI(c, i) {
                document.getElementById('c_val').innerText = c;
                document.getElementById('i_val').innerText = i;
                let color = i > 25 ? "#ff4d4d" : c > 30 ? "#ff99cc" : "#00ff41";
                document.documentElement.style.setProperty('--main-color', color);
            }

            async function enviar() {
                const box = document.getElementById('p');
                const q = box.value; if(!q) return;
                box.value = '';
                appendMessage(q, 'u');
