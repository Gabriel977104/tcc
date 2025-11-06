from flask import Flask, request, jsonify
import subprocess
import json
import os
import time
import logging
from openai import OpenAI

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar cliente OpenAI
client = OpenAI(
    api_key="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"
)

def classify_comments_with_openai(comments, max_comments=1000):
    """
    Classifica comentários usando OpenAI ChatGPT API
    Processa até 1000 comentários com rate limiting adequado
    Retorna classificação em JSON para 9 categorias específicas
    OTIMIZADO: Classificação em lotes para melhor contexto e precisão
    """
    # Limitar comentários se necessário
    if len(comments) > max_comments:
        logger.info(f"Limitando de {len(comments)} para {max_comments} comentários")
        comments = comments[:max_comments]
    
    classified_comments = []
    total = len(comments)
    batch_size = 8  # Processar 8 comentários por vez para melhor contexto
    
    # Definir as 9 categorias obrigatórias
    categorias_validas = [
        "alegria", "gracejo", "ira", "aversão", "revolta", 
        "explicativo", "conteúdo vulgar", "ódio", "não identificáveis"
    ]
    
    # Processar em lotes
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_comments = comments[batch_start:batch_end]
        
        try:
            # Preparar batch de comentários
            comentarios_batch = []
            for idx, comment in enumerate(batch_comments):
                texto = comment.get('text', '')[:250]  # Limitar para economizar tokens
                comentarios_batch.append(f"{batch_start + idx + 1}. \"{texto}\"")
            
            comentarios_texto = "\n".join(comentarios_batch)
            
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um especialista em análise de sentimentos para comentários do YouTube brasileiro. Sua missão é classificar cada comentário com alta precisão.

CATEGORIAS OBRIGATÓRIAS (escolha exatamente uma por comentário):
🟢 alegria: felicidade, satisfação, elogios, empolgação, gratidão, admiração
🔵 gracejo: humor, piadas, ironia, sarcasmo, brincadeiras, memes, zoação amigável  
🔴 ira: raiva, indignação, irritação, agressividade, briga, hostilidade
🟡 aversão: desagrado, crítica negativa, desgosto, insatisfação, repulsa
🟠 revolta: protesto, inconformismo, indignação social, injustiça, rebeldia
⚪ explicativo: informações, esclarecimentos, perguntas, ensino, dados, instruções
🟣 conteúdo vulgar: palavrões, linguagem sexual explícita, obscenidades, grosserias
⚫ ódio: ofensas pessoais, discriminação, preconceito, ameaças, xingamentos direcionados
🔘 não identificáveis: neutros, ambíguos, incompreensíveis, spam, sem contexto emocional claro

INSTRUÇÕES CRÍTICAS:
- Analise o CONTEXTO e INTENÇÃO por trás das palavras
- Considere gírias brasileiras e expressões regionais
- "kkkk", "kkk", "rsrs" = gracejo (não alegria)
- Palavrões em contexto de humor = gracejo (não vulgar)
- Palavrões agressivos = vulgar ou ódio
- Críticas construtivas = explicativo
- Críticas destrutivas = aversão

