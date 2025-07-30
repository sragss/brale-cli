#!/usr/bin/env python3
# https://docs.brale.xyz/guides/fiat-to-stablecoin-onramp

import os
import base64
import requests
import json
import uuid
from dotenv import load_dotenv

def main():
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
    
    # Get accounts
    accounts_response = requests.get(
        "https://api.brale.xyz/accounts",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if accounts_response.status_code != 200:
        print(f"Error getting accounts: {accounts_response.text}")
        return
    
    accounts_data = accounts_response.json()
    account_id = accounts_data["accounts"][0]
    print(f"Account ID: {account_id}")
    
    # Get addresses to find Base address for USDC
    addresses_response = requests.get(
        f"https://api.brale.xyz/accounts/{account_id}/addresses",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if addresses_response.status_code != 200:
        print(f"Error getting addresses: {addresses_response.text}")
        return
    
    addresses_data = addresses_response.json()
    
    # Find Base address
    base_address_id = None
    for addr in addresses_data["addresses"]:
        if addr['status'] == 'active' and 'base' in addr['transfer_types']:
            base_address_id = addr['id']
            print(f"Found Base address: {addr['address']} (ID: {base_address_id})")
            break
    
    if not base_address_id:
        print("Error: No active Base address found")
        return
    
    # Create fiat-to-stablecoin automation
    print(f"\nCreating fiat-to-stablecoin automation...")
    
    automation_data = {
        "name": "Test USDC Base Automation",
        "type": "USD",
        "destination": {
            "address_id": base_address_id,
            "value_type": "USDC",
            "transfer_type": "base"
        }
    }
    
    print(f"Automation request body:")
    print(json.dumps(automation_data, indent=2))
    print()
    
    automation_response = requests.post(
        f"https://api.brale.xyz/accounts/{account_id}/automations",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        },
        json=automation_data
    )
    
    if automation_response.status_code not in [200, 201]:
        print(f"Error creating automation: {automation_response.status_code}")
        print(automation_response.text)
        return
    
    automation_result = automation_response.json()
    print(f"Automation created successfully!")
    
    print(f"\nFull response:")
    print(json.dumps(automation_result, indent=2))

if __name__ == "__main__":
    main()