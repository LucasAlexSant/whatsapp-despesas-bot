import os
import base64
import logging
import requests
from config.settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, GEMINI_API_KEY, GEMINI_URL

logger = logging.getLogger()

class AudioService:
    """Service to handle audio conversion to text"""
    
    def convert_to_text(self, media_url):
        """Convert WhatsApp audio to text using Gemini API"""
        try:
            # Download audio from Twilio
            logger.info(f"Downloading audio from: {media_url}")
            
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            response = requests.get(media_url, auth=auth, timeout=30)
            response.raise_for_status()
            
            audio_content = response.content
            logger.info(f"Audio downloaded, size: {len(audio_content)} bytes")
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            content_type = response.headers.get('content-type', 'audio/ogg')
            
            # Transcribe with Gemini
            transcription = self._transcribe_with_gemini(audio_base64, content_type)
            
            if transcription:
                logger.info(f'Audio transcribed successfully: {transcription}')
            
            return transcription
            
        except requests.exceptions.RequestException as error:
            logger.error(f'Error downloading audio or calling Gemini API: {str(error)}')
            return None
        except Exception as error:
            logger.error(f'Error converting audio to text: {str(error)}')
            return None
    
    def _transcribe_with_gemini(self, audio_base64, content_type):
        """Send audio to Gemini for transcription"""
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Transcreva este áudio em português brasileiro. Responda APENAS com o texto transcrito, sem comentários adicionais."
                        },
                        {
                            "inlineData": {
                                "mimeType": content_type,
                                "data": audio_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        logger.info("Sending audio to Gemini for transcription...")
        
        response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract transcription
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                return candidate['content']['parts'][0]['text'].strip()
        
        logger.warning("No transcription found in Gemini response")
        return None