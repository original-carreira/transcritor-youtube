import io
import re


class SrtExporter:

    def export(self, segments: list, titulo: str, nome_arquivo: str):

        if not segments:
            raise ValueError("Nenhum segmento disponível para exportação SRT.")

        buffer = io.BytesIO()
        srt_content = []
        index = 1

        for segment in segments:
            text = (segment.get("text") or "").strip()

            if not text:
                continue

            # 🔥 NOVO: remover quebras de parágrafo para SRT
            text = re.sub(r'\n+', ' ', text)

            start = self._format_timestamp(segment["start"])
            end = self._format_timestamp(segment["end"])

            bloco = f"{index}\n{start} --> {end}\n{text}\n"
            srt_content.append(bloco)

            index += 1

        final_content = "\n".join(srt_content).strip()

        buffer.write(final_content.encode("utf-8"))
        buffer.seek(0)

        return {
            "buffer": buffer,
            "filename": f"{nome_arquivo}.srt",
            "mimetype": "application/x-subrip"
        }

    def _format_timestamp(self, seconds: float) -> str:
        total_milliseconds = int(round(seconds * 1000))

        hours = total_milliseconds // 3_600_000
        remainder = total_milliseconds % 3_600_000

        minutes = remainder // 60_000
        remainder = remainder % 60_000

        secs = remainder // 1000
        milliseconds = remainder % 1000

        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"