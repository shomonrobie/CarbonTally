# backend/tests/export_postman.py
"""
Export test endpoints to Postman collection
"""

import json
from pathlib import Path

def export_to_postman():
    """Export API endpoints to Postman collection"""
    
    collection = {
        "info": {
            "name": "CarbonTally API Tests",
            "description": "Complete API test collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "auth_token",
                "value": "",
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": '{"email": "{{test_email}}", "password": "{{test_password}}"}'
                            },
                            "url": {
                                "raw": "{{base_url}}/api/auth/login"
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    with open("CarbonTally_API_Tests.postman_collection.json", "w") as f:
        json.dump(collection, f, indent=2)
    
    print("✅ Postman collection exported!")

if __name__ == "__main__":
    export_to_postman()