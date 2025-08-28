class DateHelper:
    """Helper class for date operations"""
    
    @staticmethod
    def get_month_name(numero_mes):
        """Get month name in Portuguese"""
        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return meses[numero_mes] if 0 <= numero_mes < 12 else 'Mês'