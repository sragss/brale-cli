"""Authentication module for Brale CLI."""

import base64
import time
from typing import Optional, Dict, Any
import requests
from .config import config

class BraleAuth:
    """Authentication manager for Brale API."""
    
    def __init__(self):
        self.auth_base_url = config.get_auth_base_url()
        self.api_base_url = config.get_api_base_url()
    
    def authenticate(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> bool:
        """Authenticate with Brale API using client credentials."""
        # Get credentials from parameters or config/env
        if not client_id or not client_secret:
            client_id, client_secret = config.get_client_credentials()
        
        if not client_id or not client_secret:
            raise ValueError("Client ID and secret are required. Set them via environment variables or config.")
        
        # Create basic auth header
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        # Make token request
        try:
            response = requests.post(
                f"{self.auth_base_url}/oauth2/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Authentication failed: {response.text}")
            
            token_data = response.json()
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            expires_at = int(time.time()) + expires_in
            
            # Store token and credentials
            config.set_access_token(access_token, expires_at)
            config.set_credential('client_id', client_id)
            config.set_credential('client_secret', client_secret)
            
            return True
            
        except requests.RequestException as e:
            raise RuntimeError(f"Network error during authentication: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid access token."""
        token = config.get_access_token()
        if not token:
            return False
        
        # Check if token is expired
        expires_at = config.get_credential('token_expires_at')
        if expires_at and int(time.time()) >= expires_at:
            config.clear_access_token()
            return False
        
        return True
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if necessary."""
        if not self.is_authenticated():
            # Try to refresh token automatically
            try:
                client_id, client_secret = config.get_client_credentials()
                if client_id and client_secret:
                    self.authenticate(client_id, client_secret)
                else:
                    return None
            except Exception:
                return None
        
        return config.get_access_token()
    
    def logout(self):
        """Clear stored authentication data."""
        config.clear_access_token()
        # Note: We keep client credentials for easy re-authentication
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        token = self.get_access_token()
        if not token:
            raise RuntimeError("Not authenticated. Run 'brale auth login' first.")
        
        return {"Authorization": f"Bearer {token}"}

class BraleAPIClient:
    """API client with automatic authentication."""
    
    def __init__(self):
        self.auth = BraleAuth()
        self.base_url = config.get_api_base_url()
        self.session = requests.Session()
    
    def _ensure_authenticated(self):
        """Ensure we have valid authentication."""
        if not self.auth.is_authenticated():
            raise RuntimeError("Not authenticated. Run 'brale auth login' first.")
        
        # Update session headers
        self.session.headers.update(self.auth.get_auth_headers())
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated API request."""
        self._ensure_authenticated()
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        # Handle token expiration
        if response.status_code == 401:
            # Try to refresh token and retry once
            try:
                client_id, client_secret = config.get_client_credentials()
                if client_id and client_secret:
                    self.auth.authenticate(client_id, client_secret)
                    self.session.headers.update(self.auth.get_auth_headers())
                    response = self.session.request(method, url, **kwargs)
            except Exception:
                pass  # If refresh fails, return original 401 response
        
        return response
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make GET request."""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make POST request."""
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make PUT request."""
        return self.request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make DELETE request."""
        return self.request('DELETE', endpoint, **kwargs)

# Global instances
auth = BraleAuth()
api_client = BraleAPIClient()