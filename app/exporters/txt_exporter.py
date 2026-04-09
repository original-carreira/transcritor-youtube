import io


class TxtExporter:

    def export(self, data: str, titulo: str, nome_arquivo: str):
        buffer = io.BytesIO()
        buffer.write(data.encode('utf-8'))
        buffer.seek(0)

        return {
            "buffer": buffer,
            "filename": f"{nome_arquivo}.txt",
            "mimetype": "text/plain; charset=utf-8"
        }