# ==============================
# IMPORTS
# ==============================
import os
import json
import sys
import threading
import time
import socket
import webbrowser

from flask import Flask, render_template, request, send_file, redirect, url_for

# Projeto
from app.services.transcription_service import TranscriptionService
from app.repositories.cache_repository import CacheRepository
from app.utils.file_utils import sanitize_filename
from app.utils.logger import setup_logger
from app.exporters import get_exporter


# ==============================
# UTILITÁRIOS (Compatibilidade com Executável)
# ==============================
def resource_path(relative_path):
    """
    Obtém o caminho absoluto para recursos,
    compatível com PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==============================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==============================

if getattr(sys, 'frozen', False):
    # modo executável
    template_folder = resource_path("templates")
    static_folder = resource_path("static")
else:
    # modo desenvolvimento
    template_folder = "templates"
    static_folder = "static"

app = Flask(
    __name__,
    template_folder=template_folder,
    static_folder=static_folder
)

# ==============================
# BOOTSTRAP
# ==============================

# Service principal
service = TranscriptionService()

# Cache (histórico)
cache_repo = CacheRepository()

# Logger
logger = setup_logger()


# ==============================
# ROTA PRINCIPAL
# ==============================

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    url = None

    # ==============================
    # DEFAULTS (IMPORTANTE)
    # ==============================
    post_process = False

    if request.method == 'POST':
        url = request.form.get('url')

        if url:
            url = url.strip()

        # ==============================
        # VALIDAÇÃO
        # ==============================
        if not url:
            resultado = {
                "text": None,
                "segments": None,
                "source": "Sistema",
                "success": False,
                "error": "Por favor, insira uma URL do YouTube.",
                "titulo": None,
                "thumbnail": None
            }
        else:
            # ==============================
            # CONFIGURAÇÕES DE PROCESSAMENTO
            # ==============================
            post_process = request.form.get('post_process') == 'on'
            
            print("POST_PROCESS (APP):", post_process)  # 👈 AQUI Retirar depois!!!!


            logger.info(f'Processando URL | post_process={post_process}')

            # ==============================
            # EXECUÇÃO DO PIPELINE
            # ==============================
            resultado = service.process(
                url,
                post_process=post_process
            )

    # ==============================
    # HISTÓRICO (FAIL-SAFE)
    # ==============================
    try:
        historico = cache_repo.listar()
        logger.info(f"Histórico carregado: {len(historico)} itens")
    except Exception:
        logger.error("Erro ao carregar histórico", exc_info=True)
        historico = []

    # ==============================
    # RENDERIZAÇÃO
    # ==============================
    return render_template(
        'index.html',
        resultado=resultado or {},
        url=url,
        historico=historico,
        post_process=post_process
    )


# ==============================
# DOWNLOAD TXT
# ==============================

@app.route('/download_txt', methods=['POST'])
def download_txt():
    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', '').strip()

    if not texto:
        return "Nenhum conteúdo para download.", 400

    nome_arquivo = sanitize_filename(titulo or "transcricao")

    exporter = get_exporter("txt")
    result = exporter.export(texto, titulo, nome_arquivo)

    return send_file(
        result["buffer"],
        as_attachment=True,
        download_name=result["filename"],
        mimetype=result["mimetype"]
    )


# ==============================
# DOWNLOAD DOCX
# ==============================

@app.route('/download_docx', methods=['POST'])
def download_docx():
    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', '').strip()

    if not texto:
        return "Nenhum conteúdo para download.", 400

    nome_arquivo = sanitize_filename(titulo or "transcricao")

    exporter = get_exporter("docx")
    result = exporter.export(texto, titulo, nome_arquivo)

    return send_file(
        result["buffer"],
        as_attachment=True,
        download_name=result["filename"],
        mimetype=result["mimetype"]
    )


# ==============================
# DOWNLOAD SRT
# ==============================

@app.route('/download_srt', methods=['POST'])
def download_srt():
    segments_json = request.form.get('segments')
    titulo = request.form.get('titulo', '').strip()

    if not segments_json:
        return "Nenhum segmento para exportação.", 400

    segments = json.loads(segments_json)

    nome_arquivo = sanitize_filename(titulo or "transcricao")

    exporter = get_exporter("srt")
    result = exporter.export(segments, titulo, nome_arquivo)

    return send_file(
        result["buffer"],
        as_attachment=True,
        download_name=result["filename"],
        mimetype=result["mimetype"]
    )


# ==============================
# LIMPAR HISTÓRICO
# ==============================

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    cache_repo.limpar()
    return redirect(url_for('index'))


# ==============================
# EXECUÇÃO LOCAL
# ==============================

def servidor_esta_pronto(host="127.0.0.1", port=5000):
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)


def abrir_navegador():
    servidor_esta_pronto()
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == '__main__':
    threading.Thread(target=abrir_navegador).start()
    app.run(debug=False)