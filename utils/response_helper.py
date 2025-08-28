class ResponseHelper:
    """Helper class for handling HTTP responses"""
    
    @staticmethod
    def get_cors_headers():
        """Get CORS headers for all responses"""
        return {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
    
    @staticmethod
    def create_options_response():
        """Create OPTIONS response for CORS preflight"""
        return {
            'statusCode': 200,
            'headers': ResponseHelper.get_cors_headers(),
            'body': ''
        }
    
    @staticmethod
    def create_twiml_response(mensagem):
        """Create TwiML response for Twilio"""
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{mensagem}</Message>
</Response>"""
        
        headers = ResponseHelper.get_cors_headers()
        headers['Content-Type'] = 'application/xml'
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': twiml_response
        }