#!/usr/bin/env python3
"""
Web Interface - Sistema Completo de Análise de Sentimentos YouTube
Porta: 8083
Interface web com 4 telas funcionais
"""

from flask import Flask, request, jsonify, send_from_directory, send_file, redirect
import requests
import json
import os
import time
import logging
import threading
import uuid
from datetime import datetime
import re

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
DASHBOARD_SERVICE_URL = "http://localhost:8081"
JOBS_STORAGE = {}  # Armazenamento em memória dos jobs
STATIC_DIR = "/opt/yt/static"
os.makedirs(STATIC_DIR, exist_ok=True)

def is_valid_youtube_url(url):
    """Valida se a URL é do YouTube"""
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'^https?://youtu\.be/([a-zA-Z0-9_-]+)',
        r'^https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
    ]
    return any(re.match(pattern, url) for pattern in patterns)

def process_analysis_async(job_id, video_url):
    """Processa análise em background"""
    try:
        logger.info(f"Iniciando análise para job {job_id}")
        
        # Atualizar status
        JOBS_STORAGE[job_id].update({
            'status': 'collecting',
            'progress': 20,
            'message': 'Coletando comentários do YouTube...'
        })
        
        time.sleep(2)  # Simular tempo de coleta
        
        # Chamar dashboard service
        JOBS_STORAGE[job_id].update({
            'status': 'analyzing', 
            'progress': 50,
            'message': 'Classificando comentários com IA...'
        })
        
        response = requests.post(
            f"{DASHBOARD_SERVICE_URL}/generate",
            json={'video_url': video_url},
            timeout=1800
        )
        
        if response.status_code == 200:
            result = response.json()
            
            JOBS_STORAGE[job_id].update({
                'status': 'generating',
                'progress': 80,
                'message': 'Gerando dashboard...'
            })
            
            time.sleep(2)
            
            JOBS_STORAGE[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Análise concluída!',
                'dashboard_id': result.get('job_id'),
                'download_url': f"/download-dashboard/{result.get('job_id')}",
                'file_size': result.get('file_size_kb', 0)
            })
            
            logger.info(f"Análise {job_id} concluída com sucesso")
            
        else:
            raise Exception(f"Erro no dashboard service: {response.text}")
            
    except Exception as e:
        logger.error(f"Erro na análise {job_id}: {str(e)}")
        JOBS_STORAGE[job_id].update({
            'status': 'error',
            'progress': 0,
            'message': 'Erro no processamento',
            'error': str(e)
        })

# Rotas para servir arquivos estáticos
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/')
def index():
    """Página inicial - index.html"""
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Página Inicial</title>
  <style>
/* ================= VARIÁVEIS ================= */
:root {
  --sz: 23px;
  --c1: #350909;
  --c2: #410202;
  --c3: #160000;
  --c4: #210606;

  --ts: 50%/ calc(var(--sz) * 5.5) calc(var(--sz) * 9.5);
  --b1: conic-gradient(from 180deg at 16% 73.5%, var(--c2) 0 120deg, transparent 0 100%) var(--ts);
  --b2: conic-gradient(from 180deg at 39.5% 65.65%, var(--c3) 0 60deg, var(--c1) 0 120deg, transparent 0 100%) var(--ts);

  --video-size: 250px;
  --pattern-opacity: 0.15;
}

html, body {
  height: 100%;
  margin: 0;
}

body {
  position: relative;
  isolation: isolate;
  font-family: "Inter", sans-serif;
  color: #eee;

  /* fundo principal = preto + vermelho vindo de baixo */
  background: linear-gradient(to top, rgb(65 3 3) 0%, #000 45%);
  overflow: hidden;
}

/* overlay do padrão geométrico */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: var(--pattern-opacity);

  background:
    var(--b1), var(--b1), var(--b1), var(--b1),
    var(--b2), var(--b2), var(--b2), var(--b2),
    conic-gradient(from 0deg at 92.66% 50%, var(--c2) 0 120deg, transparent 0 100%) var(--ts),
    conic-gradient(from -60deg at 81.66% 10.25%, var(--c2) 0 180deg, transparent 0 100%) var(--ts),
    conic-gradient(from -60deg at 66.66% 22.25%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
    conic-gradient(from 0deg at 71.66% 43%, var(--c3) 0 120deg, transparent 0 100%) var(--ts),
    conic-gradient(from 0deg at 66.66% 45.95%, var(--c3) 0 60deg, transparent 0 100%) var(--ts),
    conic-gradient(from 120deg at 25% 91.5%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
    conic-gradient(from 60deg at 50% 51.5%, var(--c1) 0 60deg, var(--c2) 0 120deg, var(--c4) 0 100%) var(--ts);

  background-repeat: repeat;
}

/* ================= LAYOUT ================= */
.container{
  position: relative;
  z-index: 1;               /* acima do padrão (::before) */
  max-width: 760px;
  margin: 0 auto;
  text-align: center;
  padding: 150px 20px 64px;
}

/* linha fina com brilho discreto */
.line{
  width: 82%;
  height: 1px;
  margin: 24px auto 18px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.45), transparent);
  border-radius: 1px;
}

