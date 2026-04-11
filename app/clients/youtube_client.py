from youtube_transcript_api import YouTubeTranscriptApi

import requests
import re

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
    
    
    def fetch_video_metadata(self, video_id: str):
        """ Obtém título e thumbnails do vídeo. """
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