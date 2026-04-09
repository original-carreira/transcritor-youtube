import io
from docx import Document
from docx.shared import Pt


class DocxExporter:

    def export(self, data: str, titulo: str, nome_arquivo: str):
        document = Document()
        document.add_heading(titulo or "Transcrição", 0)

        for paragrafo in data.split("\n\n"):
            if paragrafo.strip():
                p = document.add_paragraph(paragrafo.strip())
                p.paragraph_format.space_after = Pt(12)

        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)

        return {
            "buffer": buffer,
            "filename": f"{nome_arquivo}.docx",
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }