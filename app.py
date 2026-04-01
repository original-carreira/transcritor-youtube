from flask import Flask, render_template, request, send_file
from transcript import obter_transcricao, obter_titulo_video, limpar_nome_arquivo
from docx import Document 
from docx.shared import Pt
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    url = None
    titulo = None
    transcricao = None
 
    if request.method == 'POST':
        url = request.form.get('url','').strip()
        
        if not url:
            transcricao = "Por favor, insira uma URL do YouTube."
        else:
            transcricao = obter_transcricao(url)
            titulo = obter_titulo_video(url)

    return render_template('index.html', transcricao=transcricao, url=url, titulo=titulo)

@app.route('/download_txt', methods=['POST'])
def download_txt():
    # Capturar o texto do formulário aqui
    texto = request.form.get('texto', '')
    url = request.form.get('url', '')
    
    if not texto.strip():
        return "Nenhum conteúdo para download.",400
    
    titulo = obter_titulo_video(url)
    nome_arquivo = limpar_nome_arquivo(titulo)
    
    buffer = io.BytesIO()
    buffer.write(texto.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{nome_arquivo}.txt",
        mimetype="text/plain; charset=utf-8"
        )

@app.route('/download_docx', methods=['POST'])
def download_docx():
    texto = request.form.get('texto', '')
    url = request.form.get('url', '')

    if not texto.strip():
        return "Nenhum conteúdo para download.", 400
    
    titulo = obter_titulo_video(url)
    nome_arquivo = limpar_nome_arquivo(titulo)

    document = Document()
    document.add_heading(titulo, 0)

    for paragrafo in texto.split("\n\n"):
        if paragrafo.strip():
            p = document.add_paragraph(paragrafo.strip())
            p.paragraph_format.space_after = Pt(12)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{nome_arquivo}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == '__main__':
    app.run(debug=True)