/* título estilo cinza → branco */
h1{
  font-size: clamp(2.2rem, 3.2vw + 1rem, 3.2rem);
  font-weight: 300;
  letter-spacing: -0.5px;
  margin: 0 0 14px;
  background: linear-gradient(90deg, #a9a9a9, #e9e9e9 55%, #ffffff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
h1 span{
  font-weight: 600;
  background: linear-gradient(90deg, #bdbdbd, #ececec);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* subtítulo */
.sub{
  font-size: 1rem;
  line-height: 1.55;
  color: rgba(230,230,230,.72);
  font-weight:300;
  margin: 2px 0 36px;
}
.sub span{
  font-weight: 500;
  color: #e6e6e6;
}

/* vídeo com alpha */
.video-container{
  display:flex;
  justify-content:center;
  margin: 10px 0 28px;
}
.video-container video{
  width: var(--video-size);
  height: var(--video-size);
  pointer-events:none;
}

/* input glassmorphism */
.input-wrapper{
  display:flex;
  align-items:center;
  gap:10px;
  width: min(420px, 92%);
  margin: 0 auto;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.16);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 10px 24px rgba(0,0,0,.35) inset;
}
.input-wrapper input{
  flex:1;
  background: transparent;
  border:0;
  outline:0;
  color:#fff;
  font-size:.95rem;
}
.input-wrapper input::placeholder{
  color: rgba(255,255,255,.55);
}
.input-wrapper button{
  display:grid;
  place-items:center;
  border:0;
  border-radius:10px;
  padding:8px 10px;
  background: rgba(255,46,46,.88);
  cursor:pointer;
  transition: transform .15s ease, background .2s ease;
}
.input-wrapper button:hover{ transform: translateY(-1px); }
.input-wrapper button img{ width:20px; height:20px; display:block; }

.error-message {
  margin-top: 20px;
  padding: 12px 16px;
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.3);
  border-radius: 8px;
  color: #ff6666;
  font-size: 0.9rem;
  display: none;
}

@media (max-width: 768px) {
  /* container ocupa toda a tela e centraliza */
  .container {
    padding: 50px 10px 50px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    text-align: center;
  }

  /* título menor mas ainda forte */
  h1 {
    font-size: 1.9rem;
    line-height: 1.3;
  }
  h1 span {
    font-size: 2rem;
  }

  /* subtítulo */
  .sub {
    font-size: 0.95rem;
    margin: 12px 0 28px;
    line-height: 1.5;
  }

  /* aumenta o vídeo (bola) no mobile */
  :root {
    --video-size: 240px; /* maior que no desktop */
  }

  .video-container {
    margin-bottom: 32px;
    padding-top: 40px;
  }

  /* input mais largo */
  .input-wrapper {
    width: 92%;
    border-radius: 12px;
    padding: 10px 12px;
    margin: 0 auto;
  }
  .input-wrapper input {
    font-size: 0.95rem;
  }
  .input-wrapper button img {
    width: 20px;
    height: 20px;
  }
}
  </style>
</head>
<body>
  <div class="container">
    <div class="line"></div>

    <h1>Entenda <span>sua audiência</span></h1>

    <p class="sub">
      Use inteligência artificial para revelar o que seu público realmente sente.<br />
      Transforme comentários em <span>insights claros</span>, identifique emoções ocultas e compreenda de verdade
      a voz da sua <span>audiência no YouTube</span>.
    </p>

    <div class="video-container">
      <video autoplay loop muted playsinline>
        <source src="/static/Comp1_alpha.webm" type="video/webm" />
      </video>
    </div>

    <div class="input-wrapper">
      <input type="text" id="videoUrl" placeholder="Cole o link do YouTube aqui..." />
      <button aria-label="Enviar" id="submitBtn">
        <img src="/static/foguete.svg" alt="" />
      </button>
    </div>
    
    <div class="error-message" id="errorMessage"></div>
  </div>

  <script>
    function isValidYouTubeURL(url) {
      const patterns = [
        /^https?:\/\/(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)/,
        /^https?:\/\/youtu\.be\/([a-zA-Z0-9_-]+)/,
        /^https?:\/\/(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)/
      ];
      return patterns.some(pattern => pattern.test(url));
    }
    
    function showError(message) {
      const errorDiv = document.getElementById('errorMessage');
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
    }
    
    function hideError() {
      document.getElementById('errorMessage').style.display = 'none';
    }
    
    async function startAnalysis() {
      const videoUrl = document.getElementById('videoUrl').value.trim();
      const submitBtn = document.getElementById('submitBtn');
      
      hideError();
      
      if (!videoUrl) {
        showError('Por favor, cole o link do vídeo do YouTube');
        return;
      }
      
      if (!isValidYouTubeURL(videoUrl)) {
        showError('URL inválida. Use um link válido do YouTube');
        return;
      }
      
      submitBtn.style.opacity = '0.6';
      submitBtn.style.pointerEvents = 'none';
      
      try {
        const response = await fetch('/start-analysis', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ video_url: videoUrl })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
          window.location.href = `/processing/${data.job_id}`;
        } else {
          showError(data.error || 'Erro ao iniciar análise');
          submitBtn.style.opacity = '1';
          submitBtn.style.pointerEvents = 'auto';
        }
      } catch (error) {
        showError('Erro de conexão. Tente novamente');
        submitBtn.style.opacity = '1';
        submitBtn.style.pointerEvents = 'auto';
      }
    }
    
    document.getElementById('submitBtn').addEventListener('click', startAnalysis);
    document.getElementById('videoUrl').addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        startAnalysis();
      }
    });
    document.getElementById('videoUrl').addEventListener('input', hideError);
  </script>
