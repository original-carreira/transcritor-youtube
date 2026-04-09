from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeClient:
    """Responsável por acessar o YouTube e obter a transcrição."""

    def fetch_transcript(self, video_id: str):
        """Obtém transcript do vídeo via API externa."""
        api = YouTubeTranscriptApi()

        transcript = api.fetch(
            video_id,
            languages=['pt', 'pt-BR', 'en']
        )

        if not transcript:
            return None

        return transcript