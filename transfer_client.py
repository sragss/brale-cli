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
    
    # Get addresses
    addresses_response = requests.get(
        f"https://api.brale.xyz/accounts/{account_id}/addresses",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if addresses_response.status_code != 200:
        print(f"Error getting addresses: {addresses_response.text}")
        return
    
    addresses_data = addresses_response.json()
    
    print("\nAddresses:")
    print("=" * 50)
    
    # Find the Base-compatible address
    base_address_id = None
    for addr in addresses_data["addresses"]:
        print(f"ID: {addr['id']}")
        print(f"Status: {addr['status']}")
        print(f"Address: {addr.get('address', 'N/A')}")
        print(f"Transfer Types: {', '.join(addr['transfer_types'])}")
        
        if addr['status'] == 'active' and 'base' in addr['transfer_types']:
            base_address_id = addr['id']
            print(f"  ^^ This will be used for Base SBC transfer")
        
        print("-" * 30)
    
    if not base_address_id:
        print("Error: No active Base-compatible address found")
        return
    
    # Create transfer from Wire to Base SBC
    print(f"\nCreating Wire to Base SBC transfer...")
    
    transfer_data = {
        "amount": {"value": "10", "currency": "USD"},
        "source": {"value_type": "USD", "transfer_type": "wire"},
        "destination": {
            "address_id": base_address_id,
            "value_type": "SBC",
            "transfer_type": "base"
        }
    }
    
    print(f"Transfer request body:")
    print(json.dumps(transfer_data, indent=2))
    print()
    
    transfer_response = requests.post(
        f"https://api.brale.xyz/accounts/{account_id}/transfers",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        },
        json=transfer_data
    )
    
    if transfer_response.status_code not in [200, 201]:
        print(f"Error creating transfer: {transfer_response.status_code}")
        print(transfer_response.text)
        return
    
    transfer_result = transfer_response.json()
    print(f"Transfer created successfully!")
    print(f"Transfer ID: {transfer_result['id']}")
    print(f"Status: {transfer_result['status']}")
    print(f"Amount: ${transfer_result['amount']['value']} {transfer_result['amount']['currency']}")
    
    if 'wire_instructions' in transfer_result:
        print("\nWire Instructions:")
        print(json.dumps(transfer_result['wire_instructions'], indent=2))

if __name__ == "__main__":
    main()