import logging
from datetime import datetime, timedelta
from repositories.expense_repository import ExpenseRepository
from services.gemini_service import GeminiService
from utils.date_helper import DateHelper

logger = logging.getLogger()

class ReportService:
    """Service to handle expense reports and queries"""
    
    def __init__(self):
        self.repository = ExpenseRepository()
        self.gemini_service = GeminiService()
        self.date_helper = DateHelper()
    
    def process_query(self, texto, nome_usuario, interpretacao):
        """Process queries using Gemini interpretation"""
        agora = datetime.now()
        
        # Determine period and dates
        periodo_info, inicio_data, fim_data, titulo, periodo = self._get_period_info(
            interpretacao, agora
        )
        
        # Determine if it's personal or family query
        is_consulta_familia = interpretacao.get('escopo', 'individual') == 'familiar'
        
        # Search expenses
        despesas = self.repository.search_expenses(
            inicio_data, fim_data, 
            None if is_consulta_familia else nome_usuario
        )
        
        if not despesas:
            return f"""{titulo}

❌ Nenhuma despesa encontrada neste período.

💡 *Dica:* Registre gastos por texto ou áudio: "gastei 50 reais no almoço" """
        
        # Generate basic report
        relatorio_basico = self._generate_report(despesas, titulo, is_consulta_familia)
        
        # Generate insight with AI
        insight = self.gemini_service.generate_insights(
            despesas, titulo, is_consulta_familia, periodo
        )
        
        # Combine report with insight
        return f"""{relatorio_basico}

🤖 *Insight Inteligente (IA Gemini):*
{insight}"""
    
    def _get_period_info(self, interpretacao, agora):
        """Get period information based on interpretation"""
        periodo_info = interpretacao.get('periodo', 'mes_atual')
        
        if periodo_info == 'semana_atual':
            inicio_semana = agora - timedelta(days=agora.weekday())
            inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
            inicio_data = inicio_semana.isoformat()
            fim_data = agora.isoformat()
            titulo = "📅 *Relatório da Semana*"
            periodo = "semana atual"
        
        elif periodo_info == 'mes_especifico' and interpretacao.get('mes_especifico'):
            mes = interpretacao['mes_especifico']
            inicio_mes = datetime(agora.year, mes, 1)
            if mes == 12:
                fim_mes = datetime(agora.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                fim_mes = datetime(agora.year, mes + 1, 1) - timedelta(seconds=1)
            inicio_data = inicio_mes.isoformat()
            fim_data = fim_mes.isoformat()
            titulo = f"📅 *Relatório de {self.date_helper.get_month_name(mes - 1)}*"
            periodo = f"mês de {self.date_helper.get_month_name(mes - 1).lower()}"
        
        else:  # mes_atual (default)
            inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            inicio_data = inicio_mes.isoformat()
            fim_data = agora.isoformat()
            titulo = f"📅 *Relatório de {self.date_helper.get_month_name(agora.month - 1)}*"
            periodo = f"mês de {self.date_helper.get_month_name(agora.month - 1).lower()}"
        
        return periodo_info, inicio_data, fim_data, titulo, periodo
    
    def _generate_report(self, despesas, titulo, is_consulta_familia):
        """Generate formatted report"""
        # Calculate totals
        total_geral = sum(float(item.get('valor', 0)) for item in despesas)
        
        # Group by category
        por_categoria = {}
        for despesa in despesas:
            cat = despesa.get('categoria', 'outros')
            if cat not in por_categoria:
                por_categoria[cat] = {'total': 0, 'count': 0}
            por_categoria[cat]['total'] += float(despesa.get('valor', 0))
            por_categoria[cat]['count'] += 1
        
        # Group by user (if family query)
        por_usuario = {}
        if is_consulta_familia:
            for despesa in despesas:
                user = despesa.get('user_id', 'desconhecido')
                if user not in por_usuario:
                    por_usuario[user] = 0
                por_usuario[user] += float(despesa.get('valor', 0))
        
        emojis = {
            'alimentacao': '🍽️',
            'transporte': '🚗',
            'saude': '🏥',
            'lazer': '🎬',
            'outros': '📝'
        }
        
        relatorio = f"{titulo}\n\n"
        
        # General total
        relatorio += f"💰 *Total:* R$ {total_geral:.2f}\n"
        relatorio += f"📊 *{len(despesas)} despesas registradas*\n\n"
        
        # By category
        relatorio += "📋 *Por Categoria:*\n"
        for categoria, dados in sorted(por_categoria.items(), key=lambda x: x[1]['total'], reverse=True):
            emoji = emojis.get(categoria, '📝')
            porcentagem = (dados['total'] / total_geral * 100) if total_geral > 0 else 0
            relatorio += f"{emoji} {categoria}: R$ {dados['total']:.2f} ({porcentagem:.1f}%)\n"
        
        # By user (if family)
        if is_consulta_familia and len(por_usuario) > 1:
            relatorio += "\n👥 *Por Pessoa:*\n"
            for usuario, total in sorted(por_usuario.items(), key=lambda x: x[1], reverse=True):
                porcentagem = (total / total_geral * 100) if total_geral > 0 else 0
                relatorio += f"• {usuario}: R$ {total:.2f} ({porcentagem:.1f}%)\n"
        
        return relatorio