</body>
</html>'''

@app.route('/processing/<job_id>')
def processing(job_id):
    """Página de processamento com progresso real"""
    if job_id not in JOBS_STORAGE:
        return redirect('/error?message=Job não encontrado')
    
    job = JOBS_STORAGE[job_id]
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Entenda sua audiência</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --red-primary: #ff0000;
      --red-dark: #cc0000;
      --red-light: #ff6666;
      --red-glow: rgba(255, 0, 0, 0.5);
      --black-bg: #000000;
      --black-secondary: #0a0a0a;
      --white: #ffffff;
      
      /* Variáveis do padrão geométrico */
      --sz: 23px;
      --c1: #350909;
      --c2: #410202;
      --c3: #160000;
      --c4: #210606;
      --ts: 50%/ calc(var(--sz) * 5.5) calc(var(--sz) * 9.5);
      --b1: conic-gradient(from 180deg at 16% 73.5%, var(--c2) 0 120deg, transparent 0 100%) var(--ts);
      --b2: conic-gradient(from 180deg at 39.5% 65.65%, var(--c3) 0 60deg, var(--c1) 0 120deg, transparent 0 100%) var(--ts);
      --pattern-opacity: 0.15;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: linear-gradient(to top, rgb(65 3 3) 0%, #000 45%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: relative;
      isolation: isolate;
      color: #fff;
    }}

    /* Padrão geométrico idêntico ao original */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: var(--pattern-opacity);
      
      background:
        var(--b1), var(--b1), var(--b1), var(--b1),
        var(--b2), var(--b2), var(--b2), var(--b2),
        conic-gradient(from 0deg at 92.66% 50%, var(--c2) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 81.66% 10.25%, var(--c2) 0 180deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 66.66% 22.25%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 71.66% 43%, var(--c3) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 66.66% 45.95%, var(--c3) 0 60deg, transparent 0 100%) var(--ts),
        conic-gradient(from 120deg at 25% 91.5%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 60deg at 50% 51.5%, var(--c1) 0 60deg, var(--c2) 0 120deg, var(--c4) 0 100%) var(--ts);
        
      background-repeat: repeat;
    }}

    .container {{
      position: relative;
      z-index: 1;
      padding: 40px;
      max-width: 600px;
      width: 100%;
    }}

    /* Título principal */
    .header {{
      text-align: center;
      margin-bottom: 60px;
      animation: fadeInDown 0.8s ease;
    }}

    .header h1 {{
      font-size: 3rem;
      font-weight: 700;
      margin-bottom: 20px;
      background: linear-gradient(135deg, #595959 0%, #ffffff 50%, #000000 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      text-shadow: 0 0 40px rgb(255 255 255 / 30%);
      letter-spacing: -1px;
    }}

    .header p {{
      font-size: 1rem;
      font-weight: 400;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.6;
      max-width: 500px;
      margin: 0 auto;
    }}

    .header .highlight {{
      color: #ff3d3d;
      font-weight: 500;
    }}

    /* Wrapper principal */
    #wrapper {{
      position: relative;
      width: 100%;
      max-width: 400px;
      margin: 0 auto;
      padding: 40px 0;
    }}

    /* Loader circular glass */
    .loader-container {{
      position: relative;
      width: 120px;
      height: 120px;
      margin: 0 auto 50px;
    }}

    .loader {{
      width: 100%;
      height: 100%;
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.1);
      position: relative;
      box-shadow: 
        inset 0 0 30px rgba(255, 0, 0, 0.1),
        0 0 40px rgba(255, 0, 0, 0.2),
        0 10px 40px rgba(0, 0, 0, 0.5);
      animation: pulse 2s ease-in-out infinite;
    }}

    .loader::before {{
      content: '';
      position: absolute;
      top: -3px;
      left: -3px;
      right: -3px;
      bottom: -3px;
      border-radius: 50%;
      background: conic-gradient(
        from 0deg,
        transparent,
        var(--red-primary),
        var(--red-light),
        transparent
      );
      animation: rotate 2s linear infinite;
      z-index: -1;
    }}

    .loader::after {{
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 60%;
      height: 60%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,0,0,0.3) 0%, transparent 70%);
      animation: innerPulse 1.5s ease-in-out infinite;
    }}

    @keyframes rotate {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}

    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.05); }}
    }}

    @keyframes innerPulse {{
      0%, 100% {{ opacity: 0.3; transform: translate(-50%, -50%) scale(0.8); }}
      50% {{ opacity: 0.8; transform: translate(-50%, -50%) scale(1.2); }}
    }}

    /* Mouse glassmorphism */
    #mouse {{
      position: absolute;
      top: -50px;
      left: 20%;
      width: 40px;
      height: 40px;
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 
        inset 0 0 20px rgba(255, 0, 0, 0.2),
        0 8px 32px rgba(255, 0, 0, 0.1),
        0 0 20px rgba(255, 0, 0, 0.2);
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: mouseMove 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }}

    #mouse::before {{
      content: '';
      width: 15px;
      height: 15px;
      background: radial-gradient(circle, var(--red-light) 0%, var(--red-primary) 100%);
      border-radius: 50%;
      animation: cursorPulse 1.5s ease-in-out infinite;
    }}

    #mouse::after {{
      content: '';
      position: absolute;
      top: -20px;
      left: -20px;
      right: -20px;
      bottom: -20px;
      border: 2px solid var(--red-primary);
      border-radius: 50%;
      opacity: 0;
      animation: mouseClick 8s ease infinite;
    }}

    @keyframes mouseMove {{
      0%, 100% {{ 
        top: -50px; 
        left: 20%;
        transform: rotate(0deg);
      }}
      25% {{ 
        top: 30px; 
        left: 10%;
        transform: rotate(-10deg);
      }}
      50% {{ 
        top: 30px; 
        left: 85%;
        transform: rotate(10deg);
      }}
      75% {{ 
        top: 30px; 
        left: 50%;
        transform: rotate(0deg);
      }}
    }}

    @keyframes cursorPulse {{
      0%, 100% {{ transform: scale(1); opacity: 0.8; }}
      50% {{ transform: scale(0.8); opacity: 1; }}
    }}

    @keyframes mouseClick {{
      0%, 24%, 26%, 49%, 51%, 74%, 76%, 100% {{ 
        transform: scale(1);
        opacity: 0;
      }}
      25%, 50%, 75% {{
        transform: scale(1.5);
        opacity: 0.5;
      }}
    }}

    /* Barra de progresso glass */
    .loading-bar {{
      width: 100%;
      height: 12px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 100px;
      overflow: hidden;
      position: relative;
      box-shadow: 
        inset 0 1px 3px rgba(0, 0, 0, 0.5),
        0 0 20px rgba(255, 0, 0, 0.1);
    }}

    .progress-bar {{
      height: 100%;
      background: linear-gradient(90deg, 
        var(--red-dark) 0%,
        var(--red-primary) 30%,
        var(--red-light) 50%,
        var(--red-primary) 70%,
        var(--red-dark) 100%);
      background-size: 200% 100%;
      border-radius: 100px;
      width: 0%;
      transition: width 0.5s ease;
      animation: shimmer 2s linear infinite;
      box-shadow: 
        0 0 20px rgba(255, 0, 0, 0.5),
        inset 0 0 10px rgba(255, 255, 255, 0.2);
      position: relative;
    }}

    .progress-bar::after {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(90deg, 
        transparent, 
        rgba(255, 255, 255, 0.3) 50%, 
        transparent);
      animation: shine 2s ease-in-out infinite;
    }}

    @keyframes shimmer {{
      0% {{ background-position: 0% 50%; }}
      100% {{ background-position: 200% 50%; }}
    }}

    @keyframes shine {{
      0% {{ transform: translateX(-100%); }}
      100% {{ transform: translateX(100%); }}
    }}

    /* Status */
    .status {{
      display: flex;
      justify-content: space-between;
      margin-top: 20px;
      font-size: 0.875rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .state {{
      color: rgba(255, 255, 255, 0.8);
      position: relative;
      overflow: hidden;
    }}

    .percentage {{
      color: var(--red-light);
      font-weight: 600;
      text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
    }}

    @keyframes fadeInDown {{
      from {{
        opacity: 0;
        transform: translateY(-20px);
      }}
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Analisando sua audiência...</h1>
      <p>
        Nos bastidores, nossa IA está processando cada detalhe dos
        <span class="highlight">comentários</span>. 
        Em poucos segundos, você terá acesso ao seu
        relatório premium para entender de verdade sua 
        <span class="highlight">audiência no YouTube.</span>.
      </p>
    </div>

    <div id="wrapper">
      <div id="mouse"></div>
      
      <div class="loader-container">
        <div class="loader"></div>
      </div>
      
      <div class="loading-bar">
        <div class="progress-bar" id="progressBar"></div>
      </div>
      
      <div class="status">
        <div class="state" id="statusText">Iniciando...</div>
        <div class="percentage" id="progressText">0%</div>
      </div>
    </div>
  </div>

  <script>
    const jobId = '{job_id}';
    
    async function checkProgress() {{
      try {{
        const response = await fetch(`/status/${{jobId}}`);
        const data = await response.json();
        
        // Atualizar progresso
        document.getElementById('progressBar').style.width = data.progress + '%';
        document.getElementById('progressText').textContent = data.progress + '%';
        document.getElementById('statusText').textContent = data.message;
        
        if (data.status === 'completed') {{
          window.location.href = `/success/${{jobId}}`;
        }} else if (data.status === 'error') {{
          window.location.href = `/error?message=${{encodeURIComponent(data.error)}}`;
        }} else {{
          setTimeout(checkProgress, 2000);
        }}
      }} catch (error) {{
        console.error('Erro ao verificar progresso:', error);
        setTimeout(checkProgress, 3000);
      }}
    }}
    
    // Iniciar verificação
    setTimeout(checkProgress, 1000);
  </script>
</body>
</html>'''

