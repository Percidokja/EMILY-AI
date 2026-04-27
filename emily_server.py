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

# 2. FUNCIONES DE APOYO
def obtener_contexto_reciente():
    pasado = list(chat_history.find().sort("timestamp", -1).limit(5))
    contexto = ""
    for msg in reversed(pasado):
        contexto += f"Usuario: {msg['pregunta']}\nEMILY: {msg['respuesta']}\n"
    return contexto

def gestionar_emociones(texto):
    estado = db.emociones.find_one({"usuario": "Perci"}) or {"closeness": 20, "irritation": 0}
    p = texto.lower()
    c = estado.get('closeness', 20)
    i = estado.get('irritation', 0)
    
    if any(w in p for w in ["gracias", "linda", "te quiero", "ayuda"]): 
        c += 4
        i -= 2
    if any(w in p for w in ["tonta", "odio", "baka", "estúpida"]): 
        i += 5
        c -= 1
    
    c = max(0, min(100, c))
    i = max(0, min(100, i))
    
    db.emociones.update_one({"usuario": "Perci"}, {"$set": {"closeness": c, "irritation": i}}, upsert=True)
    return c, i

# 3. RUTAS
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
        <title>EMILY OS v3.0</title>
        <link href="https://cdn.jsdelivr.net/npm/inter-ui@3.19.3/inter.min.css" rel="stylesheet">
        <style>
            :root { --main-color: #00ff41; --bg-color: #0a0a0a; transition: all 0.8s ease; }
            body { background: linear-gradient(135deg, var(--bg-color) 0%, #151515 100%); color: #fff; font-family: 'Inter', sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; margin: 0; }
            header { display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background: rgba(10,10,10,0.8); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,0.05); }
            .stat-card { background: rgba(255,255,255,0.03); padding: 5px 12px; border-radius: 6px; font-size: 0.8em; }
            #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
            .bubble { max-width: 85%; padding: 12px 16px; border-radius: 15px; font-size: 0.95em; }
            .msg-u-container { display: flex; justify-content: flex-end; }
            .bubble-u { background: rgba(255,255,255,0.07); border-bottom-right-radius: 4px; }
            .msg-e-container { display: flex; justify-content: flex-start; }
            .bubble-e { background: rgba(0,255,65,0.05); border: 1px solid rgba(0,255,65,0.2); border-bottom-left-radius: 4px; }
            #input-area { padding: 20px; background: rgba(10,10,10,0.9); }
            input { width: 100%; padding: 15px; background: #111; color: #fff; border: 1px solid #333; border-radius: 10px; outline: none; }
        </style>
    </head>
    <body>
        <header>
            <h1 style="font-size:1.1em; color:var(--main-color)">EMILY OS v3.0</h1>
            <div style="display:flex; gap:10px">
                <div class="stat-card">Confianza: <span id="c_val">--</span>%</div>
                <div class="stat-card">Irritación: <span id="i_val">--</span>%</div>
            </div>
        </header>
        <div id="chat"></div>
        <div id="input-area"><input type="text" id="p" placeholder="Escribe aquí..." onkeypress="if(event.key==='Enter') enviar()"></div>
        <script>
            window.onload = async () => {
                const res = await fetch('/historial');
                const data = await res.json();
                data.historial.forEach(m => { appendMessage(m.u, 'u'); appendMessage(m.e, 'e'); });
            };
            function appendMessage(t, type) {
                const chat = document.getElementById('chat');
                const div = document.createElement('div');
                div.className = `msg-${type}-container`;
                div.innerHTML = `<div class="bubble bubble-${type}">${t}</div>`;
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
                const res = await fetch('/preguntar', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pregunta: q})
                });
                const data = await res.json();
                appendMessage(data.emily_dice, 'e');
                updateUI(data.closeness, data.irritation);
                if(data.audio) {
                    const audio = new Audio("data:audio/mp3;base64," + data.audio);
                    audio.playbackRate = 1.15;
                    audio.play();
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/preguntar")
def preguntar_emily(consulta: Consulta):
    contexto_previo = obtener_contexto_reciente()
    c, i = gestionar_emociones(consulta.pregunta)
    mood = "neutral"
    if i > 25: mood = "molesta"
    if c > 35: mood = "cariñosa"

    prompt = f"Eres EMILY, IA de Ricardo. Confianza: {c}%, Irritación: {i}%. Humor: {mood}. Sé breve y con personalidad tsundere/madura."
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt + "\nHistorial:\n" + contexto_previo},
                {"role": "user", "content": consulta.pregunta}
            ],
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content
        tts = gTTS(text=respuesta, lang='es', tld='com.mx')
        fp = BytesIO()
        tts.write_to_fp(fp)
        audio_b64 = base64.b64encode(fp.getvalue()).decode()
        chat_history.insert_one({"pregunta": consulta.pregunta, "respuesta": respuesta, "timestamp": datetime.datetime.utcnow()})
        return {"emily_dice": respuesta, "audio": audio_b64, "closeness": c, "irritation": i}
    except Exception as e:
        return {"emily_dice": f"Error: {str(e)}", "closeness": c, "irritation": i}
