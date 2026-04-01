from youtube_transcript_api import YouTubeTranscriptApi
import requests ,re , unicodedata

def extrair_id(url):
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def limpar_texto(texto):
    # Remove texto entre colchetes e substitui quebras de linha por espaço
    texto = re.sub(r'\[[^\]]*\]', '', texto)
    # Remove espaços duplicados 
    texto = re.sub(r'\s*\n\s*', ' ', texto)
    return texto.strip()

def normalizar_sentencas(texto):
    if not texto:
        return ""
    # Primeira Letra maíscula
    texto = texto[0].upper() + texto[1:]
    # Verifica se já termina com pontuação (ignorando aspas/espaços)
    if not re.search(r'[.!?]["\']?$', texto):
        texto += '.'
    # Maiscula após ponto final
    texto = re.sub(
        r'([.!?]\s+)([a-záéíóúâêôãõç])', 
        lambda m: m.group(1) + m.group(2).upper(),
        texto
        )
    return texto.strip()
        
def remover_repeticoes(texto):
    # remove duplicação de palavras curtas também (ex: "a a")
    texto = re.sub(r'\b(\w{3,})\s+\1\b', r'\1', texto, flags=re.IGNORECASE)
    return texto

def quebra_por_gatilhos(texto):
    gatilhos = [
        "E agora", "E aqui", "Por isso", "Mas", "Então", "Porque", 
        "Por que", "Além disso", "No entanto", "Entretanto", 
        "Contudo", "Ou seja", "Hoje", "E nós vemos","Enfim",
        "Concluindo"
    ]
    
    for g in gatilhos:
        padrao = r'([.!?]\s+)(' + re.escape(g) + r')'
        texto = re.sub(padrao, r'\1\n\n\2', texto, flags=re.IGNORECASE)
    
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

def agrupar_por_tempo(transcript, pausa=2.0, max_palavras=80):
    paragrafos = []
    bloco = []
    ultimo_tempo_fim = None
    contador_palavras = 0

    for item in transcript:
        texto = (item.text or "").strip()
        if not texto:
            continue

        tempo_inicio = item.start
        # Garante que duracao seja um número para o cálculo do tempo_fim
        duracao = getattr(item, 'duration', 0) or 0
        tempo_fim = tempo_inicio + duracao

        palavras_frase = texto.split()
        qtd_palavras = len(palavras_frase)

        # Critérios de quebra
        quebra_tempo = (
            ultimo_tempo_fim is not None and 
            (tempo_inicio - ultimo_tempo_fim > pausa)
        )
        
        # Previsão: se adicionar esta frase, ultrapassa o limite?
        quebra_tamanho = (contador_palavras + qtd_palavras) > max_palavras

        if (quebra_tempo or quebra_tamanho) and bloco:
            paragrafos.append(" ".join(bloco))
            bloco = []
            contador_palavras = 0

        bloco.append(texto)
        contador_palavras += qtd_palavras
        ultimo_tempo_fim = tempo_fim

    # Adiciona o último bloco pendente
    if bloco:
        paragrafos.append(" ".join(bloco))

    return paragrafos

def corrigir_pontos_quebrados(texto):
    # 1. Junta casos de palavras muito curtas (1-3 letras) seguidas de maiúscula
    # Ex: "no. Caminho" -> "no Caminho"
    # Adicionamos uma verificação para NÃO mexer em abreviações comuns (Sr, Dr, Av)
    excecoes = r'(?![Ss]r|[Dd]r|[Aa]v|[Aa]rt|[Cc]ap|[Ii]d)'
    
    padrao = r'\b(' + excecoes + r'\w{1,3})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ])'
    
    texto = re.sub(padrao, r'\1 \2', texto)
    
    # 2. Opcional: Corrigir pontos que ficaram "soltos" entre espaços
    texto = re.sub(r'\s+\.\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])', '. ', texto)
    
    return texto.strip()

