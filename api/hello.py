import json
import datetime

def handler(request):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS (preflight) request
    if request.method == 'OPTIONS':
        return ('', 200, headers)
    
    # Handle GET request
    if request.method == 'GET':
        response_data = {
            "message": "Hello from Python on Vercel!",
            "status": "working",
            "timestamp": datetime.datetime.now().isoformat(),
            "project": "CFRP Monitor",
            "version": "1.0.0"
        }
        
        return (
            json.dumps(response_data, ensure_ascii=False),
            200,
            headers
        )
    
    return (
        json.dumps({"error": "Method not allowed"}),
        405,
        headers
    )