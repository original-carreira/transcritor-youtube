import json
import os


class CacheRepository:
    """Responsável exclusivamente pelo acesso ao cache em JSON."""

    def obter_caminho_cache(self):
        """Define o local do arquivo de cache."""
        pasta_base = os.getenv('LOCALAPPDATA') or os.getcwd()
        pasta_app = os.path.join(pasta_base, "@VictorCarreira", "TranscritorYouTube")
        os.makedirs(pasta_app, exist_ok=True)
        return os.path.join(pasta_app, "historico.json")

    def carregar(self):
        """Carrega o cache completo."""
        arquivo_cache = self.obter_caminho_cache()

        if not os.path.exists(arquivo_cache):
            return []

        try:
            with open(arquivo_cache, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def salvar(self, dados):
        """Salva o cache completo."""
        arquivo_cache = self.obter_caminho_cache()

        with open(arquivo_cache, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def buscar_por_video_id(self, video_id):
        """Busca item no cache."""
        if not video_id:
            return None

        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:
                return item

        return None

    def adicionar(self, video_id, url, titulo, thumbnail, transcricao):
        """Adiciona novo item evitando duplicação."""
        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:
                return

        historico.append({
            "video_id": video_id,
            "url": url,
            "titulo": titulo,
            "thumbnail": thumbnail,
            "transcricao": transcricao
        })

        self.salvar(historico)

    def limpar(self):
        """Limpa todo o cache."""
        self.salvar([])

    def listar(self):
        """Lista histórico (mais recente primeiro)."""
        historico = self.carregar()
        return list(reversed(historico))
    
    def obter_traducao(self, video_id, target_lang):
        """Busca item no cache."""
        item = self.buscar_por_video_id(video_id)
        
        if not item:
            return None

        # GARANTE COMPATIBILIDADE
        if "translations" not in item:
            item["translations"] = {}

        return item["translations"].get(target_lang)
    
    def salvar_traducao(self, video_id, target_lang, texto_traduzido):
        """ Adiciona nova tradução evitando duplicação. """
        historico = self.carregar()

        for item in historico:
            if item.get("video_id") == video_id:
                
                # GARANTE COMPATIBILIDADE
                if "translations" not in item:
                    item["translations"] = {}

                item["translations"][target_lang] = texto_traduzido
                break

        self.salvar(historico)