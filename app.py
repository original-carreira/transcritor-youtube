# ==============================
# IMPORTS
# ==============================
import os
import sys
import io
import threading
import time
import socket
import webbrowser
from flask import Flask, render_template, request, send_file, redirect, url_for
from app.infra.translators.translator_factory import get_translator

# Imports do seu projeto
from app.services.transcription_service import TranscriptionService
from app.repositories.cache_repository import CacheRepository
from app.exporters import get_exporter

# ==============================
# UTILITÁRIOS (Compatibilidade com Executável)
# ==============================
def resource_path(relative_path):
    """ Obtém o caminho absoluto para recursos, compatível com PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)




# ==============================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==============================

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
    )
service = TranscriptionService() # Instância única para o app
cache_repo = CacheRepository()   # Cria a instância do repositório
translator = get_translator("simple")  # ou None
service = TranscriptionService(translator=translator)

# ==============================
# ROTA PRINCIPAL
# ==============================

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    url = None

    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            url = url.strip()

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
            translate = request.form.get('translate') == 'on'
            target_lang = request.form.get('target_lang') or 'EN'

            resultado = service.process(
                url,
                translate=translate,
                target_lang=target_lang
                )
           
    # CENTRALIZADO: Histórico via service
    historico = cache_repo.listar()
    
    return render_template(
        'index.html',
        resultado = resultado or {},
        url = url,
        historico=historico
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

    # CENTRALIZADO: Limpeza de nome via service
    nome_arquivo = service.limpar_nome_arquivo(titulo or "transcricao")
    
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

    # CENTRALIZADO: Limpeza de nome via service
    nome_arquivo = service.limpar_nome_arquivo(titulo or "transcricao")
    
    exporter = get_exporter("docx")
    result = exporter.export(texto, titulo, nome_arquivo)
    
    return send_file(result["buffer"],
                     as_attachment=True,
                     download_name=result["filename"],
                     mimetype=result["mimetype"]
                     )

# ==============================
# LIMPAR HISTÓRICO
# ==============================

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    # CENTRALIZADO: Limpeza via service
    cache_repo.limpar()
    return redirect(url_for('index'))

# ==============================
# EXECUÇÃO LOCAL (Mantido original)
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
