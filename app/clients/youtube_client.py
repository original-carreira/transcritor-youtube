from youtube_transcript_api import YouTubeTranscriptApi
import requests
import re


class YouTubeClient:
    """Responsável por acessar o YouTube e obter dados."""

    # ==============================
    # ENTRYPOINT PRINCIPAL
    # ==============================
    def get_transcription(self, url: str):
        """
        Orquestra:
        - extrair video_id
        - buscar transcrição
        - buscar metadata
        """

        video_id = self._extract_video_id(url)

        if not video_id:
            return "URL inválida"

        transcript = self.fetch_transcript(video_id)
        metadata = self.fetch_video_metadata(video_id)

        if not transcript:
            return "Não foi possível obter a transcrição"

        # Texto completo
        texto = " ".join([item["text"] for item in transcript])

        # Segments padronizados
        segments = [
            {
                "start": item["start"],
                "end": item["start"] + item["duration"],
                "text": item["text"]
            }
            for item in transcript
        ]

        return {
            "transcricao": texto,
            "segments": segments,
            "titulo": metadata.get("titulo"),
            "thumbnail": metadata.get("thumbnail"),
            "from_cache": False
        }

    # ==============================
    # EXTRAÇÃO DE ID
    # ==============================
    def _extract_video_id(self, url: str):
        patterns = [
            r"v=([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    # ==============================
    # TRANSCRIÇÃO
    # ==============================
    def fetch_transcript(self, video_id: str):

        try:
            transcript = YouTubeTranscriptApi.fetch(
                video_id,
                languages=['pt', 'pt-BR', 'en']
            )
        except TypeError:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(
                video_id,
                languages=['pt', 'pt-BR', 'en']
            )

        if not transcript:
            return None

        normalized = []

        for item in transcript:
            try:
                normalized.append({
                    "text": item["text"],
                    "start": item["start"],
                    "duration": item.get("duration", 0)
                })
            except Exception:
                normalized.append({
                    "text": item.text,
                    "start": item.start,
                    "duration": getattr(item, "duration", 0)
                })

        return normalized

    # ==============================
    # METADATA
    # ==============================
    def fetch_video_metadata(self, video_id: str):
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"

            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            html = response.text

            match = re.search(r'<title>(.*?)</title>', html)
            titulo = match.group(1).replace(" - YouTube", "").strip() if match else None

            qualidades = ["maxresdefault", "hqdefault", "mqdefault"]

            thumbnail = [
                f"https://img.youtube.com/vi/{video_id}/{q}.jpg"
                for q in qualidades
            ]

            return {
                "titulo": titulo,
                "thumbnail": thumbnail
            }

        except Exception:
            return {
                "titulo": None,
                "thumbnail": None
            }