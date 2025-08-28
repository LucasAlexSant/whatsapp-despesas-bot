import logging
import boto3
from config.settings import DYNAMODB_TABLE_NAME

logger = logging.getLogger()

class ExpenseRepository:
    """Repository to handle DynamoDB operations for expenses"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(DYNAMODB_TABLE_NAME)
    
    def save_expense(self, dados):
        """Save expense to DynamoDB"""
        try:
            logger.info(f'Saving to DynamoDB: {dados}')
            resultado = self.table.put_item(Item=dados)
            logger.info(f'Expense saved successfully: {resultado}')
            return resultado
        except Exception as error:
            logger.error(f'Error saving expense: {str(error)}')
            raise
    
    def search_expenses(self, inicio_data, fim_data, usuario=None):
        """Search expenses in DynamoDB"""
        try:
            filter_expression = "attribute_exists(#timestamp) AND #timestamp BETWEEN :inicio AND :fim"
            expression_attribute_names = {'#timestamp': 'timestamp'}
            expression_attribute_values = {':inicio': inicio_data, ':fim': fim_data}
            
            if usuario:
                filter_expression += " AND #user_id = :usuario"
                expression_attribute_names['#user_id'] = 'user_id'
                expression_attribute_values[':usuario'] = usuario
            
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            return response.get('Items', [])
        except Exception as error:
            logger.error(f'Error searching expenses: {str(error)}')
            return []