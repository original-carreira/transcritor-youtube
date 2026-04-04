# ==============================
# IMPORTS
# ==============================

from flask import Flask, render_template, request, send_file, redirect, url_for
from transcript import (
    obter_transcricao,
    obter_titulo_video,
    limpar_nome_arquivo,
    extrair_id,
    obter_thumbnail,
    limpar_cache,
    listar_historico,
)

from docx import Document
from docx.shared import Pt
import io
import webbrowser
import threading
import time
import socket


# ==============================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==============================

app = Flask(__name__)


# ==============================
# ROTA PRINCIPAL
# ==============================

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Página principal:
    - recebe URL
    - processa transcrição
    - usa cache quando disponível
    """

    # Estado inicial (GET)
    url = None
    titulo = None
    transcricao = None
    thumbnail = None

    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        if not url:
            transcricao = "Por favor, insira uma URL do YouTube."
        else:
            # 1. Processa transcrição
            resultado = obter_transcricao(url)

            # 🔍 CACHE HIT → retorno completo (dict completo)
            if isinstance(resultado, dict):
                transcricao = resultado.get("transcricao")
                titulo = resultado.get("titulo")
                thumbnail = resultado.get("thumbnail")

            # 🔄 CACHE MISS → processamento normal(string)
            else:
                transcricao = resultado
                # 2. Obtém título (usado no front e downloads)
                titulo = obter_titulo_video(url)

                # 3. Obtém thumbnail a partir do ID do vídeo
                video_id = extrair_id(url)
                thumbnail = obter_thumbnail(video_id)

    # 4. Lista histórico para exibir na página (mais recentes primeiro)
    historico = listar_historico()  # Obtém histórico para exibir na página
    
    # Renderiza página com os dados
    return render_template(
        'index.html',
        transcricao=transcricao,
        url=url,
        titulo=titulo,
        thumbnail=thumbnail,
        historico=historico
    )


# ==============================
# DOWNLOAD TXT
# ==============================

@app.route('/download_txt', methods=['POST'])
def download_txt():
    """
    Gera arquivo .txt da transcrição.
    Evita nova chamada ao YouTube usando título do formulário.
    """

    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', '').strip()

    # Validação
    if not texto:
        return "Nenhum conteúdo para download.", 400

    # Limpa título para usar como nome de arquivo, ou usa nome genérico
    nome_arquivo = limpar_nome_arquivo(titulo or "transcricao")

    # Cria arquivo em memória (BytesIO) para envio
    buffer = io.BytesIO()
    buffer.write(texto.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{nome_arquivo}.txt",
        mimetype="text/plain; charset=utf-8"
    )


# ==============================
# DOWNLOAD DOCX
# ==============================

@app.route('/download_docx', methods=['POST'])
def download_docx():
    """
    Gera arquivo Word (.docx) da transcrição.
    """

    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', '').strip()

    # Validação
    if not texto:
        return "Nenhum conteúdo para download.", 400

    # Limpa título para usar como nome de arquivo, ou usa nome genérico
    nome_arquivo = limpar_nome_arquivo(titulo or "transcricao")

    # Cria documento Word em memória usando python-docx
    document = Document()
    document.add_heading(titulo or "Transcrição", 0)

    # Adiciona parágrafos com espaçamento entre eles
    for paragrafo in texto.split("\n\n"):
        if paragrafo.strip():
            p = document.add_paragraph(paragrafo.strip())
            p.paragraph_format.space_after = Pt(12)

    # Salva documento em um buffer de memória (BytesIO) para envio
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{nome_arquivo}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# ==============================
# LIMPAR HISTÓRICO
# ==============================

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    """
    Limpa o cache e redireciona (PRG pattern).
    """
    limpar_cache()
    return redirect(url_for('index'))


# ==============================
# EXECUÇÃO LOCAL
# ==============================

def servidor_esta_pronto(host="127.0.0.1", port=5000):
    """
    Verifica se o servidor já está aceitando conexões.
    """
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)


def abrir_navegador():
    """
    Aguarda o servidor subir e então abre o navegador.
    """
    servidor_esta_pronto()
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    # Thread separada para não bloquear o Flask
    threading.Thread(target=abrir_navegador).start()

    app.run(debug=False)