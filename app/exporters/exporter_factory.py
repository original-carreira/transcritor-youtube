from .txt_exporter import TxtExporter
from .docx_exporter import DocxExporter
from .srt_exporter import SrtExporter


def get_exporter(format: str):
    exporters = {
        "txt": TxtExporter(),
        "docx": DocxExporter(),
        "srt": SrtExporter(),
    }

    exporter = exporters.get(format)

    if not exporter:
        raise ValueError(f"Formato não suportado: {format}")

    return exporter