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
        print("Usage: python transfer_status.py <account_id> <transfer_id>")
        print("Example: python transfer_status.py 30Z94Xpsu7XFo54BjnAkitL9CCw 30bf1wZEgp58gHKubmtvuqTsFLS")
        return
    
    account_id = sys.argv[1]
    transfer_id = sys.argv[2]
    
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
    
    # Get transfer status
    print(f"Getting status for transfer {transfer_id}...")
    
    transfer_response = requests.get(
        f"https://api.brale.xyz/accounts/{account_id}/transfers/{transfer_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if transfer_response.status_code != 200:
        print(f"Error getting transfer: {transfer_response.status_code}")
        print(transfer_response.text)
        return
    
    transfer_data = transfer_response.json()
    
    print(f"\nTransfer Status:")
    print("=" * 40)
    print(f"ID: {transfer_data['id']}")
    print(f"Status: {transfer_data['status']}")
    print(f"Amount: ${transfer_data['amount']['value']} {transfer_data['amount']['currency']}")
    print(f"Created: {transfer_data['created_at']}")
    print(f"Updated: {transfer_data['updated_at']}")
    
    print(f"\nSource:")
    source = transfer_data['source']
    print(f"  Type: {source['value_type']} via {source['transfer_type']}")
    
    print(f"\nDestination:")
    dest = transfer_data['destination']
    print(f"  Type: {dest['value_type']} via {dest['transfer_type']}")
    print(f"  Address ID: {dest['address_id']}")
    
    if transfer_data.get('note'):
        print(f"\nNote: {transfer_data['note']}")
    
    print(f"\nFull response:")
    print(json.dumps(transfer_data, indent=2))

if __name__ == "__main__":
    main()