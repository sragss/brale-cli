#!/usr/bin/env python3

import os
import base64
import requests
import json
import sys
from dotenv import load_dotenv

def main():
    # Check for command line arguments
    if len(sys.argv) != 3:
        print("Usage: python automation_status.py <account_id> <automation_id>")
        print("Example: python automation_status.py 30Z94Xpsu7XFo54BjnAkitL9CCw 30b41dv38AsBH9Ci2kys2YRItY0")
        return
    
    account_id = sys.argv[1]
    automation_id = sys.argv[2]
    
    # Load environment variables
    load_dotenv()
    
    client_id = os.getenv('BRALE_CLIENT_ID')
    client_secret = os.getenv('BRALE_SECRET')
    
    if not client_id or not client_secret:
        print("Error: BRALE_CLIENT_ID and BRALE_SECRET must be set in .env file")
        return
    
    # Get OAuth token
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    token_response = requests.post(
        "https://auth.brale.xyz/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    
    if token_response.status_code != 200:
        print(f"Error getting token: {token_response.text}")
        return
    
    token_data = token_response.json()
    access_token = token_data["access_token"]
    print(f"Token obtained successfully")
    
    # Get automation status
    print(f"Getting status for automation {automation_id}...")
    
    automation_response = requests.get(
        f"https://api.brale.xyz/accounts/{account_id}/automations/{automation_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if automation_response.status_code != 200:
        print(f"Error getting automation: {automation_response.status_code}")
        print(automation_response.text)
        return
    
    automation_data = automation_response.json()
    
    print(f"\nAutomation Status:")
    print("=" * 40)
    print(f"ID: {automation_data['id']}")
    print(f"Name: {automation_data['name']}")
    print(f"Status: {automation_data['status']}")
    
    if 'created_at' in automation_data:
        print(f"Created: {automation_data['created_at']}")
    if 'updated_at' in automation_data:
        print(f"Updated: {automation_data['updated_at']}")
    
    print(f"\nDestination:")
    dest = automation_data['destination']
    print(f"  Type: {dest['value_type']} via {dest['transfer_type']}")
    print(f"  Address ID: {dest['address_id']}")
    
    if 'wire_instructions' in automation_data:
        print(f"\nWire Instructions:")
        instructions = automation_data['wire_instructions']
        print(f"  Beneficiary Name: {instructions['beneficiary_name']}")
        print(f"  Bank Name: {instructions['bank_name']}")
        print(f"  Account Number: {instructions['account_number']}")
        print(f"  Routing Number: {instructions['routing_number']}")
        if instructions.get('memo'):
            print(f"  Memo: {instructions['memo']}")
    
    print(f"\nFull response:")
    print(json.dumps(automation_data, indent=2))

if __name__ == "__main__":
    main()