@app.route('/success/<job_id>')
def success(job_id):
    """Página de sucesso com download"""
    if job_id not in JOBS_STORAGE:
        return redirect('/error?message=Job não encontrado')
    
    job = JOBS_STORAGE[job_id]
    dashboard_id = job.get('dashboard_id', job_id)
    file_size = job.get('file_size', 35)
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Download Pronto - YouTube Analytics</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --red-primary: #ff0000;
      --red-dark: #cc0000;
      --red-light: #ff6666;
      --red-glow: rgba(255, 0, 0, 0.5);
      --black-bg: #000000;
      --black-700: hsla(0 0% 12% / 1);
      --white: #ffffff;
      
      /* Variáveis do padrão geométrico */
      --sz: 23px;
      --c1: #350909;
      --c2: #410202;
      --c3: #160000;
      --c4: #210606;
      --ts: 50%/ calc(var(--sz) * 5.5) calc(var(--sz) * 9.5);
      --b1: conic-gradient(from 180deg at 16% 73.5%, var(--c2) 0 120deg, transparent 0 100%) var(--ts);
      --b2: conic-gradient(from 180deg at 39.5% 65.65%, var(--c3) 0 60deg, var(--c1) 0 120deg, transparent 0 100%) var(--ts);
      --pattern-opacity: 0.15;
      
      /* Botão */
      --border_radius: 9999px;
      --transtion: 0.3s ease-in-out;
      --offset: 2px;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: linear-gradient(to top, rgb(65 3 3) 0%, #000 45%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: relative;
      isolation: isolate;
      color: #fff;
    }}

    /* Padrão geométrico */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: var(--pattern-opacity);
      
      background:
        var(--b1), var(--b1), var(--b1), var(--b1),
        var(--b2), var(--b2), var(--b2), var(--b2),
        conic-gradient(from 0deg at 92.66% 50%, var(--c2) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 81.66% 10.25%, var(--c2) 0 180deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 66.66% 22.25%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 71.66% 43%, var(--c3) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 66.66% 45.95%, var(--c3) 0 60deg, transparent 0 100%) var(--ts),
        conic-gradient(from 120deg at 25% 91.5%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 60deg at 50% 51.5%, var(--c1) 0 60deg, var(--c2) 0 120deg, var(--c4) 0 100%) var(--ts);
        
      background-repeat: repeat;
    }}

    /* Container principal com glass */
    .container {{
      position: relative;
      z-index: 1;
      max-width: 500px;
      width: 90%;
      padding: 60px 40px;
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 24px;
      box-shadow: 
        inset 0 0 30px rgba(255, 0, 0, 0.05),
        0 20px 60px rgba(0, 0, 0, 0.6);
      text-align: center;
      animation: slideUp 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
      opacity: 0;
    }}

    @keyframes slideUp {{
      from {{
        transform: translateY(40px) scale(0.95);
        opacity: 0;
      }}
      to {{
        transform: translateY(0) scale(1);
        opacity: 1;
      }}
    }}

    /* Logo do YouTube com animação */
    .logo-container {{
      width: 100px;
      height: 100px;
      margin: 0 auto 30px;
      position: relative;
      animation: logoEntry 1s cubic-bezier(0.34, 1.56, 0.64, 1) 0.3s forwards;
      opacity: 0;
    }}

    @keyframes logoEntry {{
      from {{
        transform: scale(0) rotate(180deg);
        opacity: 0;
      }}
      to {{
        transform: scale(1) rotate(0deg);
        opacity: 1;
      }}
    }}

    .logo-container::before {{
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 120%;
      height: 120%;
      background: radial-gradient(circle, rgba(255, 0, 0, 0.3) 0%, transparent 70%);
      animation: pulse 2s ease-in-out infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ transform: translate(-50%, -50%) scale(0.8); opacity: 0.5; }}
      50% {{ transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }}
    }}

    /* Ícone do YouTube (simulado) */
    .youtube-icon {{
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, var(--red-dark), var(--red-primary));
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      box-shadow: 0 10px 30px rgba(255, 0, 0, 0.3);
    }}

    .youtube-icon::after {{
      content: '▶';
      color: white;
      font-size: 40px;
      transform: translateX(3px);
    }}

    /* Success checkmark */
    .success-badge {{
      position: absolute;
      bottom: -5px;
      right: -5px;
      width: 35px;
      height: 35px;
      background: linear-gradient(135deg, #4ade80, #22c55e);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
      animation: checkEntry 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.8s forwards;
      opacity: 0;
      transform: scale(0);
    }}

    @keyframes checkEntry {{
      to {{
        opacity: 1;
        transform: scale(1);
      }}
    }}

    .success-badge::after {{
      content: '✓';
      color: white;
      font-size: 20px;
      font-weight: bold;
    }}

    /* Títulos */
    h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      margin-bottom: 16px;
      background: linear-gradient(135deg, #fff 0%, var(--red-light) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.5px;
      animation: fadeIn 0.8s ease 0.5s forwards;
      opacity: 0;
    }}

    p {{
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.6;
      margin-bottom: 40px;
      animation: fadeIn 0.8s ease 0.6s forwards;
      opacity: 0;
    }}

    @keyframes fadeIn {{
      to {{
        opacity: 1;
      }}
    }}

    /* Botão customizado */
    .button {{
      cursor: pointer;
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transform-origin: center;
      padding: 1rem 2rem;
      background-color: transparent;
      border: none;
      border-radius: var(--border_radius);
      transform: scale(calc(1 + (var(--active, 0) * 0.1)));
      transition: transform var(--transtion);
      animation: buttonEntry 0.8s ease 0.8s forwards;
      opacity: 0;
    }}

    @keyframes buttonEntry {{
      from {{
        transform: translateY(20px);
        opacity: 0;
      }}
      to {{
        transform: translateY(0);
        opacity: 1;
      }}
    }}

    .button::before {{
      content: "";
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, var(--c1), var(--black-700));
      border-radius: var(--border_radius);
      box-shadow: 
        inset 0 0.5px rgba(255, 255, 255, 0.1), 
        inset 0 -1px 2px 0 rgba(0, 0, 0, 0.5),
        0px 4px 10px -4px hsla(0 0% 0% / calc(1 - var(--active, 0))),
        0 0 0 calc(var(--active, 0) * 0.375rem) rgba(255, 0, 0, 0.75);
      transition: all var(--transtion);
      z-index: 0;
    }}

    .button::after {{
      content: "";
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 100%;
      background: rgba(255, 0, 0, 0.4);
      background-image: 
        radial-gradient(at 51% 89%, rgba(255, 102, 102, 0.8) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(255, 0, 0, 0.6) 0px, transparent 50%),
        radial-gradient(at 22% 91%, rgba(204, 0, 0, 0.6) 0px, transparent 50%);
      background-position: top;
      opacity: var(--active, 0);
      border-radius: var(--border_radius);
      transition: opacity var(--transtion);
      z-index: 2;
    }}

    .button:is(:hover, :focus-visible) {{
      --active: 1;
    }}

    .button:active {{
      transform: scale(1);
    }}

    .button .dots_border {{
      --size_border: calc(100% + 2px);
      overflow: hidden;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: var(--size_border);
      height: var(--size_border);
      background-color: transparent;
      border-radius: var(--border_radius);
      z-index: -10;
    }}

    .button .dots_border::before {{
      content: "";
      position: absolute;
      top: 30%;
      left: 50%;
      transform: translate(-50%, -50%);
      transform-origin: left;
      transform: rotate(0deg);
      width: 100%;
      height: 2rem;
      background: linear-gradient(90deg, transparent, var(--red-light), transparent);
      mask: linear-gradient(transparent 0%, white 120%);
      animation: rotate 2s linear infinite;
    }}

    @keyframes rotate {{
      to {{
        transform: rotate(360deg);
      }}
    }}

    .button .sparkle {{
      position: relative;
      z-index: 10;
      width: 1.75rem;
    }}

    .button .sparkle .path {{
      fill: currentColor;
      stroke: currentColor;
      transform-origin: center;
      color: rgba(255, 255, 255, 0.9);
    }}

    .button:is(:hover, :focus) .sparkle .path {{
      animation: path 1.5s linear 0.5s infinite;
    }}

    .button .sparkle .path:nth-child(1) {{
      --scale_path_1: 1.2;
    }}

    .button .sparkle .path:nth-child(2) {{
      --scale_path_2: 1.2;
    }}

    .button .sparkle .path:nth-child(3) {{
      --scale_path_3: 1.2;
    }}

    @keyframes path {{
      0%, 34%, 71%, 100% {{
        transform: scale(1);
      }}
      17% {{
        transform: scale(var(--scale_path_1, 1));
      }}
      49% {{
        transform: scale(var(--scale_path_2, 1));
      }}
      83% {{
        transform: scale(var(--scale_path_3, 1));
      }}
    }}

    .button .text_button {{
      position: relative;
      z-index: 10;
      background-image: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.9) 0%,
        rgba(255, 255, 255, var(--active, 0)) 120%
      );
      background-clip: text;
      -webkit-background-clip: text;
      font-size: 1rem;
      font-weight: 500;
      color: transparent;
      letter-spacing: 0.3px;
    }}

    /* Detalhes adicionais */
    .file-info {{
      margin-top: 30px;
      padding-top: 30px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      animation: fadeIn 1s ease 1s forwards;
      opacity: 0;
    }}

    .file-info span {{
      display: inline-block;
      margin: 0 15px;
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.5);
    }}

    .file-info .highlight {{
      color: var(--red-light);
      font-weight: 500;
    }}

    /* Partículas de celebração */
    .celebration {{
      position: absolute;
      width: 100%;
      height: 100%;
      top: 0;
      left: 0;
      pointer-events: none;
      overflow: hidden;
    }}

    .particle {{
      position: absolute;
      width: 10px;
      height: 10px;
      background: var(--red-light);
      border-radius: 50%;
      animation: float 3s ease-in-out forwards;
      opacity: 0;
    }}

    @keyframes float {{
      0% {{
        transform: translateY(100vh) rotate(0deg);
        opacity: 1;
      }}
      100% {{
        transform: translateY(-100vh) rotate(360deg);
        opacity: 0;
      }}
    }}

    .particle:nth-child(1) {{ left: 10%; animation-delay: 0s; background: var(--red-primary); }}
    .particle:nth-child(2) {{ left: 20%; animation-delay: 0.2s; background: var(--red-light); }}
    .particle:nth-child(3) {{ left: 30%; animation-delay: 0.4s; width: 8px; height: 8px; }}
    .particle:nth-child(4) {{ left: 40%; animation-delay: 0.6s; background: var(--red-dark); }}
    .particle:nth-child(5) {{ left: 50%; animation-delay: 0.8s; width: 12px; height: 12px; }}
    .particle:nth-child(6) {{ left: 60%; animation-delay: 1s; background: var(--red-light); }}
    .particle:nth-child(7) {{ left: 70%; animation-delay: 1.2s; width: 6px; height: 6px; }}
    .particle:nth-child(8) {{ left: 80%; animation-delay: 1.4s; background: var(--red-primary); }}
    .particle:nth-child(9) {{ left: 90%; animation-delay: 1.6s; width: 14px; height: 14px; }}
    .particle:nth-child(10) {{ left: 95%; animation-delay: 1.8s; background: var(--red-dark); }}

    .new-analysis-btn {{
      margin-top: 20px;
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      color: rgba(255, 255, 255, 0.8);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      transition: all 0.3s ease;
      display: inline-block;
    }}

    .new-analysis-btn:hover {{
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
      transform: translateY(-2px);
    }}
  </style>
