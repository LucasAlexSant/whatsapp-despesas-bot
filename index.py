import json
import logging
from urllib.parse import parse_qs
from datetime import datetime

from services.audio_service import AudioService
from services.gemini_service import GeminiService
from services.expense_service import ExpenseService
from services.report_service import ReportService
from utils.response_helper import ResponseHelper

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main Lambda handler function"""
    logger.info(f'Event received: {json.dumps(event)}')
    
    # CORS headers for all responses
    headers = ResponseHelper.get_cors_headers()
    
    # Handle OPTIONS requests (preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return ResponseHelper.create_options_response()
    
    try:
        # Parse message from Twilio or test event
        mensagem = _parse_message(event)
        
        # Handle audio messages
        if _is_audio_message(mensagem):
            audio_service = AudioService()
            texto_convertido = audio_service.convert_to_text(mensagem['mediaUrl'])
            
            if not texto_convertido:
                return ResponseHelper.create_twiml_response(
                    "🎤 Desculpe, não consegui entender o áudio. Tente enviar uma mensagem de texto ou grave novamente com mais clareza."
                )
            
            mensagem['texto'] = texto_convertido
        
        texto_mensagem = mensagem.get('texto', '').strip()
        
        if not texto_mensagem:
            return ResponseHelper.create_twiml_response(
                "❌ Não recebi nenhuma mensagem de texto ou áudio válido. Tente novamente!"
            )
        
        # Use Gemini to interpret the message
        gemini_service = GeminiService()
        interpretacao = gemini_service.interpret_message(texto_mensagem)
        
        # Process based on interpretation
        if interpretacao['tipo'] == 'despesa':
            expense_service = ExpenseService()
            resposta = expense_service.process_expense(mensagem, interpretacao)
        elif interpretacao['tipo'] == 'consulta':
            report_service = ReportService()
            resposta = report_service.process_query(texto_mensagem, mensagem.get('profileName', ''), interpretacao)
        else:
            resposta = _generate_help_message()
        
        return ResponseHelper.create_twiml_response(resposta)
    
    except Exception as error:
        logger.error(f'Error: {str(error)}', exc_info=True)
        return ResponseHelper.create_twiml_response("❌ Ops! Algo deu errado. Tente novamente em alguns segundos.")


def _parse_message(event):
    """Parse message from Twilio data or test event"""
    if event.get('body'):
        params = parse_qs(event['body'])
        return {
            'texto': params.get('Body', [''])[0],
            'from': params.get('From', [''])[0],
            'profileName': params.get('ProfileName', [''])[0],
            'mediaUrl': params.get('MediaUrl0', [''])[0] if params.get('MediaUrl0') else None,
            'mediaContentType': params.get('MediaContentType0', [''])[0] if params.get('MediaContentType0') else None,
            'numMedia': int(params.get('NumMedia', ['0'])[0])
        }
    else:
        return event


def _is_audio_message(mensagem):
    """Check if message contains audio"""
    return (mensagem.get('numMedia', 0) > 0 and 
            mensagem.get('mediaContentType', '').startswith('audio/'))


def _generate_help_message():
    """Generate help message"""
    return """🤖 *Olá! Sou seu assistente de despesas com IA Gemini!*

🧠 *Inteligência Artificial Avançada:*
• Entendo linguagem natural e áudios 🎤
• Classifico automaticamente suas despesas
• Gero insights personalizados

📝 *Exemplos de mensagens (texto ou áudio):*
• "gastei uns 40 reais em comida hoje"
• "paguei 120 no supermercado"
• "almoço custou 25 reais"
• "uber foi 35 reais"

📊 *Para relatórios inteligentes:*
• "quanto gastei este mês?"
• "relatório da semana"
• "gastos de junho"
• "quanto a família gastou?"

🎯 *Categorias automáticas com IA:*
🍽️ Alimentação • 🚗 Transporte
🏥 Saúde • 🎬 Lazer • 📝 Outros

🎤 *Novidade:* Agora você pode mandar áudios também!
"""