from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeClient:
    """Responsável por acessar o YouTube e obter a transcrição."""
    
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
            except (TypeError, KeyError, AttributeError):
                normalized.append({
                    "text": item.text,
                    "start": item.start,
                    "duration": getattr(item, "duration", 0)
                })
                
        return normalized