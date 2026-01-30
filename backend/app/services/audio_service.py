"""
Audio Transcription Service - Whisper Integration
Transcrição de áudio usando OpenAI Whisper
"""
import os
import tempfile
from typing import Optional, Dict, Any
import structlog
import httpx

from app.core.config import settings

logger = structlog.get_logger()


class AudioTranscriptionService:
    """Serviço de transcrição de áudio com Whisper."""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.whisper_model = "whisper-1"
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.ogg",
        language: str = "pt"
    ) -> Optional[str]:
        """
        Transcreve áudio usando OpenAI Whisper API.
        
        Args:
            audio_data: Dados binários do áudio
            filename: Nome do arquivo (com extensão)
            language: Código do idioma (pt, en, etc.)
        
        Returns:
            Texto transcrito ou None se falhar
        """
        if not self.openai_api_key:
            logger.warning("openai_api_key_not_configured")
            # Fallback: retorna mensagem informativa
            return "[Áudio recebido - transcrição não configurada]"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepara o arquivo para upload
                files = {
                    "file": (filename, audio_data, "audio/ogg"),
                    "model": (None, self.whisper_model),
                    "language": (None, language),
                    "response_format": (None, "text")
                }
                
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}"
                    },
                    files=files
                )
                
                if response.status_code == 200:
                    transcription = response.text.strip()
                    logger.info("audio_transcribed", 
                              length=len(transcription),
                              language=language)
                    return transcription
                else:
                    logger.error("whisper_api_error", 
                               status=response.status_code,
                               response=response.text[:200])
                    return None
                    
        except Exception as e:
            logger.error("audio_transcription_failed", error=str(e))
            return None
    
    async def transcribe_from_telegram(
        self,
        file_id: str,
        bot_token: str
    ) -> Optional[str]:
        """
        Baixa e transcreve áudio do Telegram.
        
        Args:
            file_id: ID do arquivo no Telegram
            bot_token: Token do bot
            
        Returns:
            Texto transcrito
        """
        try:
            async with httpx.AsyncClient() as client:
                # Obtém informações do arquivo
                file_info = await client.get(
                    f"https://api.telegram.org/bot{bot_token}/getFile",
                    params={"file_id": file_id}
                )
                
                if file_info.status_code != 200:
                    logger.error("telegram_get_file_failed")
                    return None
                
                file_path = file_info.json().get("result", {}).get("file_path")
                if not file_path:
                    return None
                
                # Baixa o arquivo
                file_response = await client.get(
                    f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                )
                
                if file_response.status_code != 200:
                    logger.error("telegram_download_failed")
                    return None
                
                audio_data = file_response.content
                
                # Transcreve
                return await self.transcribe_audio(
                    audio_data,
                    filename=file_path.split("/")[-1]
                )
                
        except Exception as e:
            logger.error("telegram_audio_failed", error=str(e))
            return None
    
    async def transcribe_from_url(self, audio_url: str) -> Optional[str]:
        """
        Baixa áudio de URL e transcreve.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(audio_url)
                if response.status_code == 200:
                    return await self.transcribe_audio(
                        response.content,
                        filename="audio.ogg"
                    )
        except Exception as e:
            logger.error("url_audio_failed", error=str(e))
        
        return None


# Singleton
audio_service = AudioTranscriptionService()
