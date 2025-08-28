import logging
from datetime import datetime
from decimal import Decimal
from repositories.expense_repository import ExpenseRepository

logger = logging.getLogger()

class ExpenseService:
    """Service to handle expense processing"""
    
    def __init__(self):
        self.repository = ExpenseRepository()
    
    def process_expense(self, mensagem, interpretacao):
        """Process expense using Gemini interpretation"""
        try:
            # Prepare expense data
            dados_despesa = {
                'timestamp': datetime.now().isoformat(),
                'valor': Decimal(str(interpretacao.get('valor', 0))),
                'categoria': interpretacao.get('categoria', 'outros'),
                'descricao': interpretacao.get('descricao', mensagem.get('texto', '')),
                'user_id': mensagem.get('profileName', 'desconhecido'),
                'whatsapp_from': mensagem.get('from', ''),
                'data_criacao': datetime.now().isoformat()
            }
            
            # Save to DynamoDB
            self.repository.save_expense(dados_despesa)
            
            # Format response
            return self._format_expense_response(dados_despesa, mensagem)
            
        except Exception as error:
            logger.error(f'Error processing expense with Gemini: {str(error)}')
            raise
    
    def _format_expense_response(self, dados_despesa, mensagem):
        """Format expense confirmation message"""
        data_formatada = datetime.fromisoformat(dados_despesa['timestamp']).strftime('%d/%m/%Y %H:%M')
        
        categoria_emoji = {
            'alimentacao': '🍽️',
            'transporte': '🚗',
            'saude': '🏥',
            'lazer': '🎬',
            'outros': '📝'
        }
        
        emoji = categoria_emoji.get(dados_despesa['categoria'], '📝')
        valor = float(dados_despesa['valor'])
        
        # Add audio indicator if it was converted from audio
        audio_indicator = "🎤➡️📝 " if mensagem.get('numMedia', 0) > 0 else ""
        
        return f"""✅ {audio_indicator}Despesa registrada com IA!

📊 *Detalhes:*
• Valor: R$ {valor:.2f}
• Categoria: {emoji} {dados_despesa['categoria']}
• Descrição: {dados_despesa['descricao']}
• Data: {data_formatada}

🤖 *Processado automaticamente pela IA Gemini*
💬 *Dica:* Envie áudios ou textos - eu entendo os dois!"""