</head>
<body>
  <div class="celebration">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
  </div>

  <div class="container">
    <div class="logo-container">
      <div class="youtube-icon"></div>
      <div class="success-badge"></div>
    </div>

    <h1>Análise Concluída!</h1>
    <p>
      Sua análise de sentimentos está pronta.<br>
      Baixe o relatório completo com todos os insights da sua audiência.
    </p>

    <button class="button" onclick="downloadDashboard()">
      <div class="dots_border"></div>
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="sparkle">
        <path class="path" stroke-linejoin="round" stroke-linecap="round" stroke="currentColor" fill="currentColor"
          d="M14.187 8.096L15 5.25L15.813 8.096C16.0231 8.83114 16.4171 9.50062 16.9577 10.0413C17.4984 10.5819 18.1679 10.9759 18.903 11.186L21.75 12L18.904 12.813C18.1689 13.0231 17.4994 13.4171 16.9587 13.9577C16.4181 14.4984 16.0241 15.1679 15.814 15.903L15 18.75L14.187 15.904C13.9769 15.1689 13.5829 14.4994 13.0423 13.9587C12.5016 13.4181 11.8321 13.0241 11.097 12.814L8.25 12L11.096 11.187C11.8311 10.9769 12.5006 10.5829 13.0413 10.0423C13.5819 9.50162 13.9759 8.83214 14.186 8.097L14.187 8.096Z">
        </path>
        <path class="path" stroke-linejoin="round" stroke-linecap="round" stroke="currentColor" fill="currentColor"
          d="M6 14.25L5.741 15.285C5.59267 15.8785 5.28579 16.4206 4.85319 16.8532C4.42059 17.2858 3.87853 17.5927 3.285 17.741L2.25 18L3.285 18.259C3.87853 18.4073 4.42059 18.7142 4.85319 19.1468C5.28579 19.5794 5.59267 20.1215 5.741 20.715L6 21.75L6.259 20.715C6.40725 20.1216 6.71398 19.5796 7.14639 19.147C7.5788 18.7144 8.12065 18.4075 8.714 18.259L9.75 18L8.714 17.741C8.12065 17.5925 7.5788 17.2856 7.14639 16.853C6.71398 16.4204 6.40725 15.8784 6.259 15.285L6 14.25Z">
        </path>
        <path class="path" stroke-linejoin="round" stroke-linecap="round" stroke="currentColor" fill="currentColor"
          d="M6.5 4L6.303 4.5915C6.24777 4.75718 6.15472 4.90774 6.03123 5.03123C5.90774 5.15472 5.75718 5.24777 5.5915 5.303L5 5.5L5.5915 5.697C5.75718 5.75223 5.90774 5.84528 6.03123 5.96877C6.15472 6.09226 6.24777 6.24282 6.303 6.4085L6.5 7L6.697 6.4085C6.75223 6.24282 6.84528 6.09226 6.96877 5.96877C7.09226 5.84528 7.24282 5.75223 7.4085 5.697L8 5.5L7.4085 5.303C7.24282 5.24777 7.09226 5.15472 6.96877 5.03123C6.84528 4.90774 6.75223 4.75718 6.697 4.5915L6.5 4Z">
        </path>
      </svg>
      <span class="text_button">Baixar Arquivo</span>
    </button>

    <div class="file-info">
      <span class="highlight">HTML</span>
      <span>•</span>
      <span>{file_size:.1f} KB</span>
      <span>•</span>
      <span>Relatório Completo</span>
    </div>

    <a href="/" class="new-analysis-btn">Nova Análise</a>
  </div>

  <script>
    function downloadDashboard() {{
      window.location.href = '/download-dashboard/{dashboard_id}';
    }}
  </script>