Responda APENAS em JSON válido:
{"classificacoes": [{"id": 1, "categoria": "alegria"}, {"id": 2, "categoria": "gracejo"}, ...]}"""
                    },
                    {
                        "role": "user", 
                        "content": f"Classifique estes comentários do YouTube:\n\n{comentarios_texto}"
                    }
                ],
                max_completion_tokens=120,  # Espaço para JSON com múltiplas classificações
                temperature=0.05  # Muito baixa para máxima consistência
            )
            
            response_text = response.choices[0].message.content.strip()
            
            try:
                # Tentar parsear JSON do lote
                import json
                resultado_json = json.loads(response_text)
                classificacoes = resultado_json.get('classificacoes', [])
                
                # Processar cada classificação do lote
                for idx, comment in enumerate(batch_comments):
                    comment_id = batch_start + idx + 1
                    
                    # Encontrar classificação correspondente
                    classificacao_encontrada = None
                    for classif in classificacoes:
                        if classif.get('id') == comment_id:
                            classificacao_encontrada = classif
                            break
                    
                    if classificacao_encontrada:
                        categoria = classificacao_encontrada.get('categoria', '').lower()
                        if categoria in categorias_validas:
                            comment['categoria'] = categoria
                            comment['classificacao_status'] = 'sucesso_lote'
                        else:
                            comment['categoria'] = classify_fallback(comment.get('text', ''))
                            comment['classificacao_status'] = 'fallback_categoria_invalida'
                    else:
                        comment['categoria'] = classify_fallback(comment.get('text', ''))
                        comment['classificacao_status'] = 'fallback_id_nao_encontrado'
                    
                    classified_comments.append(comment)
                
                # Log de progresso do lote
                logger.info(f"Lote processado: {batch_start + 1}-{batch_end}/{total} comentários")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Erro JSON no lote {batch_start + 1}-{batch_end}: {str(e)}")
                # Fallback: classificar individualmente este lote
                for comment in batch_comments:
                    comment['categoria'] = classify_fallback(comment.get('text', ''))
                    comment['classificacao_status'] = 'fallback_json_lote_invalido'
                    classified_comments.append(comment)
            
            # Rate limiting entre lotes
            time.sleep(2.5)
            
        except Exception as e:
            logger.error(f"Erro no lote {batch_start + 1}-{batch_end}: {str(e)}")
            # Fallback para todo o lote
            for comment in batch_comments:
                comment['categoria'] = classify_fallback(comment.get('text', ''))
                comment['classificacao_status'] = 'fallback_erro_lote'
                classified_comments.append(comment)
            
            # Delay extra em caso de erro
            time.sleep(5)
    
    logger.info(f"Classificação concluída: {len(classified_comments)} comentários processados")
    return classified_comments

def classify_fallback(text):
    """
    Classificação simples por palavras-chave quando API falha
    Usa as mesmas 9 categorias obrigatórias
    """
    if not text:
        return 'não identificáveis'
        
    text_lower = text.lower()
    
    # Palavras-chave otimizadas para as 9 categorias
    keywords = {
        'alegria': ['kkk', 'haha', 'legal', 'incrível', 'amei', 'adorei', 'parabéns', 'top', 'massa', 'show', 'perfeito', 'lindo'],
        'ira': ['raiva', 'pqp', 'droga', 'idiota', 'burro', 'estúpido', 'merda', 'puto', 'irritado'],
        'gracejo': ['kkk', 'kk', 'rs', 'lol', 'piada', 'engraçado', 'zoando', 'brincando', 'kkkk', 'hilário'],
        'explicativo': ['porque', 'assim', 'então', 'primeiro', 'segundo', 'terceiro', 'explicando', 'como', 'quando', 'onde'],
        'conteúdo vulgar': ['porra', 'caralho', 'pqp', 'merda', 'buceta', 'puto', 'fdp', 'cu', 'cacete'],
        'ódio': ['odeio', 'nojo', 'lixo', 'horrível', 'desgraça', 'maldito', 'morte', 'matar', 'imbecil'],
        'aversão': ['não gosto', 'ruim', 'péssimo', 'terrível', 'chato', 'detesto', 'vergonha'],
        'revolta': ['absurdo', 'revoltante', 'injusto', 'ridículo', 'palhaçada', 'inadmissível', 'inaceitável']
    }
    
    for categoria, palavras in keywords.items():
        if any(palavra in text_lower for palavra in palavras):
            return categoria
    
    return 'não identificáveis'

def generate_comprehensive_statistics(classified_comments, video_url):
    """
    Gera estatísticas completas garantindo que todas as 9 categorias apareçam
    Cada categoria terá sua porcentagem, mesmo que seja 0%
    """
    # Definir as 9 categorias obrigatórias
    categorias_obrigatorias = [
        "alegria", "gracejo", "ira", "aversão", "revolta", 
        "explicativo", "conteúdo vulgar", "ódio", "não identificáveis"
    ]
    
    # Inicializar contadores para todas as categorias
    categorias = {cat: 0 for cat in categorias_obrigatorias}
    status_classificacao = {}
    total = len(classified_comments)
    
    # Top comentários por categoria
    top_comentarios = {cat: [] for cat in categorias_obrigatorias}
    
    for comment in classified_comments:
        # Contar categorias
        categoria = comment.get('categoria', 'não identificáveis')
        
        # Se a categoria não está nas obrigatórias, colocar em "não identificáveis"
        if categoria not in categorias_obrigatorias:
            categoria = 'não identificáveis'
            
        categorias[categoria] += 1
        
        # Contar status de classificação
        status = comment.get('classificacao_status', 'unknown')
        status_classificacao[status] = status_classificacao.get(status, 0) + 1
        
        # Coletar exemplos para cada categoria (máximo 3 por categoria)
        if len(top_comentarios[categoria]) < 3:
            top_comentarios[categoria].append({
                'texto': comment.get('text', '')[:100] + '...' if len(comment.get('text', '')) > 100 else comment.get('text', ''),
                'likes': comment.get('like_count', 0),
                'autor': comment.get('author', 'Anônimo')
            })
    
    # Calcular estatísticas por categoria (TODAS as 9 categorias)
    stats_categorias = {}
    for categoria in categorias_obrigatorias:
        count = categorias[categoria]
        stats_categorias[categoria] = {
            'quantidade': count,
            'porcentagem': round((count / total) * 100, 2) if total > 0 else 0.0,
            'exemplos': top_comentarios[categoria]
        }
    
    # Métricas de qualidade
    sucessos = status_classificacao.get('sucesso', 0)
    fallbacks = total - sucessos
    taxa_sucesso = round((sucessos / total) * 100, 2) if total > 0 else 0.0
    
    # Categoria mais comum
    categoria_principal = max(categorias.items(), key=lambda x: x[1]) if any(categorias.values()) else ('não identificáveis', 0)
    
    # Categorias com comentários (para resumo)
    categorias_ativas = {k: v for k, v in categorias.items() if v > 0}
    
    return {
        'video_info': {
            'url': video_url,
            'total_comentarios_analisados': total,
            'data_analise': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'resumo_geral': {
            'categoria_predominante': categoria_principal[0],
            'porcentagem_predominante': round((categoria_principal[1] / total) * 100, 2) if total > 0 else 0.0,
            'taxa_classificacao_sucesso': taxa_sucesso,
            'total_categorias_encontradas': len(categorias_ativas),
            'categorias_com_comentarios': list(categorias_ativas.keys())
        },
        'distribuicao_completa': {
            'todas_9_categorias': stats_categorias,
            'resumo_percentuais': {cat: stats_categorias[cat]['porcentagem'] for cat in categorias_obrigatorias}
        },
        'estatisticas_por_categoria': stats_categorias,  # Mantido para compatibilidade
        'metricas_qualidade': {
            'comentarios_api_sucesso': sucessos,
            'comentarios_fallback': fallbacks,
            'distribuicao_status': status_classificacao
        },
        'comentarios_classificados': classified_comments,
        'status': 'success'
    }

@app.route('/analyze-youtube', methods=['POST'])
def analyze_youtube():
    try:
        data = request.json
        video_url = data.get('video_url')

        if not video_url:
            return jsonify({'error': 'video_url é obrigatória'}), 400

        logger.info(f"🎬 Iniciando análise do vídeo: {video_url}")

        # Executar script de coleta
        env = os.environ.copy()
        env['YOUTUBE_API_KEY'] = 'AIzaSyAhuLtctycytftyjytfyfy3SKRVHa54viddeS08'

        output_path = '/tmp/youtube_comments.json'

        result = subprocess.run([
            '/usr/bin/python3', '/opt/yt/scripts/collect_comments.py',
            '--video-url', video_url,
            '--out', output_path
        ], env=env, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            # Ler comentários coletados
            with open(output_path, 'r', encoding='utf-8') as f:
                comments = json.load(f)

            logger.info(f"📝 Coletados {len(comments)} comentários")

            # Classificar comentários com OpenAI (limite 1000)
            classified_comments = classify_comments_with_openai(comments, max_comments=1000)

            # Gerar relatório completo
            final_result = generate_comprehensive_statistics(classified_comments, video_url)
            
            logger.info(f"✅ Análise concluída! Taxa de sucesso: {final_result['resumo_geral']['taxa_classificacao_sucesso']}%")
            logger.info(f"🏆 Categoria predominante: {final_result['resumo_geral']['categoria_predominante']}")

            return jsonify(final_result)
            
        else:
            logger.error(f"❌ Erro na coleta: {result.stderr}")
            return jsonify({
                'status': 'error', 
                'error': f'Erro ao coletar comentários: {result.stderr or result.stdout}'
            }), 500

    except subprocess.TimeoutExpired:
        logger.error("⏰ Timeout na coleta de comentários")
        return jsonify({
            'status': 'error', 
            'error': 'Timeout - vídeo pode ter muitos comentários'
        }), 408
        
    except Exception as e:
        logger.error(f"💥 Erro geral: {str(e)}")
        return jsonify({
            'status': 'error', 
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'youtube-analyzer-openai',
        'max_comments': 1000,
        'api': 'OpenAI GPT-5-nano'
    })

@app.route('/test-openai', methods=['GET'])
def test_openai():
    """Endpoint para testar se a API do OpenAI está funcionando"""
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Responda apenas em JSON: {\"status\": \"funcionando\"}"}],
            max_completion_tokens=10
        )
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content,
            'api': 'OpenAI GPT-5-nano conectada',
            'categorias_suportadas': [
                "alegria", "gracejo", "ira", "aversão", "revolta", 
                "explicativo", "conteúdo vulgar", "ódio", "não identificáveis"
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
