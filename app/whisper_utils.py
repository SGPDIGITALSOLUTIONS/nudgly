"""Voice note transcription utilities using OpenAI Whisper."""

import io
import tempfile
from typing import Optional
import requests
from openai import OpenAI
from twilio.rest import Client

from .settings import OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN


class VoiceTranscriber:
    """Handles voice note downloading and transcription."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    def transcribe_voice_note(self, media_url: str, content_type: str) -> Optional[str]:
        """Download and transcribe a voice note from Twilio."""
        if not self.openai_client:
            print("OpenAI API key not configured")
            return None
        
        # Check if it's an audio file
        if not content_type.startswith('audio/'):
            print(f"Not an audio file: {content_type}")
            return None
        
        try:
            # Download the audio file
            audio_data = self._download_media(media_url)
            if not audio_data:
                return None
            
            # Transcribe using Whisper
            return self._transcribe_audio(audio_data, content_type)
            
        except Exception as e:
            print(f"Error transcribing voice note: {e}")
            return None
    
    def _download_media(self, media_url: str) -> Optional[bytes]:
        """Download media file from Twilio."""
        try:
            # Twilio media URLs require authentication
            response = requests.get(
                media_url,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                timeout=30
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading media: {e}")
            return None
    
    def _transcribe_audio(self, audio_data: bytes, content_type: str) -> Optional[str]:
        """Transcribe audio data using OpenAI Whisper."""
        try:
            # Determine file extension from content type
            extension = self._get_file_extension(content_type)
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Transcribe using Whisper
                with open(temp_file.name, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"  # Can be removed to auto-detect
                    )
                
                return transcript.text.strip()
                
        except Exception as e:
            print(f"Error in Whisper transcription: {e}")
            return None
    
    def _get_file_extension(self, content_type: str) -> str:
        """Get file extension from content type."""
        content_type_map = {
            'audio/ogg': '.ogg',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.mp4',
            'audio/wav': '.wav',
            'audio/webm': '.webm',
            'audio/x-m4a': '.m4a'
        }
        return content_type_map.get(content_type, '.ogg')


# Global transcriber instance
transcriber = VoiceTranscriber()


async def transcribe_if_voice(form_data) -> str:
    """
    Check if the message contains voice notes and transcribe them.
    Returns transcribed text or original body text.
    """
    body = form_data.get("Body", "")
    media_count = int(form_data.get("NumMedia", 0))
    
    if media_count == 0:
        return body
    
    # Process first media item (voice note)
    media_url = form_data.get("MediaUrl0")
    content_type = form_data.get("MediaContentType0", "")
    
    if not media_url:
        return body
    
    # Try to transcribe the voice note
    transcribed_text = transcriber.transcribe_voice_note(media_url, content_type)
    
    if transcribed_text:
        # If we have both body text and transcription, combine them
        if body.strip():
            return f"{body} {transcribed_text}"
        return transcribed_text
    
    # If transcription failed, return original body or indicate voice note received
    return body if body.strip() else "Voice note received (transcription failed)"


def download_and_transcribe(media_url: str, content_type: str) -> Optional[str]:
    """Direct function to download and transcribe a voice note."""
    return transcriber.transcribe_voice_note(media_url, content_type)

