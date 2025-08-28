import json
import logging
import requests
from config.settings import GEMINI_API_KEY, GEMINI_URL

logger = logging.getLogger()

class GeminiService:
    """Service to handle Gemini AI interactions"""
    
    def interpret_message(self, texto_mensagem):
        """Use Gemini to interpret message type and extract relevant data"""
        try:
            prompt = f"""Analise a seguinte mensagem de WhatsApp e determine se é:
1. DESPESA: usuário relatando um gasto
2. CONSULTA: usuário pedindo relatório/informações sobre gastos
3. AJUDA: mensagem que não se encaixa nas anteriores

Mensagem: "{texto_mensagem}"

Se for DESPESA, extraia:
- Valor gasto (apenas número, sem texto)
- Categoria (alimentacao, transporte, saude, lazer, outros)
- Descrição resumida do gasto

Se for CONSULTA, identifique:
- Período solicitado (semana_atual, mes_atual, mes_especifico)
- Se é consulta individual ou familiar
- Mês específico se mencionado (1-12)

Responda APENAS com um JSON válido no formato:

Para DESPESA:
{{
    "tipo": "despesa",
    "valor": 50.0,
    "categoria": "alimentacao",
    "descricao": "almoço no restaurante"
}}

Para CONSULTA:
{{
    "tipo": "consulta",
    "periodo": "mes_atual",
    "escopo": "individual",
    "mes_especifico": null
}}

Para AJUDA:
{{
    "tipo": "ajuda"
}}

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional."""
            
            response = self._call_gemini(prompt, max_tokens=200, temperature=0.1)
            
            if response:
                # Clean response and parse JSON
                clean_response = response.replace('```json', '').replace('```', '').strip()
                logger.info(f'Gemini interpretation: {clean_response}')
                return json.loads(clean_response)
            
            # Fallback
            logger.warning("Could not interpret message with Gemini, using fallback")
            return {"tipo": "ajuda"}
            
        except json.JSONDecodeError as error:
            logger.error(f'Error parsing Gemini JSON response: {str(error)}')
            return {"tipo": "ajuda"}
        except Exception as error:
            logger.error(f'Error interpreting message: {str(error)}')
            return {"tipo": "ajuda"}
    
    def generate_insights(self, despesas, titulo, is_consulta_familia, periodo):
        """Generate insights with Gemini API"""
        try:
            # Prepare data for analysis
            total_geral = sum(float(item.get('valor', 0)) for item in despesas)
            
            # Group by category
            por_categoria = {}
            for despesa in despesas:
                cat = despesa.get('categoria', 'outros')
                if cat not in por_categoria:
                    por_categoria[cat] = {'total': 0, 'count': 0}
                por_categoria[cat]['total'] += float(despesa.get('valor', 0))
                por_categoria[cat]['count'] += 1
            
            # Group by user if family query
            por_usuario = {}
            if is_consulta_familia:
                for despesa in despesas:
                    user = despesa.get('user_id', 'desconhecido')
                    if user not in por_usuario:
                        por_usuario[user] = 0
                    por_usuario[user] += float(despesa.get('valor', 0))
            
            # Build analysis prompt
            prompt = self._build_insights_prompt(
                por_categoria, por_usuario, despesas, 
                total_geral, periodo, is_consulta_familia
            )
            
            insight = self._call_gemini(prompt, max_tokens=500, temperature=0.7)
            
            if insight:
                logger.info(f'Generated detailed insight: {insight[:200]}...')
                return insight
            
            return "💡 Continue registrando suas despesas para obter insights personalizados da IA!"
            
        except Exception as error:
            logger.error(f'Error generating AI insight: {str(error)}')
            return "💡 Continue registrando suas despesas para obter insights personalizados da IA!"
    
    def _build_insights_prompt(self, por_categoria, por_usuario, despesas, total_geral, periodo, is_consulta_familia):
        """Build comprehensive prompt for insights generation"""
        # Prepare category data
        categorias = []
        for cat, dados in sorted(por_categoria.items(), key=lambda x: x[1]['total'], reverse=True):
            categorias.append({
                'categoria': cat,
                'total': dados['total'],
                'quantidade': dados['count'],
                'porcentagem': f"{(dados['total'] / total_geral * 100):.1f}" if total_geral > 0 else "0.0"
            })
        
        # Prepare user data
        usuarios = []
        if is_consulta_familia:
            for user, total in sorted(por_usuario.items(), key=lambda x: x[1], reverse=True):
                usuarios.append({
                    'usuario': user,
                    'total': total,
                    'porcentagem': f"{(total / total_geral * 100):.1f}" if total_geral > 0 else "0.0"
                })
        
        # Format data for prompt
        categorias_text = '\n'.join([
            f"- {c['categoria']}: R$ {c['total']:.2f} ({c['porcentagem']}%) - {c['quantidade']} despesas"
            for c in categorias
        ])
        
        usuarios_text = ""
        if is_consulta_familia and len(usuarios) > 1:
            usuarios_text = f"\n\nGastos por pessoa:\n" + '\n'.join([
                f"- {u['usuario']}: R$ {u['total']:.2f} ({u['porcentagem']}%)"
                for u in usuarios
            ])
        
        # Recent expenses context
        despesas_recentes = ""
        if despesas:
            detalhes_despesas = despesas[-10:]  # Last 10 expenses
            despesas_recentes = f"\n\nÚltimas despesas registradas:\n" + '\n'.join([
                f"- {d.get('categoria', 'outros')}: R$ {float(d.get('valor', 0)):.2f} - {d.get('descricao', '')[:30]}..."
                for d in detalhes_despesas
            ])
        
        return f"""Analise detalhadamente os dados de despesas e forneça insights úteis e práticos em português brasileiro:

Período analisado: {periodo}
Total gasto: R$ {total_geral:.2f}
Número de despesas: {len(despesas)}
Tipo de análise: {'Família' if is_consulta_familia else 'Individual'}

Distribuição por categoria:
{categorias_text}{usuarios_text}{despesas_recentes}

Como especialista em finanças pessoais, forneça 3 insights práticos e específicos (máximo 4 linhas cada):

1. **Padrão Principal:** Qual o padrão mais importante identificado nos gastos?
2. **Oportunidade de Economia:** Onde há maior potencial de redução de custos?
3. **Recomendação Estratégica:** Qual ação concreta recomenda para otimizar os gastos?

Só traga os insights, sem conclusão ou resumo, seja prático e focado nos dados apresentados. Use emojis relevantes."""
    
    def _call_gemini(self, prompt, max_tokens=1000, temperature=0.7):
        """Generic method to call Gemini API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    return candidate['content']['parts'][0]['text'].strip()
            
            return None
            
        except requests.exceptions.RequestException as error:
            logger.error(f'Error calling Gemini API: {str(error)}')
            return None