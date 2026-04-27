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
                --main-color: #00ff41; /* Verde base */
                --bg-color: #0a0a0a;
                --text-u: #e0e0e0;
                --text-e: #ffffff;
                --shadow: 0 4px 15px rgba(0,0,0,0.5);
                transition: --main-color 0.8s, --bg-color 0.8s;
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

            /* --- DASHBOARD HEADER --- */
            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 25px;
                background: rgba(10,10,10,0.8);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255,255,255,0.05);
                box-shadow: var(--shadow);
                z-index: 10;
            }
            h1 { font-size: 1.1em; font-weight: 700; letter-spacing: 2px; color: var(--main-color); }
            #stats { display: flex; gap: 20px; font-size: 0.85em; }
            .stat-card { background: rgba(255,255,255,0.03); padding: 5px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }
            .stat-val { color: var(--main-color); font-weight: bold; }

            /* --- CHAT AREA --- */
            #chat { 
                flex: 1; 
                overflow-y: auto; 
                padding: 25px;
                scroll-behavior: smooth;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            #chat::-webkit-scrollbar { width: 6px; }
            #chat::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }

            .bubble { max-width: 80%; padding: 12px 18px; border-radius: 12px; font-size: 0.95em; line-height: 1.5; position: relative; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
            
            /* Mensaje de Usuario (Ricardo) */
            .msg-u-container { display: flex; justify-content: flex-end; }
            .bubble-u { 
                background: rgba(255,255,255,0.05);
                color: var(--text-u); 
                border-bottom-right-radius: 4px;
            }
            .bubble-u::before { content: 'R'; position: absolute; right: -15px; bottom: 0; font-size: 0.7em; color: #555; }

            /* Mensaje de EMILY */
            .msg-e-container { display: flex; justify-content: flex-start; }
            .bubble-e { 
                background: linear-gradient(135deg, rgba(0,255,65,0.1) 0%, rgba(0,255,65,0.02) 100%);
                color: var(--text-e); 
                border: 1px solid rgba(0,255,65,0.1);
                border-bottom-left-radius: 4px;
            }
            .bubble-e::before { content: 'E'; position: absolute; left: -15px; bottom: 0; font-size: 0.7em; color: var(--main-color); }

            /* --- INPUT AREA --- */
            #input-area {
                padding: 15px 25px;
                background: rgba(10,10,10,0.8);
                backdrop-filter: blur(10px);
                border-top: 1px solid rgba(255,255,255,0.05);
                box-shadow: 0 -4px 15px rgba(0,0,0,0.3);
            }
            input { 
                width: 100%; 
                padding: 14px 20px; 
                background: rgba(255,255,255,0.02);
                color: #fff; 
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px; 
                font-size: 16px; 
                outline: none; 
                transition: border 0.3s, background 0.3s;
            }
            input:focus { border-color: var(--main-color); background: rgba(255,255,255,0.04); }

        </style>
    </head>
    <body>
        <header>
            <h1>EMILY OS v3.0</h1>
            <div id="stats">
                <div class="stat-card">Confianza: <span id="c_val" class="stat-val">--</span>%</div>
                <div class="stat-card">Irritación: <span id="i_val" class="stat-val">--</span>%</div>
            </div>
        </header>
        
        <div id="chat">
            </div>
        
        <div id="input-area">
            <input type="text" id="p" placeholder="¿Cómo puedo ayudarte hoy, Ricardo?" onkeypress="if(event.key==='Enter') enviar()">
        </div>
        
        <script>
            // LÓGICA DE HISTORIAL PERSISTENTE
            window.onload = async () => {
                try {
                    const res = await fetch('/historial');
                    const data = await res.json();
                    const chat = document.getElementById('chat');
                    data.historial.forEach(m => {
                        appendMessage(m.u, 'u');
                        appendMessage(m.e, 'e');
                    });
                    chat.scrollTop = chat.scrollHeight;
                } catch(e) { console.error("Error cargando historial", e); }
            };

            // Función única para pintar mensajes estéticos
            function appendMessage(text, type) {
                const chat = document.getElementById('chat');
                const container = document.createElement('div');
                container.className = `msg-${type}-container`;
                
                const bubble = document.createElement('div');
                bubble.className = `bubble bubble-${type}`;
                bubble.innerText = text;
                
                container.appendChild(bubble);
                chat.appendChild(container);
                chat.scrollTop = chat.scrollHeight;
            }

            function updateUI(c, i) {
                document.getElementById('c_val').innerText = c;
                document.getElementById('i_val').innerText = i;
                
                // --- LÓGICA DE WAIFU-FICACTION DE COLORES ---
                let mainColor = "#00ff41"; // Verde base
                let bgColor = "#0a0a0a"; // Fondo oscuro

                if (i > 25) { // Enojada / Tsunderefied
                    mainColor = "#ff4d4d"; // Rojo F1
                    bgColor = "#150a0a"; // Fondo ligeramente rojizo
                } else if (c > 30) { // Tierna / Tsukasa-vibe
                    mainColor = "#ff99cc"; // Rosa pastel
                    bgColor = "#120a15"; // Fondo ligeramente púrpura
                }
                
                document.documentElement.style.setProperty('--main-color', mainColor);
                document.documentElement.style.setProperty('--bg-color', bgColor);
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
                    audio.playbackRate = 1.12; 
                    audio.preservesPitch = false; 
                    audio.play();
                }
            }
        </script>
    </body>
    </html>
    """