</body>
</html>'''

@app.route('/error')
def error():
    """Página de erro"""
    message = request.args.get('message', 'Ocorreu um erro inesperado')
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Erro - YouTube Analytics</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --red-primary: #ff0000;
      --red-dark: #cc0000;
      --red-light: #ff6666;
      
      /* Variáveis do padrão geométrico */
      --sz: 23px;
      --c1: #350909;
      --c2: #410202;
      --c3: #160000;
      --c4: #210606;
      --ts: 50%/ calc(var(--sz) * 5.5) calc(var(--sz) * 9.5);
      --b1: conic-gradient(from 180deg at 16% 73.5%, var(--c2) 0 120deg, transparent 0 100%) var(--ts);
      --b2: conic-gradient(from 180deg at 39.5% 65.65%, var(--c3) 0 60deg, var(--c1) 0 120deg, transparent 0 100%) var(--ts);
      --pattern-opacity: 0.15;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: linear-gradient(to top, rgb(65 3 3) 0%, #000 45%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      isolation: isolate;
      color: #fff;
    }}

    /* Padrão geométrico */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: var(--pattern-opacity);
      
      background:
        var(--b1), var(--b1), var(--b1), var(--b1),
        var(--b2), var(--b2), var(--b2), var(--b2),
        conic-gradient(from 0deg at 92.66% 50%, var(--c2) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 81.66% 10.25%, var(--c2) 0 180deg, transparent 0 100%) var(--ts),
        conic-gradient(from -60deg at 66.66% 22.25%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 71.66% 43%, var(--c3) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 0deg at 66.66% 45.95%, var(--c3) 0 60deg, transparent 0 100%) var(--ts),
        conic-gradient(from 120deg at 25% 91.5%, var(--c1) 0 120deg, transparent 0 100%) var(--ts),
        conic-gradient(from 60deg at 50% 51.5%, var(--c1) 0 60deg, var(--c2) 0 120deg, var(--c4) 0 100%) var(--ts);
        
      background-repeat: repeat;
    }}

    .container {{
      position: relative;
      z-index: 1;
      max-width: 500px;
      width: 90%;
      padding: 60px 40px;
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 68, 68, 0.2);
      border-radius: 24px;
      box-shadow: 
        inset 0 0 30px rgba(255, 68, 68, 0.1),
        0 20px 60px rgba(0, 0, 0, 0.6);
      text-align: center;
      animation: slideUp 0.8s ease forwards;
    }}

    @keyframes slideUp {{
      from {{
        transform: translateY(40px);
        opacity: 0;
      }}
      to {{
        transform: translateY(0);
        opacity: 1;
      }}
    }}

    .error-icon {{
      width: 80px;
      height: 80px;
      margin: 0 auto 30px;
      background: linear-gradient(135deg, var(--red-dark), var(--red-primary));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 40px;
      color: white;
      box-shadow: 0 10px 30px rgba(255, 0, 0, 0.3);
      animation: pulse 2s ease-in-out infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.05); }}
    }}

    h1 {{
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 20px;
      color: var(--red-light);
    }}

    p {{
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.6;
      margin-bottom: 40px;
    }}

    .error-details {{
      background: rgba(255, 68, 68, 0.1);
      border: 1px solid rgba(255, 68, 68, 0.2);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 30px;
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
      color: #ff6666;
      word-break: break-word;
    }}

    .retry-btn {{
      padding: 16px 32px;
      background: linear-gradient(135deg, var(--red-primary), var(--red-dark));
      border: none;
      border-radius: 12px;
      color: white;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-block;
      margin-right: 15px;
    }}

    .retry-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 25px rgba(255, 0, 0, 0.3);
    }}

    .home-btn {{
      padding: 16px 32px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      color: rgba(255, 255, 255, 0.8);
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-block;
    }}

    .home-btn:hover {{
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
      transform: translateY(-2px);
    }}

    .suggestions {{
      margin-top: 30px;
      padding-top: 30px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      text-align: left;
    }}

    .suggestions h3 {{
      font-size: 1.1rem;
      margin-bottom: 15px;
      color: #fff;
    }}

    .suggestions ul {{
      list-style: none;
      padding: 0;
    }}

    .suggestions li {{
      padding: 8px 0;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
    }}

    .suggestions li::before {{
      content: '•';
      color: var(--red-light);
      margin-right: 10px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="error-icon">✕</div>
    
    <h1>Oops! Algo deu errado</h1>
    <p>Não foi possível processar sua análise no momento.</p>
    
    <div class="error-details">
      {message}
    </div>
    
    <a href="/" class="retry-btn">Tentar Novamente</a>
    <a href="/" class="home-btn">Voltar ao Início</a>
    
    <div class="suggestions">
      <h3>Possíveis soluções:</h3>
      <ul>
        <li>Verifique se a URL do YouTube está correta</li>
        <li>Certifique-se de que o vídeo tem comentários públicos</li>
        <li>Tente novamente em alguns minutos</li>
        <li>Use uma URL completa (ex: https://youtube.com/watch?v=ABC123)</li>
      </ul>
    </div>
  </div>
</body>
</html>'''

