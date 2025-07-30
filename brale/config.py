"""Configuration management for Brale CLI."""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class BraleConfig:
    """Configuration manager for Brale CLI."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.brale'
        self.config_file = self.config_dir / 'config.yaml'
        self.credentials_file = self.config_dir / 'credentials.json'
        
        # Load environment variables
        load_dotenv()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self._config = self._load_config()
        self._credentials = self._load_credentials()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {
                'default_account': None,
                'default_output': 'table',
                'api_base_url': 'https://api.brale.xyz',
                'auth_base_url': 'https://auth.brale.xyz'
            }
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from file."""
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save config: {e}")
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(self._credentials, f, indent=2)
            # Set restrictive permissions on credentials file
            os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            raise RuntimeError(f"Failed to save credentials: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value
        self._save_config()
    
    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get credential value."""
        return self._credentials.get(key, default)
    
    def set_credential(self, key: str, value: Any):
        """Set credential value."""
        self._credentials[key] = value
        self._save_credentials()
    
    def get_client_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Get client ID and secret from environment or config."""
        client_id = os.getenv('BRALE_CLIENT_ID') or self.get_credential('client_id')
        client_secret = os.getenv('BRALE_SECRET') or self.get_credential('client_secret')
        return client_id, client_secret
    
    def get_access_token(self) -> Optional[str]:
        """Get stored access token."""
        return self.get_credential('access_token')
    
    def set_access_token(self, token: str, expires_at: Optional[int] = None):
        """Store access token."""
        self.set_credential('access_token', token)
        if expires_at:
            self.set_credential('token_expires_at', expires_at)
    
    def clear_access_token(self):
        """Clear stored access token."""
        self._credentials.pop('access_token', None)
        self._credentials.pop('token_expires_at', None)
        self._save_credentials()
    
    def get_default_account(self) -> Optional[str]:
        """Get default account ID."""
        return self.get('default_account')
    
    def set_default_account(self, account_id: str):
        """Set default account ID."""
        self.set('default_account', account_id)
    
    def get_api_base_url(self) -> str:
        """Get API base URL."""
        return self.get('api_base_url', 'https://api.brale.xyz')
    
    def get_auth_base_url(self) -> str:
        """Get auth base URL."""
        return self.get('auth_base_url', 'https://auth.brale.xyz')
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (excluding sensitive data)."""
        config_copy = self._config.copy()
        # Add non-sensitive credential info
        if self.get_access_token():
            config_copy['authenticated'] = True
        else:
            config_copy['authenticated'] = False
        return config_copy

# Global config instance
config = BraleConfig()