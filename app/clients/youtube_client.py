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
    # TRANSCRIÇÃO novo
    # ==============================
    
    def fetch_transcript(self, video_id: str):
        try:
            # 🔍 tenta usar API nova
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # manual
                try:
                    transcript = transcript_list.find_manually_created_transcript(['pt', 'pt-BR'])
                    data = transcript.fetch()
                except:
                    transcript = None

                # auto
                if not transcript:
                    try:
                        transcript = transcript_list.find_generated_transcript(['pt', 'pt-BR'])
                        data = transcript.fetch()
                    except:
                        transcript = None

                # fallback inglês
                if not transcript:
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                        data = transcript.fetch()
                    except:
                        transcript = None

                if not transcript:
                    raise Exception("Nenhuma transcript encontrada")

            except AttributeError:
                # 🔥 fallback para versão antiga
                print("Usando fallback da API antiga")

                api = YouTubeTranscriptApi()
                data = api.fetch(
                    video_id,
                    languages=['pt', 'pt-BR', 'en']
                    )

            # ==============================
            # NORMALIZAÇÃO
            # ==============================
            normalized = []

            for item in data:
                try:
                    
                    normalized.append({
                        "text": item["text"],
                        "start": item["start"],
                        "duration": item.get("duration", 0)
                    })
                    
                except TypeError:
                    
                    normalized.append({
                        "text": item.text,
                        "start": item.start,
                        "duration": getattr(item, "duration", 0)
                        })

            return normalized

        except Exception as e:
            print("ERRO TRANSCRIPT:", e)
            return None  
    
    
    
    # ==============================
    # TRANSCRIÇÃO old
    # ==============================
    def fetch_transcript_old(self, video_id: str):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # ==============================
            # 1. MANUAL (PT)
            # ==============================
            try:
                transcript = transcript_list.find_manually_created_transcript(['pt', 'pt-BR'])
                data = transcript.fetch()
            except:
                transcript = None

            # ==============================
            # 2. AUTO (PT)
            # ==============================
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(['pt', 'pt-BR'])
                    data = transcript.fetch()
                except:
                    transcript = None

            # ==============================
            # 3. FALLBACK FINAL (FETCH DIRETO)
            # 🔥 ESSENCIAL
            # ==============================
            if not transcript:
                try:
                    data = YouTubeTranscriptApi.fetch(
                        video_id,
                        languages=['pt', 'pt-BR', 'en']
                        )
                except:
                    return None

            # ==============================
            # NORMALIZAÇÃO
            # ==============================
            normalized = []

            for item in data:
                normalized.append({
                    "text": item["text"],
                    "start": item["start"],
                    "duration": item.get("duration", 0)
                    })

            return normalized

        except Exception as e:
            print("ERRO TRANSCRIPT:", e)
            return None

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