# Endpoints da API
@app.route('/start-analysis', methods=['POST'])
def start_analysis():
    """Inicia análise assíncrona"""
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'status': 'error', 'error': 'video_url é obrigatória'}), 400
        
        if not is_valid_youtube_url(video_url):
            return jsonify({'status': 'error', 'error': 'URL do YouTube inválida'}), 400
        
        # Criar job
        job_id = str(uuid.uuid4())[:8]
        JOBS_STORAGE[job_id] = {
            'status': 'pending',
            'progress': 0,
            'message': 'Iniciando análise...',
            'video_url': video_url,
            'created_at': datetime.now().isoformat()
        }
        
        # Iniciar processamento em background
        thread = threading.Thread(target=process_analysis_async, args=(job_id, video_url))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'message': 'Análise iniciada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar análise: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    """Retorna status do job"""
    if job_id not in JOBS_STORAGE:
        return jsonify({'status': 'error', 'error': 'Job não encontrado'}), 404
    
    job = JOBS_STORAGE[job_id]
    return jsonify(job)

@app.route('/download-dashboard/<dashboard_id>')
def download_dashboard(dashboard_id):
    """Download direto do dashboard via redirect"""
    try:
        # Redirect direto para o dashboard service (mais simples e confiável)
        return redirect(f"{DASHBOARD_SERVICE_URL}/download/{dashboard_id}")
            
    except Exception as e:
        logger.error(f"Erro no download: {str(e)}")
        return redirect('/error?message=Erro no download')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'service': 'Web Interface',
        'status': 'healthy',
        'jobs_active': len(JOBS_STORAGE)
    })

if __name__ == '__main__':
    logger.info("🌐 Web Interface iniciado na porta 8083")
    app.run(host='0.0.0.0', port=8083, debug=False)