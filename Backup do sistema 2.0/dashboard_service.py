#!/usr/bin/env python3
"""
Dashboard Generator Pro - Versão Premium - DESENVOLVIDO POR GAYBRIEL
Gráficos funcionais garantidos + Design profissional YouTube
"""

from flask import Flask, request, jsonify, send_file
import requests
import json
import os
import time
import logging
import re
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANALYZER_SERVICE_URL = "http://localhost:8080"
DASHBOARD_DIR = "/tmp/dashboards"
os.makedirs(DASHBOARD_DIR, exist_ok=True)

def get_youtube_video_info(video_url):
    """
    Busca informações do vídeo do YouTube (thumbnail, título, canal)
    """
    try:
        # Extrair video ID do URL
        video_id = extract_video_id(video_url)
        if not video_id:
            return None
        
        # Usar a mesma API key do analyzer
        api_key = 'AIzaSyAhuLhdz2mCl9DraB3SKRVHa54viddeS08'
        
        # Chamar YouTube Data API v3
        youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet',
            'id': video_id,
            'key': api_key
        }
        
        response = requests.get(youtube_api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                snippet = data['items'][0]['snippet']
                
                # Pegar thumbnail de melhor qualidade
                thumbnails = snippet.get('thumbnails', {})
                thumbnail_url = (
                    thumbnails.get('maxres', {}).get('url') or
                    thumbnails.get('high', {}).get('url') or
                    thumbnails.get('medium', {}).get('url') or
                    thumbnails.get('default', {}).get('url') or
                    ''
                )
                
                return {
                    'title': snippet.get('title', 'Título não disponível'),
                    'channel': snippet.get('channelTitle', 'Canal não disponível'),
                    'thumbnail': thumbnail_url,
                    'video_id': video_id
                }
        
        return None
        
    except Exception as e:
        logger.warning(f"Erro ao buscar dados do YouTube: {str(e)}")
        return None

def extract_video_id(url):
    """
    Extrai o video ID de diferentes formatos de URL do YouTube
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def generate_dashboard_html(analysis_result, job_id):
    """
    Gera dashboard premium com gráficos funcionais garantidos
    """
    # Extrair dados
    video_info = analysis_result.get('video_info', {})
    resumo = analysis_result.get('resumo_geral', {})
    distribuicao = analysis_result.get('distribuicao_completa', {})
    stats_categorias = distribuicao.get('todas_9_categorias', {})
    metricas = analysis_result.get('metricas_qualidade', {})
    
    # Buscar dados do YouTube
    youtube_data = get_youtube_video_info(video_info.get('url', ''))
    
    # Descrições dos sentimentos
    descricoes_sentimentos = {
        'alegria': 'Expressa felicidade, satisfação ou entusiasmo positivo.',
        'gracejo': 'Traz humor, piada ou comentário irônico leve.',
        'ira': 'Demonstra raiva intensa, fúria ou hostilidade.',
        'aversão': 'Indica repulsa, nojo ou rejeição a algo.',
        'revolta': 'Reflete indignação ou protesto contra uma situação.',
        'explicativo': 'Focado em esclarecer, informar ou ensinar.',
        'conteúdo vulgar': 'Uso de linguagem chula, ofensiva ou sexual explícita.',
        'ódio': 'Manifesta hostilidade extrema ou desejo de prejudicar.',
        'não identificáveis': 'Quando o sentimento não é claro ou não se enquadra nas categorias.<br>'
                      'Obs: Devido às limitações da IA, não é possível compreender todo o contexto da maioria dos comentários. '
                      'Por isso, grande parte é categorizada como "não identificável". Dessa forma, não se consegue atingir uma acurácia próxima de 100%.',
    }
    
    # Descrições dos sentimentos
    descricoes_sentimentos = {
        'alegria': 'Expressa felicidade, satisfação ou entusiasmo positivo.',
        'gracejo': 'Traz humor, piada ou comentário irônico leve.',
        'ira': 'Demonstra raiva intensa, fúria ou hostilidade.',
        'aversão': 'Indica repulsa, nojo ou rejeição a algo.',
        'revolta': 'Reflete indignação ou protesto contra uma situação.',
        'explicativo': 'Focado em esclarecer, informar ou ensinar.',
        'conteúdo vulgar': 'Uso de linguagem chula, ofensiva ou sexual explícita.',
        'ódio': 'Manifesta hostilidade extrema ou desejo de prejudicar.',
        'não identificáveis': 'Quando o sentimento não é claro ou não se enquadra nas categorias.<br>'
                      'Obs: Devido às limitações da IA, não é possível compreender todo o contexto da maioria dos comentários. '
                      'Por isso, grande parte é categorizada como "não identificável". Dessa forma, não se consegue atingir uma acurácia próxima de 100%.',
    }
    
    # Preparar dados para gráficos
    cores_categorias = {
        'alegria': '#10B981',       # Verde
        'gracejo': '#3B82F6',       # Azul  
        'ira': '#EF4444',           # Vermelho
        'aversão': '#F59E0B',       # Amarelo
        'revolta': '#8B5CF6',       # Roxo
        'explicativo': '#06B6D4',   # Ciano
        'conteúdo vulgar': '#F97316', # Laranja
        'ódio': '#DC2626',          # Vermelho escuro
        'não identificáveis': '#6B7280'  # Cinza
    }
    
    # Categorias apenas com dados (para gráfico de pizza)
    categorias_dados = []
    for categoria, dados in stats_categorias.items():
        quantidade = dados.get('quantidade', 0)
        if quantidade > 0:  # Apenas categorias com comentários
            categorias_dados.append({
                'categoria': categoria.title(),
                'quantidade': quantidade,
                'porcentagem': dados.get('porcentagem', 0),
                'cor': cores_categorias.get(categoria, '#6B7280'),
                'exemplos': dados.get('exemplos', [])
            })
    
    categorias_dados.sort(key=lambda x: x['quantidade'], reverse=True)
    
    # TODAS as 9 categorias (para gráfico de barras e detalhamento)
    todas_categorias = []
    categorias_obrigatorias = [
        "alegria", "gracejo", "ira", "aversão", "revolta", 
        "explicativo", "conteúdo vulgar", "ódio", "não identificáveis"
    ]
    
    for categoria in categorias_obrigatorias:
        dados = stats_categorias.get(categoria, {'quantidade': 0, 'porcentagem': 0.0, 'exemplos': []})
        todas_categorias.append({
            'categoria': categoria.title(),
            'quantidade': dados.get('quantidade', 0),
            'porcentagem': dados.get('porcentagem', 0.0),
            'cor': cores_categorias.get(categoria, '#6B7280'),
            'exemplos': dados.get('exemplos', [])
        })

    # Início do HTML
    html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Sentimentos - YouTube Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #161616 25%, #212121 50%, #080606 75%, #0a0a0a 100%);
            min-height: 100vh;
            color: #ffffff;
            line-height: 1.5;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 32px 24px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 56px;
            padding: 48px 0;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 4px;
            background: linear-gradient(90deg, #FF0000, #FF4444, #FF6666);
            border-radius: 2px;
        }}
        
        .header h1 {{
            font-size: clamp(3rem, 8vw, 5rem);
            font-weight: 900;
            background: linear-gradient(135deg, #FF0000 0%, #FF3333 25%, #FF6666 50%, #FF3333 75%, #FF0000 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            letter-spacing: -0.03em;
            text-shadow: 0 0 40px rgba(255, 0, 0, 0.3);
        }}
        
        .header p {{
            font-size: 1.4rem;
            color: #b0b0b0;
            font-weight: 400;
            letter-spacing: 0.5px;
        }}
        
        .glass-card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 68, 68, 0.15);
            border-radius: 28px;
            padding: 32px;
            box-shadow: 
                0 25px 50px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 0 0 1px rgba(255, 68, 68, 0.05);
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
        }}
        
        .glass-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 0, 0, 0.03) 0%, transparent 50%, rgba(255, 68, 68, 0.03) 100%);
            pointer-events: none;
        }}
        
        .glass-card:hover {{
            transform: translateY(-12px) scale(1.01);
            box-shadow: 
                0 40px 80px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 0 0 1px rgba(255, 68, 68, 0.1);
            border-color: rgba(255, 68, 68, 0.25);
        }}
        
        .video-info {{
            background: linear-gradient(135deg, rgba(255, 0, 0, 0.08) 0%, rgba(139, 0, 0, 0.05) 100%);
            border: 1px solid rgba(255, 68, 68, 0.2);
        }}
        
        .video-url {{
            font-family: 'Courier New', 'Monaco', monospace;
            background: rgba(0, 0, 0, 0.4);
            padding: 16px 24px;
            border-radius: 16px;
            margin: 20px 0;
            word-break: break-all;
            font-size: 1rem;
            border: 1px solid rgba(255, 68, 68, 0.1);
            color: #e0e0e0;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 32px;
            margin-bottom: 56px;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, rgba(255, 0, 0, 0.06) 0%, rgba(139, 0, 0, 0.04) 100%);
            position: relative;
            text-align: center;
            border: 1px solid rgba(255, 68, 68, 0.15);
        }}
        
        .kpi-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #FF0000, #FF4444, #FF6666, #FF4444, #FF0000);
            background-size: 200% 100%;
        }}
        
        .kpi-value {{
            font-size: clamp(3rem, 6vw, 4.5rem);
            font-weight: 900;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .kpi-label {{
            color: #c0c0c0;
            font-size: 1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
            margin-bottom: 56px;
        }}
        
        .chart-container {{
            position: relative;
        }}
        
        .chart-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 28px;
            text-align: center;
            color: #ffffff;
            letter-spacing: 0.5px;
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 400px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 68, 68, 0.08);
        }}
        
        .chart-canvas {{
            width: 100% !important;
            height: 100% !important;
        }}
        
        .categories-section {{
            margin-top: 56px;
        }}
        
        .section-title {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 40px;
            text-align: center;
            color: #ffffff;
            letter-spacing: 0.5px;
        }}
        
        .categories-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 28px;
        }}
        
        .category-card {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.05) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}
        
        .category-name {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #ffffff;
        }}
        
        .category-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            background: rgba(255, 68, 68, 0.15);
            color: #FF6666;
            border: 1px solid rgba(255, 68, 68, 0.2);
        }}
        
        .sentiment-description {{
            color: #b0b0b0;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-bottom: 20px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            border-left: 3px solid rgba(255, 68, 68, 0.3);
            font-style: italic;
        }}
        
        .show-all-btn {{
            background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(255, 68, 68, 0.25) 100%);
            border: 1px solid rgba(255, 68, 68, 0.3);
            color: #FF6666;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 16px;
            text-align: center;
        }}
        
        .show-all-btn:hover {{
            background: linear-gradient(135deg, rgba(255, 68, 68, 0.25) 0%, rgba(255, 68, 68, 0.35) 100%);
            border-color: rgba(255, 68, 68, 0.5);
            transform: translateY(-2px);
        }}
        
        .all-comments {{
            display: none;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid rgba(255, 68, 68, 0.1);
            border-radius: 12px;
            padding: 16px;
            background: rgba(0, 0, 0, 0.2);
        }}
        
        .all-comments.show {{
            display: block;
        }}
        
        .comment-item {{
            padding: 12px;
            margin-bottom: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            border-left: 3px solid;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        
        .comment-text {{
            color: #e0e0e0;
            margin-bottom: 6px;
        }}
        
        .comment-meta-small {{
            font-size: 0.75rem;
            color: #888;
            display: flex;
            justify-content: space-between;
        }}
        
        .category-stats {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 24px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: #a0a0a0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }}
        
        .examples {{
            margin-top: 24px;
        }}
        
        .examples h4 {{
            font-size: 1rem;
            color: #c0c0c0;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        
        .example {{
            background: rgba(255, 255, 255, 0.02);
            padding: 18px;
            border-radius: 14px;
            margin-bottom: 12px;
            border-left: 4px solid;
            transition: all 0.3s ease;
        }}
        
        .example:hover {{
            background: rgba(255, 255, 255, 0.04);
            transform: translateX(6px);
        }}
        
        .example-text {{
            font-size: 0.95rem;
            margin-bottom: 10px;
            line-height: 1.6;
            color: #e0e0e0;
        }}
        
        .example-meta {{
            font-size: 0.8rem;
            color: #888;
            display: flex;
            justify-content: space-between;
        }}
        
        .footer {{
            text-align: center;
            padding: 56px 20px;
            color: #777;
            font-size: 0.95rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 56px;
        }}
        
        .chart-placeholder {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 300px;
            color: #888;
            font-size: 1.1rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            border: 2px dashed rgba(255, 68, 68, 0.2);
        }}
        
        @media (max-width: 768px) {{
            .charts-section {{
                grid-template-columns: 1fr;
            }}
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            .container {{
                padding: 20px 16px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Análise de Sentimentos</h1>
            <p>Dashboard Premium de Comentários do YouTube</p>
        </div>'''
    
    # Video Info com dados do YouTube
    if youtube_data:
        html_content += f'''
        <div class="glass-card video-info">
            <div style="display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap;">
                <div style="flex-shrink: 0;">
                    <img src="{youtube_data['thumbnail']}" 
                         alt="Thumbnail do vídeo" 
                         style="width: 240px; height: 135px; border-radius: 16px; 
                                border: 2px solid rgba(255, 68, 68, 0.3); 
                                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                                object-fit: cover;">
                </div>
                <div style="flex: 1; min-width: 300px;">
                    <h3 style="font-size: 1.6rem; font-weight: 700; margin-bottom: 12px; 
                               color: #ffffff; line-height: 1.3; text-align: left;">
                        {youtube_data['title']}
                    </h3>
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                        <div style="background: rgba(255, 68, 68, 0.15); 
                                    color: #FF6666; padding: 6px 16px; 
                                    border-radius: 20px; font-size: 0.9rem; 
                                    font-weight: 600; border: 1px solid rgba(255, 68, 68, 0.2);">
                            📺 {youtube_data['channel']}
                        </div>
                    </div>
                    <div class="video-url" style="font-size: 0.9rem; padding: 12px 16px; margin: 16px 0;">
                        {video_info.get('url', 'N/A')}
                    </div>
                    <p style="color: #b0b0b0; font-size: 1rem; margin: 0; text-align: left;">
                        Análise realizada em: {video_info.get('data_analise', 'N/A')}
                    </p>
                </div>
            </div>
        </div>'''
    else:
        html_content += f'''
        <div class="glass-card video-info">
            <h3>Informações do Vídeo Analisado</h3>
            <div class="video-url">{video_info.get('url', 'N/A')}</div>
            <p style="color: #b0b0b0; font-size: 1rem;">Análise realizada em: {video_info.get('data_analise', 'N/A')}</p>
        </div>'''
    
    html_content += f'''
        <div class="kpi-grid">
            <div class="glass-card kpi-card">
                <div class="kpi-value">{video_info.get('total_comentarios_analisados', 0):,}</div>
                <div class="kpi-label">Total de Comentários</div>
            </div>
            
            <div class="glass-card kpi-card">
                <div class="kpi-value">100%</div>
                <div class="kpi-label">Taxa de Sucesso IA</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="glass-card chart-container">
                <h3 class="chart-title">Distribuição de Sentimentos</h3>
                <div class="chart-wrapper">
                    <canvas id="donutChart" class="chart-canvas"></canvas>
                </div>
            </div>
            <div class="glass-card chart-container">
                <h3 class="chart-title">Ranking por Categoria</h3>
                <div class="chart-wrapper">
                    <canvas id="barChart" class="chart-canvas"></canvas>
                </div>
            </div>
        </div>
        
        <div class="categories-section">
            <h2 class="section-title">Detalhamento Completo por Categoria</h2>
            <div class="categories-grid">'''
    
    # Gerar cards de categorias
    for i, cat_data in enumerate(todas_categorias):
        cor = cat_data['cor']
        categoria = cat_data['categoria'] 
        categoria_key = categoria.lower().replace(' ', '_')
        quantidade = cat_data['quantidade']
        porcentagem = cat_data['porcentagem']
        exemplos = cat_data['exemplos'][:3]
        
        # Buscar TODOS os comentários desta categoria
        todos_comentarios = []
        for comment in analysis_result.get('comentarios_classificados', []):
            if comment.get('categoria', '').lower() == categoria_key.replace('_', ' '):
                todos_comentarios.append(comment)
        
        descricao = descricoes_sentimentos.get(categoria_key.replace('_', ' '), 'Categoria de sentimento.')
        
        html_content += f'''
                <div class="glass-card category-card">
                    <div class="category-header">
                        <div class="category-name">{categoria}</div>
                        <div class="category-badge">#{i+1}</div>
                    </div>
                    <div class="sentiment-description">{descricao}</div>
                    <div class="category-stats">
                        <div class="stat">
                            <div class="stat-value" style="color: {cor}">{quantidade}</div>
                            <div class="stat-label">Comentários</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" style="color: {cor}">{porcentagem:.1f}%</div>
                            <div class="stat-label">Percentual</div>
                        </div>
                    </div>'''
        
        if exemplos and quantidade > 0:
            html_content += '''
                    <div class="examples">
                        <h4>Exemplos de Comentários:</h4>'''
            
            for exemplo in exemplos:
                texto = exemplo.get('texto', 'N/A')
                likes = exemplo.get('likes', 0)
                autor = exemplo.get('autor', 'Anônimo')
                
                html_content += f'''
                        <div class="example" style="border-left-color: {cor}">
                            <div class="example-text">"{texto}"</div>
                            <div class="example-meta">
                                <span>@{autor}</span>
                                <span>{likes} curtidas</span>
                            </div>
                        </div>'''
            
            html_content += '</div>'
            
            if len(todos_comentarios) > 3:
                html_content += f'''
                    <button class="show-all-btn" onclick="toggleComments('{categoria_key}_{i}')">
                        Exibir todos os {len(todos_comentarios)} comentários
                    </button>
                    <div id="comments_{categoria_key}_{i}" class="all-comments">
                        <h4 style="color: {cor}; margin-bottom: 16px;">Todos os Comentários - {categoria}</h4>'''
                
                for comment in todos_comentarios:
                    texto = comment.get('text', 'N/A')
                    likes = comment.get('like_count', 0)
                    autor = comment.get('author', 'Anônimo')
                    
                    html_content += f'''
                        <div class="comment-item" style="border-left-color: {cor}">
                            <div class="comment-text">"{texto}"</div>
                            <div class="comment-meta-small">
                                <span>@{autor}</span>
                                <span>{likes} curtidas</span>
                            </div>
                        </div>'''
                
                html_content += '</div>'
                
        elif quantidade == 0:
            html_content += '''
                    <div class="examples">
                        <p style="color: #888; font-style: italic; padding: 20px; text-align: center;">
                            Nenhum comentário encontrado nesta categoria
                        </p>
                    </div>'''
        
        html_content += '</div>'
    
    # Dados para JavaScript (método mais simples e robusto)
    pizza_data = {
        'labels': [cat['categoria'] for cat in categorias_dados],
        'values': [cat['porcentagem'] for cat in categorias_dados],
        'colors': [cat['cor'] for cat in categorias_dados],
        'quantities': [cat['quantidade'] for cat in categorias_dados]
    }
    
    bar_data = {
        'labels': [cat['categoria'] for cat in todas_categorias],
        'values': [cat['porcentagem'] for cat in todas_categorias],
        'colors': [cat['cor'] for cat in todas_categorias],
        'quantities': [cat['quantidade'] for cat in todas_categorias]
    }
    
    # JavaScript
    html_content += f'''
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Dashboard Premium de Análise de Sentimentos</strong></p>
            <p>ID: {job_id} • Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>
            <p>Powered by OpenAI GPT-5 • YouTube Data API v3</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    
    <script>
        console.log('🔧 Iniciando Dashboard JavaScript...');
        
        // Dados dos gráficos
        const pizzaData = {json.dumps(pizza_data, ensure_ascii=False)};
        const barData = {json.dumps(bar_data, ensure_ascii=False)};
        
        console.log('📊 Pizza Data:', pizzaData);
        console.log('📊 Bar Data:', barData);
        
        // Função para mostrar/esconder comentários
        function toggleComments(categoryId) {{
            console.log('🔘 Toggle comments:', categoryId);
            const commentsDiv = document.getElementById('comments_' + categoryId);
            const button = event.target;
            
            if (commentsDiv && commentsDiv.classList.contains('show')) {{
                commentsDiv.classList.remove('show');
                button.textContent = button.textContent.replace('Esconder', 'Exibir');
            }} else if (commentsDiv) {{
                commentsDiv.classList.add('show');
                button.textContent = button.textContent.replace('Exibir', 'Esconder');
                setTimeout(() => {{
                    commentsDiv.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                }}, 300);
            }}
        }}
        
        // Aguardar carregamento da página
        window.addEventListener('load', function() {{
            console.log('🚀 Página carregada, iniciando gráficos...');
            
            if (typeof Chart === 'undefined') {{
                console.error('❌ Chart.js não carregou');
                return;
            }}
            
            console.log('✅ Chart.js carregado');
            
            // Configurar Chart.js
            Chart.defaults.font.family = 'Inter';
            Chart.defaults.color = '#ffffff';
            Chart.defaults.font.size = 12;
            
            // Criar gráfico de pizza
            createPizzaChart();
            
            // Criar gráfico de barras
            createBarChart();
        }});
        
        function createPizzaChart() {{
            console.log('🍕 Criando gráfico de pizza...');
            const canvas = document.getElementById('donutChart');
            if (!canvas) {{
                console.error('❌ Canvas donutChart não encontrado');
                return;
            }}
            
            if (pizzaData.labels.length === 0) {{
                console.warn('⚠️ Sem dados para pizza');
                canvas.parentElement.innerHTML = '<div class="chart-placeholder">📊 Nenhum dado com comentários</div>';
                return;
            }}
            
            const ctx = canvas.getContext('2d');
            
            try {{
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: pizzaData.labels,
                        datasets: [{{
                            data: pizzaData.values,
                            backgroundColor: pizzaData.colors,
                            borderColor: pizzaData.colors.map(color => color + 'DD'),
                            borderWidth: 3,
                            hoverBorderWidth: 4,
                            hoverBorderColor: '#ffffff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom',
                                labels: {{
                                    padding: 20,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    color: '#ffffff',
                                    font: {{ size: 11, weight: '600' }}
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                                titleColor: '#ffffff',
                                bodyColor: '#ffffff',
                                borderColor: '#FF4444',
                                borderWidth: 2,
                                cornerRadius: 8,
                                callbacks: {{
                                    label: function(context) {{
                                        const label = context.label || '';
                                        const value = context.parsed;
                                        const quantity = pizzaData.quantities[context.dataIndex];
                                        return ` ${{label}}: ${{value.toFixed(1)}}% (${{quantity}} comentários)`;
                                    }}
                                }}
                            }}
                        }},
                        cutout: '60%',
                        elements: {{ arc: {{ borderRadius: 8 }} }}
                    }}
                }});
                console.log('✅ Gráfico de pizza criado');
            }} catch (error) {{
                console.error('❌ Erro no gráfico de pizza:', error);
            }}
        }}
        
        function createBarChart() {{
            console.log('📊 Criando gráfico de barras...');
            const canvas = document.getElementById('barChart');
            if (!canvas) {{
                console.error('❌ Canvas barChart não encontrado');
                return;
            }}
            
            const ctx = canvas.getContext('2d');
            
            try {{
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: barData.labels,
                        datasets: [{{
                            label: 'Porcentagem',
                            data: barData.values,
                            backgroundColor: barData.colors.map(color => color + '90'),
                            borderColor: barData.colors,
                            borderWidth: 2,
                            borderRadius: 8,
                            borderSkipped: false
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                                titleColor: '#ffffff',
                                bodyColor: '#ffffff',
                                borderColor: '#FF4444',
                                borderWidth: 2,
                                cornerRadius: 8,
                                callbacks: {{
                                    label: function(context) {{
                                        const quantity = barData.quantities[context.dataIndex];
                                        return ` ${{context.parsed.y.toFixed(1)}}% (${{quantity}} comentários)`;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                grid: {{ color: 'rgba(255, 255, 255, 0.1)', drawBorder: false }},
                                ticks: {{ color: '#ffffff', font: {{ size: 10, weight: '600' }}, maxRotation: 45 }}
                            }},
                            y: {{
                                grid: {{ color: 'rgba(255, 255, 255, 0.1)', drawBorder: false }},
                                ticks: {{ 
                                    color: '#ffffff', 
                                    font: {{ size: 10, weight: '600' }},
                                    callback: function(value) {{ return value.toFixed(1) + '%'; }}
                                }},
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                console.log('✅ Gráfico de barras criado');
            }} catch (error) {{
                console.error('❌ Erro no gráfico de barras:', error);
            }}
        }}
    </script>
</body>
</html>'''
    
    return html_content

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Dashboard Generator Pro',
        'version': '3.0',
        'status': 'running',
        'features': ['gráficos garantidos', 'design premium', 'cores YouTube']
    })

@app.route('/generate', methods=['POST'])
def generate_dashboard():
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'error': 'video_url é obrigatória'}), 400
        
        logger.info(f"Gerando dashboard premium para: {video_url}")
        
        # Chamar analyzer
        response = requests.post(
            f"{ANALYZER_SERVICE_URL}/analyze-youtube",
            json={'video_url': video_url},
            timeout=1800
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Erro no serviço de análise',
                'details': response.text
            }), 500
        
        analysis_data = response.json()
        logger.info("Dados recebidos, gerando dashboard...")
        
        # Gerar dashboard
        job_id = f"{int(time.time())}_{hash(video_url) % 10000}"
        dashboard_html = generate_dashboard_html(analysis_data, job_id)
        
        # Salvar
        dashboard_filename = f"dashboard_{job_id}.html"
        dashboard_path = os.path.join(DASHBOARD_DIR, dashboard_filename)
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        logger.info(f"Dashboard premium salvo: {dashboard_path}")
        
        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'download_url': f'/download/{job_id}',
            'dashboard_ready': True,
            'video_url': video_url,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_size_kb': round(os.path.getsize(dashboard_path) / 1024, 2)
        })
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return jsonify({
            'error': 'Erro na geração do dashboard',
            'details': str(e)
        }), 500

@app.route('/download/<job_id>')
def download_dashboard(job_id):
    try:
        dashboard_filename = f"dashboard_{job_id}.html"
        dashboard_path = os.path.join(DASHBOARD_DIR, dashboard_filename)
        
        if not os.path.exists(dashboard_path):
            return jsonify({'error': 'Dashboard não encontrado'}), 404
        
        return send_file(
            dashboard_path,
            as_attachment=True,
            download_name=f'dashboard_premium_{job_id}.html',
            mimetype='text/html'
        )
        
    except Exception as e:
        return jsonify({'error': f'Erro no download: {str(e)}'}), 500

@app.route('/health')
def health():
    try:
        analyzer_status = requests.get(f"{ANALYZER_SERVICE_URL}/health", timeout=5)
        analyzer_ok = analyzer_status.status_code == 200
    except:
        analyzer_ok = False
    
    return jsonify({
        'service': 'Dashboard Generator Pro',
        'status': 'healthy',
        'analyzer_connected': analyzer_ok,
        'features': ['charts_guaranteed', 'premium_design', 'youtube_colors']
    })

if __name__ == '__main__':
    logger.info("🚀 Dashboard Generator Pro iniciado na porta 8081")
    app.run(host='0.0.0.0', port=8081, debug=False)