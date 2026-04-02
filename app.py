# ==============================
# IMPORTS
# ==============================

from flask import Flask, render_template, request, send_file
from transcript import (
    obter_transcricao,
    obter_titulo_video,
    limpar_nome_arquivo,
    extrair_id,
    obter_thumbnail
)

from docx import Document
from docx.shared import Pt
import io


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
    - retorna dados para o template
    """

    # Estado inicial (GET)
    url = None
    titulo = None
    transcricao = None
    thumbnail = None

    if request.method == 'POST':
        url = request.form.get('url', '').strip()

        # Validação básica
        if not url:
            transcricao = "Por favor, insira uma URL do YouTube."
        else:
            # 1. Processa transcrição
            transcricao = obter_transcricao(url)

            # 2. Obtém título (usado no front e downloads)
            titulo = obter_titulo_video(url)

            # 3. Obtém thumbnail a partir do ID
            video_id = extrair_id(url)
            thumbnail = obter_thumbnail(video_id)

    # Renderiza página com os dados
    return render_template(
        'index.html',
        transcricao=transcricao,
        url=url,
        titulo=titulo,
        thumbnail=thumbnail
    )


# ==============================
# DOWNLOAD TXT
# ==============================

@app.route('/download_txt', methods=['POST'])
def download_txt():
    """
    Gera arquivo .txt da transcrição.
    """

    texto = request.form.get('texto', '').strip()
    url = request.form.get('url', '').strip()

    # Validação
    if not texto:
        return "Nenhum conteúdo para download.", 400

    # Nome do arquivo baseado no título do vídeo
    titulo = obter_titulo_video(url)
    nome_arquivo = limpar_nome_arquivo(titulo)

    # Cria arquivo em memória
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
    url = request.form.get('url', '').strip()

    # Validação
    if not texto:
        return "Nenhum conteúdo para download.", 400

    # Metadados
    titulo = obter_titulo_video(url)
    nome_arquivo = limpar_nome_arquivo(titulo)

    # Criação do documento
    document = Document()
    document.add_heading(titulo, 0)

    # Cada bloco vira um parágrafo
    for paragrafo in texto.split("\n\n"):
        if paragrafo.strip():
            p = document.add_paragraph(paragrafo.strip())
            p.paragraph_format.space_after = Pt(12)

    # Salva em memória
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
# EXECUÇÃO LOCAL
# ==============================

if __name__ == '__main__':
    # debug=True → recarregamento automático e logs detalhados
    app.run(debug=True)