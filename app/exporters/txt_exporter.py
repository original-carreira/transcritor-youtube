import io
import re


class TxtExporter:

    def export(self, data: str, titulo: str, nome_arquivo: str):

        # 🔥 normalização leve
        data = re.sub(r'\n{3,}', '\n\n', data.strip())

        buffer = io.BytesIO()
        buffer.write(data.encode('utf-8'))
        buffer.seek(0)

        return {
            "buffer": buffer,
            "filename": f"{nome_arquivo}.txt",
            "mimetype": "text/plain; charset=utf-8"
        }