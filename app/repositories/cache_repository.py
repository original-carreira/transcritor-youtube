import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger("app")


# ==============================
# CAMINHO ÚNICO E DETERMINÍSTICO
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_FILE = CACHE_DIR / "historico.json"


class CacheRepository:
    """Responsável exclusivamente pelo acesso ao cache em JSON."""

    # ==============================
    # LOAD
    # ==============================
    def carregar(self):
        try:
            if not CACHE_FILE.exists():
                return []

            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception:
            logger.error("Erro ao ler cache", exc_info=True)
            return []

    # ==============================
    # SAVE
    # ==============================
    def salvar(self, dados):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)

        except Exception:
            logger.error("Erro ao salvar cache", exc_info=True)

    # ==============================
    # BUSCAR
    # ==============================
    def buscar_por_video_id(self, video_id):
        if not video_id:
            return None

        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:
                return item

        return None

    # ==============================
    # ADICIONAR (CORRIGIDO)
    # ==============================
    def adicionar(self, video_id, url, titulo, thumbnail, texto):
        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:
                return

        # 🔴 NORMALIZAÇÃO
        if isinstance(thumbnail, list):
            thumbnail = thumbnail[0]

        item = {
            "video_id": video_id,
            "titulo": titulo or url,
            "url": url,
            "text": texto,
            "translations": {},
            "thumbnail": thumbnail or "",
            "timestamp": datetime.now().isoformat()
        }

        historico.append(item)
        self.salvar(historico)

    # ==============================
    # LISTAR (FAIL-SAFE)
    # ==============================
    def listar(self) -> list:
        try:
            historico = self.carregar()
            return list(reversed(historico))
        except Exception:
            logger.error("Erro ao listar histórico", exc_info=True)
            return []

    # ==============================
    # LIMPAR
    # ==============================
    def limpar(self):
        self.salvar([])

    # ==============================
    # TRADUÇÃO (CORRIGIDA)
    # ==============================
    def obter_traducao(self, video_id, target_lang):
        item = self.buscar_por_video_id(video_id)

        if not item:
            return None

        if "translations" not in item:
            item["translations"] = {}

        return item["translations"].get(target_lang)

    def salvar_traducao(self, video_id, target_lang, texto_traduzido):
        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:

                if "translations" not in item:
                    item["translations"] = {}

                item["translations"][target_lang] = texto_traduzido
                break

        self.salvar(historico)