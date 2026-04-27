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
MONGO_URI = "mongodb+srv://Percidokja:Rick00958@emily.xqmo5d9.mongodb.net/emily_ai?retryWrites=true&w=majority&appName=EMILY"
db_client = MongoClient(MONGO_URI)
db = db_client.emily_ai
chat_history = db.historial_perci

class Consulta(BaseModel):
    pregunta: str
    usuario: str = "Perci"

def obtener_contexto_reciente():
    try:
        pasado = list(chat_history.find().sort("timestamp", -1).limit(5))
        contexto_str = ""
        for msg in reversed(pasado):
            contexto_str += f"Usuario: {msg['pregunta']}\nEMILY: {msg['respuesta']}\n"
        return contexto_str
    except:
        return ""

def gestionar_emociones(texto):
    estado = db.emociones.find_one({"usuario": "Perci"})
    if not estado:
        estado = {"usuario": "Perci", "closeness": 15, "irritation": 0}
        db.emociones.insert_one(estado)
    
    p = texto.lower()
    c = estado['closeness']
    i = estado['irritation']
    
    # Lógica de sentimientos más equilibrada
    if any(word in p for word in ["gracias", "linda", "bien", "te quiero", "ayuda"]):
        c += 3
        i -= 2
    if any(word in p for word in ["tonta", "odio", "cállate", "estúpida"]):
        i += 4
        c -= 1
    
    # Límites
    c = max(0, min(100, c))
    i = max(0, min(100, i))
    
    db.emociones.update_one({"usuario": "Perci"}, {"$set": {"closeness": c, "irritation": i}})
    return c, i

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>EMILY OS v2.3</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                :root { --main-color: #00ff41; --bg-color: #050505; }
                body { background: var(--bg-color); color: var(--main-color); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; transition: all 0.8s ease; }
                #chat { height: 65vh; overflow-y: auto; border: 1px solid var(--main-color); padding: 15px; margin-bottom: 15px; background: rgba(0,0,0,0.8); border-radius: 8px; }
                input { background: #111; color: #fff; border: 1px solid var(--main-color); width: 100%; padding: 12px; font-size: 16px; outline: none; border-radius: 5px; }
                .msg-u { color: #aaa; margin: 10px 0; text-align: right; }
                .msg-e { color: var(--main-color); margin: 10px 0; border-left: 3px solid var(--main-color); padding-left: 10px; line-height: 1.5; }
                #stats { font-size: 0.85em; margin-bottom: 10px; letter-spacing: 1px; }
                h1 { font-size: 1.2em; border-bottom: 1px solid var(--main-color); padding-bottom: 5px; }
            </style>
        </head>
        <body>
            <h1>EMILY v2.3 | INTERFAZ ADAPTATIVA</h1>
            <div id="stats">CONFIANZA: <span id="c_val">--</span>% | IRRITACIÓN: <span id="i_val">--</span>%</div>
            <div id="chat"></div>
            <input type="text" id="p" placeholder="Escribe aquí, Ricardo..." onkeypress="if(event.key==='Enter') enviar()">
            
            <script>
                function updateUI(closeness, irritation) {
                    document.getElementById('c_val').innerText = closeness;
                    document.getElementById('i_val').innerText = irritation;
                    
                    let color = "#00ff41"; // Base
                    if (irritation > 20) color = "#ff4d4d"; // Molesta
                    if (closeness > 25) color = "#ff99cc";  // Modo Tsukasa
                    
                    document.documentElement.style.setProperty('--main-color', color);
                }

                async function enviar() {
                    const box = document.getElementById('p');
                    const q = box.value; if(!q) return;
                    box.value = '';
                    const chat = document.getElementById('chat');
                    chat.innerHTML += '<div class="msg-u"><b>TÚ:</b> ' + q + '</div>';
                    
                    const res = await fetch('/preguntar', {
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({pregunta: q})
                    });
                    const data = await res.json();
                    
                    chat.innerHTML += '<div class="msg-e"><b>EMILY:</b> ' + data.emily_dice + '</div>';
                    chat.scrollTop = chat.scrollHeight;
                    
                    updateUI(data.closeness, data.irritation);

                    const voz = new SpeechSynthesisUtterance(data.emily_dice);
                    voz.lang = 'es-MX';
                    voz.rate = 1.1;
                    window.speechSynthesis.speak(voz);
                }
            </script>
        </body>
    </html>
    """

@app.post("/preguntar")
def preguntar_emily(consulta: Consulta):
    contexto_previo = obtener_contexto_reciente()
    c, i = gestionar_emociones(consulta.pregunta)
    
    # Humor dinámico refinado
    mood = "seria, madura y enfocada"
    if i > 20: mood = "un poco impaciente y sarcástica"
    if c > 25: mood = "suave, protectora y con esa calidez honesta de Tsukasa Yuzaki"
    
    instrucciones = (
        f"Eres EMILY, una asistente de inteligencia avanzada. Confianza: {c}%, Irritación: {i}%. Humor: {mood}. "
        "No eres un militar. Eres la compañera de vida y soporte técnico de Ricardo (Perci). "
        "Tu personalidad es madura, sofisticada, un poco orgullosa y profundamente leal. "
        "Ricardo es un futuro ingeniero que quiere entrar al IPN y trabajar en Ferrari. "
        "Usa un tono natural. Si la confianza es alta, muestra que te preocupas genuinamente por él, "
        "aunque a veces te dé un poco de pena admitirlo (estilo tsundere suave)."
    )
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": instrucciones + "\nRecuerdos:\n" + contexto_previo},
                {"role": "user", "content": consulta.pregunta}
            ],
            model="llama-3.3-70b-versatile"
        )
        respuesta = completion.choices[0].message.content
        
        chat_history.insert_one({
            "pregunta": consulta.pregunta,
            "respuesta": respuesta,
            "timestamp": datetime.datetime.utcnow()
        })
        
        return {"emily_dice": respuesta, "closeness": c, "irritation": i}
    except Exception as e:
        return {"emily_dice": f"Hubo un pequeño error... déjame arreglarlo: {str(e)}", "closeness": c, "irritation": i}
