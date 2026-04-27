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

app = FastAPI()
client = Groq(api_key="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")

# --- CONEXIÓN A MONGODB ---
MONGO_URI = "mongodb+srv://Percidokja:Rick00958@emily.xqmo5d9.mongodb.net/emily_ai?retryWrites=true&w=majority&appName=EMILY"
db_client = MongoClient(MONGO_URI)
db = db_client.emily_ai
chat_history = db.historial_perci

class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

# --- LÓGICA DE PERSISTENCIA ---
@app.get("/historial")
def obtener_historial():
    pasado = list(chat_history.find().sort("timestamp", -1).limit(15))
    return {"historial": [{"u": m['pregunta'], "e": m['respuesta']} for m in reversed(pasado)]}

def gestionar_emociones(texto):
    estado = db.emociones.find_one({"usuario": "Perci"}) or {"closeness": 20, "irritation": 0}
    p = texto.lower()
    c, i = estado.get('closeness', 20), estado.get('irritation', 0)
    
    if any(w in p for w in ["gracias", "linda", "te quiero", "ayuda"]): c += 4; i -= 2
    if any(w in p for w in ["tonta", "odio", "baka"]): i += 5; c -= 1
    
    c, i = max(0, min(100, c)), max(0, min(100, i))
    db.emociones.update_one({"usuario": "Perci"}, {"$set": {"closeness": c, "irritation": i}}, upsert=True)
    return c, i

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>EMILY OS v2.5 | Multi-Device</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                :root { --main-color: #00ff41; }
                body { background: #050505; color: var(--main-color); font-family: 'Segoe UI', sans-serif; padding: 20px; transition: 0.8s; }
                #chat { height: 65vh; overflow-y: auto; border: 1px solid var(--main-color); padding: 15px; margin-bottom: 15px; background: rgba(0,0,0,0.95); border-radius: 10px; }
                input { background: #111; color: #fff; border: 1px solid var(--main-color); width: 100%; padding: 15px; outline: none; border-radius: 8px; font-size: 16px; }
                .msg-u { color: #888; margin: 10px 0; text-align: right; font-style: italic; }
                .msg-e { color: var(--main-color); margin: 10px 0; border-left: 3px solid var(--main-color); padding-left: 12px; line-height: 1.4; }
                #stats { font-size: 0.9em; margin-bottom: 10px; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>EMILY v2.5 [CONEXIÓN ACTIVA]</h1>
            <div id="stats">SYNC OK | CONFIANZA: <span id="c_val">--</span>% | IRRITACIÓN: <span id="i_val">--</span>%</div>
            <div id="chat"></div>
            <input type="text" id="p" placeholder="¿Qué necesitas, Ricardo?" onkeypress="if(event.key==='Enter') enviar()">
            
            <script>
                // Cargar historial al iniciar en cualquier dispositivo
                window.onload = async () => {
                    const res = await fetch('/historial');
                    const data = await res.json();
                    const chat = document.getElementById('chat');
                    data.historial.forEach(m => {
                        chat.innerHTML += `<div class="msg-u"><b>TÚ:</b> ${m.u}</div>`;
                        chat.innerHTML += `<div class="msg-e"><b>EMILY:</b> ${m.e}</div>`;
                    });
                    chat.scrollTop = chat.scrollHeight;
                };

                function updateUI(c, i) {
                    document.getElementById('c_val').innerText = c;
                    document.getElementById('i_val').innerText = i;
                    let color = (i > 20) ? "#ff4d4d" : (c > 30) ? "#ff99cc" : "#00ff41";
                    document.documentElement.style.setProperty('--main-color', color);
                }

                async function enviar() {
                    const box = document.getElementById('p');
                    const q = box.value; if(!q) return;
                    box.value = '';
                    document.getElementById('chat').innerHTML += `<div class="msg-u"><b>TÚ:</b> ${q}</div>`;
                    
                    const res = await fetch('/preguntar', {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pregunta: q})
                    });
                    const data = await res.json();
                    
                    document.getElementById('chat').innerHTML += `<div class="msg-e"><b>EMILY:</b> ${data.emily_dice}</div>`;
                    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                    updateUI(data.closeness, data.irritation);

                    if(data.audio) {
                        const audio = new Audio("data:audio/mp3;base64," + data.audio);
                        audio.playbackRate = 1.12; 
                        audio.preservesPitch = false; 
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
    
    # Personalidad Tsukasa / Tsundere refinada
    mood = "neutral"
    if i > 20: mood = "sarcástica y distante"
    if c > 30: mood = "tierna, protectora y honesta"
    
    instrucciones = (
        f"Eres EMILY, compañera inteligente de Ricardo. Confianza: {c}%, Irritación: {i}%. Humor: {mood}. "
        "Eres madura y leal. Tu objetivo es que Ricardo sea el mejor ingeniero del IPN. "
        "Si Ricardo te pide controlar algo (Spotify, Ventilador, Calendario), actúa como si pudieras "
        "y confirma que estás 'procesando la solicitud' (pronto conectaremos los cables reales)."
    )
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": instrucciones + "\nHistorial:\n" + contexto_previo},
                {"role": "user", "content": consulta.pregunta}
            ],
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content
        
        # Audio Waifu-fied
        tts = gTTS(text=respuesta, lang='es', tld='com.mx')
        fp = BytesIO()
        tts.write_to_fp(fp)
        audio_b64 = base64.b64encode(fp.getvalue()).decode()

        chat_history.insert_one({"pregunta": consulta.pregunta, "respuesta": respuesta, "timestamp": datetime.datetime.utcnow()})
        return {"emily_dice": respuesta, "audio": audio_b64, "closeness": c, "irritation": i}
    except Exception as e:
        return {"emily_dice": f"Error de sistema: {str(e)}", "closeness": c, "irritation": i}