def corrigir_quebra_apos_dois_pontos(texto):
    # Captura : seguido de qualquer combinação de espaços e uma ou mais quebras de linha
    # Substitui por ": " (dois pontos e um único espaço)
    texto = re.sub(r':\s*[\r\n]+', ': ', texto)
    return texto

def limpar_quebras_indevidas(texto):
    # 1. Lista de conectivos que NUNCA terminam frase (Preposições e Conjunções)
    # Adicionei mais alguns termos comuns que o YouTube quebra errado
    conectivos = r'\b(a|de|do|da|e|o|que|com|em|um|uma|para|por|como)\b'
    
    # Junta: "para.\n\nExemplo" -> "para Exemplo"
    texto = re.sub(
        f'{conectivos}\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
        lambda m: f"{m.group(1)} {m.group(2)}",
        texto,
        flags=re.IGNORECASE
    )

    # 2. Junta qualquer palavra de até 3 letras que tenha um ponto "acidental"
    # Mas ignoramos se for uma abreviação conhecida (ex: Sr. Dr.)
    texto = re.sub(
        r'\b(?!(?:Sr|Dr|Av)\.)(\w{1,3})\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
        r'\1 \2',
        texto
    )
    
    return texto

def corrigir_quebras_artificiais(texto):
    # Só junta se NÃO houver pontuação (.!?) antes da quebra
    return re.sub(r'([^.!?])\s*\n\s*\n\s*', r'\1 ', texto)

def obter_titulo_video(url):
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
            })
        html = response.text

        match = re.search(r'<title>(.*?)</title>', html)
        if match:
            titulo = match.group(1)
            titulo = titulo.replace(" - YouTube", "").strip()
            return titulo

        return "video"

    except Exception:
        return "video"

def limpar_nome_arquivo(nome):
    # Remove acentos
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')

    # Remove caracteres inválidos
    nome = re.sub(r'[\\/*?:"<>|,]', '', nome)

    # Substitui espaços por underscore
    nome = re.sub(r'\s+', '_', nome)

    # Remove múltiplos underscores
    nome = re.sub(r'_+', '_', nome)

    # Remove underscores no início/fim
    nome = nome.strip('_')

    # Limita tamanho sem cortar palavra no meio
    palavras = nome.split('_')
    resultado = []

    for palavra in palavras:
        if len("_".join(resultado + [palavra])) <= 60:
            resultado.append(palavra)
        else:
            break

    return "_".join(resultado).lower()

def obter_transcricao(url):
    video_id = extrair_id(url)
    if not video_id:
        return "URL inválida."
        
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=['pt', 'pt-BR', 'en'])

        if not transcript:
            return "Nenhuma transcrição encontrada."

        paragrafos_brutos = agrupar_por_tempo(transcript)
        
        paragrafos_processados = []
        for p in paragrafos_brutos:
            # 1. LIMPEZA BRUTA
            p_limpo = limpar_texto(p)
            # 2. CORREÇÃO ESTRUTURAL (ANTES DE TUDO)
            p_limpo = limpar_quebras_indevidas(p_limpo)
            p_limpo = corrigir_pontos_quebrados(p_limpo)
            # 3. NORMALIZAÇÃO
            p_limpo = normalizar_sentencas(p_limpo)  
            # 4. CORREÇÕES SEMÂNTICAS LEVES 
            p_limpo = remover_repeticoes(p_limpo)
            # 5. ESTRUTURAÇÃO 
            p_limpo = quebra_por_gatilhos(p_limpo) 
            # 6. REFINAMENTO FINAL  
            p_limpo = corrigir_quebra_apos_dois_pontos(p_limpo) 
            
            p_limpo = corrigir_quebras_artificiais(p_limpo)
            
            if p_limpo:
                paragrafos_processados.append(p_limpo)
            
        return "\n\n".join(paragrafos_processados)
    
    except Exception as e:
        return f"Erro ao obter transcrição: {str(e)}"