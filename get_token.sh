#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Check if required variables are set
if [ -z "$BRALE_CLIENT_ID" ] || [ -z "$BRALE_SECRET" ]; then
    echo "Error: BRALE_CLIENT_ID and BRALE_SECRET must be set in .env file"
    exit 1
fi

# Create base64 encoded credentials
CREDENTIALS=$(echo -n "$BRALE_CLIENT_ID:$BRALE_SECRET" | base64)

# Get the token
TOKEN_RESPONSE=$(curl --silent --request POST \
  --url https://auth.brale.xyz/oauth2/token \
  --header "Authorization: Basic $CREDENTIALS" \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data grant_type=client_credentials)

# Extract access token from JSON response
AUTH_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$AUTH_TOKEN" ]; then
    echo "Error: Failed to get access token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "Token obtained successfully"
echo "Making request to accounts endpoint..."

# Make the accounts API request
echo "Making accounts request with token: ${AUTH_TOKEN:0:20}..."
ACCOUNTS_RESPONSE=$(curl --request GET \
  --url https://api.brale.xyz/accounts \
  --header "Authorization: Bearer $AUTH_TOKEN")

echo "Accounts response: $ACCOUNTS_RESPONSE"

# Extract account ID from JSON array
ACCOUNT_ID=$(echo $ACCOUNTS_RESPONSE | sed 's/.*"accounts":\["//' | sed 's/".*//')

if [ -z "$ACCOUNT_ID" ]; then
    echo "Error: Failed to get account ID"
    exit 1
fi

echo "Account ID: $ACCOUNT_ID"
echo "Getting addresses..."

# Get addresses for the account
curl --request GET \
  --url "https://api.brale.xyz/accounts/$ACCOUNT_ID/addresses" \
  --header "Authorization: Bearer $AUTH_TOKEN"