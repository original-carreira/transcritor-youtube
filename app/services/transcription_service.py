# ==============================
#           IMPORTS
# =============================
from youtube_transcript_api import YouTubeTranscriptApi
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient

import requests
import re
import unicodedata
import json
import os

class TranscriptionService:
    def __init__(self):
        self.cache = CacheRepository()
        self.youtube = YouTubeClient()
    
    def process(self, url: str):
        """Orquestra todo o fluxo de transcrição.
        (Inicialmente, só vamos mover código existente para cá)"""
        # TODO: mover lógica de transcript.py para cá
        return self.obter_transcricao(url)

    # ==============================
    # UTILITÁRIOS BÁSICOS
    # ==============================
    def extrair_id(self, url):
        """Extrai o ID do vídeo a partir da URL do YouTube.
        Ex: https://youtube.com → ABC123"""
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

    # ==============================
    # LIMPEZA INICIAL DO TEXTO
    # ==============================
    def limpar_texto(self, texto):
        """Remove:
        - textos entre colchetes [música], [aplausos]
        - espaços duplicados"""
        texto = re.sub(r'\[[^\]]*\]', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    # ==============================
    # NORMALIZAÇÃO DE SENTENÇAS
    # ==============================
    def normalizar_sentencas(self, texto):
        """Ajusta:
        - primeira letra maiúscula
        - garante ponto final
        - capitalização após pontuação"""
        if not texto:
            return ""
        texto = texto[0].upper() + texto[1:]
        # Garante pontuação final
        if not re.search(r'[.!?]["\']?$', texto):
            texto += '.'
        # Capitaliza após pontuação
        texto = re.sub(r'([.!?]\s+)([a-záéíóúâêôãõç])',
                       lambda m: m.group(1) + m.group(2).upper(),
                       texto)
        return texto.strip()

    # ==============================
    # REMOÇÃO DE REPETIÇÕES
    # ==============================
    def remover_repeticoes(self, texto):
        """Remove palavras repetidas consecutivas."""
        return re.sub(r'\b(\w{2,})\s+\1\b', r'\1', texto, flags=re.IGNORECASE)

    # ==============================
    # QUEBRA POR GATILHOS SEMÂNTICOS
    # ==============================
    def quebra_por_gatilhos(self, texto):
        """Insere quebras de parágrafo com base em palavras-chave
        que indicam mudança de ideia."""
        gatilhos = ["E agora", "E aqui", "Por isso", "Mas", "Então", "Porque",
                    "Por que", "Além disso", "No entanto", "Entretanto",
                    "Contudo", "Ou seja", "Hoje", "E nós vemos", "Enfim",
                    "Concluindo"]
        for g in gatilhos:
            padrao = r'([.!?]\s+)(' + re.escape(g) + r')'
            texto = re.sub(padrao, r'\1\n\n\2', texto, flags=re.IGNORECASE)
        # Remove quebras excessivas
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        return texto.strip()

    # ==============================
    # AGRUPAMENTO POR TEMPO
    # ==============================
    def agrupar_por_tempo(self, transcript, pausa=2.0, max_palavras=80):
        """Agrupa falas em parágrafos com base em:
        - pausas entre falas
        - limite de palavras"""
        paragrafos = []
        bloco = []
        ultimo_tempo_fim = None
        contador_palavras = 0
        for item in transcript:
            texto = (item.get('text') or "").strip()
            if not texto:
                continue
            tempo_inicio = item.get('start')
            duracao = item.get('duration') or 0
            tempo_fim = tempo_inicio + duracao
            qtd_palavras = len(texto.split())
            quebra_tempo = (ultimo_tempo_fim is not None and
                           (tempo_inicio - ultimo_tempo_fim > pausa))
            quebra_tamanho = (contador_palavras + qtd_palavras) > max_palavras
            if (quebra_tempo or quebra_tamanho) and bloco:
                paragrafos.append(" ".join(bloco))
                bloco = []
                contador_palavras = 0
            bloco.append(texto)
            contador_palavras += qtd_palavras
            ultimo_tempo_fim = tempo_fim
        if bloco:
            paragrafos.append(" ".join(bloco))
        return paragrafos

    # ==============================
    # CORREÇÕES ESTRUTURAIS
    # ==============================
    def corrigir_pontos_quebrados(self, texto):
        """ Corrige:
        - palavras curtas quebradas com ponto
        Ex: "no. Caminho" → "no Caminho" """
        excecoes = r'(?![Ss]r|[Dd]r|[Aa]v|[Aa]rt|[Cc]ap|[Ii]d)'
        padrao = r'\b(' + excecoes + r'\w{1,3})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ])'
        texto = re.sub(padrao, r'\1 \2', texto)
        texto = re.sub(r'\s+\.\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])', '. ', texto)
        return texto.strip()

    def corrigir_quebra_apos_dois_pontos(self, texto):
        """ Corrige quebra após ":" """
        return re.sub(r':\s*[\r\n]+', ': ', texto)

    def limpar_quebras_indevidas(self, texto):
        """ Junta frases quebradas incorretamente após conectivos """
        conectivos = r'\b(a|de|do|da|e|o|que|com|em|um|uma|para|por|como)\b'
        texto = re.sub(f'{conectivos}\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
                       lambda m: f"{m.group(1)} {m.group(2)}",
                       texto,
                       flags=re.IGNORECASE)
        texto = re.sub(r'\b(?!(?:Sr|Dr|Av)\.)(\w{1,3})\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
                       r'\1 \2',
                       texto)
        return texto

    def corrigir_quebras_artificiais(self, texto):
        """ Junta quebras de linha indevidas sem pontuação. """
        return re.sub(r'([^.!?])\s*\n\s*\n\s*', r'\1 ', texto)

    # ==============================
    # METADADOS DO VÍDEO
    # ==============================
    def obter_titulo_video(self, url):
        """ Obtém o título do vídeo via HTML."""
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            html = response.text
            match = re.search(r'<title>(.*?)</title>', html)
            if match:
                return match.group(1).replace(" - YouTube", "").strip()
            return "titulo_indisponivel"
        except Exception:
            return "titulo_indisponivel"

    def limpar_nome_arquivo(self, nome):
        """Normaliza o nome para uso em arquivos:
        - remove acentos
        - remove caracteres inválidos
        - limita tamanho sem cortar palavras"""
        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
        nome = re.sub(r'[\\/*?:"<>|,]', '', nome)
        nome = re.sub(r'\s+', '_', nome)
        nome = re.sub(r'_+', '_', nome)
        nome = nome.strip('_')
        palavras = nome.split('_')
        resultado = []
        for palavra in palavras:
            if len("_".join(resultado + [palavra])) <= 60:
                resultado.append(palavra)
            else:
                break
        return "_".join(resultado).lower()

    def obter_thumbnail(self, video_id):
        """Retorna lista de thumbnails em diferentes qualidades
        (fallback automático no frontend)."""
        if not video_id:
            return None
        qualidades = ["maxresdefault", "hqdefault", "mqdefault"]
        return [f"https://youtube.com{video_id}/{q}.jpg" for q in qualidades]

    # ==============================
    # FUNÇÃO PRINCIPAL
    # ==============================
    def obter_transcricao(self, url):
        """Pipeline completo:
        - obtém transcript
        - limpa
        - corrige
        - estrutura"""
        video_id = self.extrair_id(url)
        # Verifica se já existe no cache, CACHE FIRST (evita chamada externa)
        cache_item = self.cache.buscar_por_video_id(video_id)
        if cache_item:
            return cache_item["transcricao"]
            
        if not video_id:
            return "URL inválida."
            
        try:
            transcript = self.youtube.fetch_transcript(video_id)
            
            if not transcript:
                return "Nenhuma trasncrição encontrada."
                
            paragrafos_brutos = self.agrupar_por_tempo(transcript)
            paragrafos_processados = []
            
            for p in paragrafos_brutos:
                # 1. LIMPEZA BRUTA
                p_limpo = self.limpar_texto(p)
                # 2. CORREÇÃO ESTRUTURAL
                p_limpo = self.limpar_quebras_indevidas(p_limpo)
                p_limpo = self.corrigir_pontos_quebrados(p_limpo)
                # 3. REMOVER REPETIÇÕES (ANTES DA NORMALIZAÇÃO)
                p_limpo = self.remover_repeticoes(p_limpo)
                # 4. NORMALIZAÇÃO
                p_limpo = self.normalizar_sentencas(p_limpo)
                # 5. ESTRUTURAÇÃO
                p_limpo = self.quebra_por_gatilhos(p_limpo)
                # 6. REFINAMENTO FINAL
                p_limpo = self.corrigir_quebra_apos_dois_pontos(p_limpo)
                p_limpo = self.corrigir_quebras_artificiais(p_limpo)
                
                if p_limpo:
                    paragrafos_processados.append(p_limpo)
                    
            texto_final = "\n\n".join(paragrafos_processados)
            titulo = self.obter_titulo_video(url)
            thumbnail = self.obter_thumbnail(video_id)
            self.cache.adicionar(video_id, url, titulo, thumbnail, texto_final)
            return texto_final
            
        except Exception as e:
            return f"Erro ao obter transcrição: {str(e)}"
