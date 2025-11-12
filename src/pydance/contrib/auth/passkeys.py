"""
Passkeys (WebAuthn) authentication backend for Pydance.
"""

import secrets
import base64
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta



@dataclass
class PasskeyCredential:
    """WebAuthn credential data"""
    credential_id: str
    public_key: str
    sign_count: int
    user_id: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'credential_id': self.credential_id,
            'public_key': self.public_key,
            'sign_count': self.sign_count,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }


class PasskeyBackend:
    """Passkeys (WebAuthn) authentication backend"""

    def __init__(self, relying_party_id: str, relying_party_name: str,
                 origin: str, challenge_timeout: int = 300):
        self.relying_party_id = relying_party_id
        self.relying_party_name = relying_party_name
        self.origin = origin
        self.challenge_timeout = challenge_timeout

        # In-memory storage for demo - in production, use database
        self.credentials: Dict[str, PasskeyCredential] = {}
        self.challenges: Dict[str, Dict[str, Any]] = {}

    async def authenticate(self, request: Request, **kwargs) -> Optional[BaseUser]:
        """Authenticate using passkey"""
        # This would be called during the authentication flow
        # For now, return None as this is handled via separate endpoints
        return None

    def generate_registration_options(self, user_id: str, user_name: str,
                                    user_display_name: str) -> Dict[str, Any]:
        """Generate WebAuthn registration options"""
        challenge = secrets.token_bytes(32)
        challenge_b64 = base64.b64encode(challenge).decode('utf-8')

        # Store challenge
        self.challenges[user_id] = {
            'challenge': challenge_b64,
            'timestamp': datetime.utcnow(),
            'type': 'registration'
        }

        return {
            'challenge': challenge_b64,
            'rp': {
                'name': self.relying_party_name,
                'id': self.relying_party_id
            },
            'user': {
                'id': base64.b64encode(user_id.encode()).decode('utf-8'),
                'name': user_name,
                'displayName': user_display_name
            },
            'pubKeyCredParams': [
                {'alg': -7, 'type': 'public-key'},  # ES256
                {'alg': -257, 'type': 'public-key'}  # RS256
            ],
            'authenticatorSelection': {
                'authenticatorAttachment': 'cross-platform',
                'userVerification': 'preferred'
            },
            'timeout': 60000,
            'attestation': 'direct'
        }

    def generate_authentication_options(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate WebAuthn authentication options"""
        challenge = secrets.token_bytes(32)
        challenge_b64 = base64.b64encode(challenge).decode('utf-8')

        # Store challenge
        challenge_id = secrets.token_hex(16)
        self.challenges[challenge_id] = {
            'challenge': challenge_b64,
            'timestamp': datetime.utcnow(),
            'type': 'authentication',
            'user_id': user_id
        }

        options = {
            'challenge': challenge_b64,
            'timeout': 60000,
            'userVerification': 'preferred'
        }

        # If user_id provided, include allowCredentials
        if user_id and user_id in self.credentials:
            credential = self.credentials[user_id]
            options['allowCredentials'] = [{
                'type': 'public-key',
                'id': base64.b64encode(credential.credential_id.encode()).decode('utf-8')
            }]

        return options

    def verify_registration(self, user_id: str, credential_data: Dict[str, Any]) -> bool:
        """Verify WebAuthn registration response"""
        try:
            # Get stored challenge
            if user_id not in self.challenges:
                return False

            challenge_data = self.challenges[user_id]
            if challenge_data['type'] != 'registration':
                return False

            # Check challenge timeout
            if datetime.utcnow() - challenge_data['timestamp'] > timedelta(seconds=self.challenge_timeout):
                del self.challenges[user_id]
                return False

            # Verify challenge matches
            client_data_b64 = credential_data.get('response', {}).get('clientDataJSON')
            if not client_data_b64:
                return False

            client_data_json = base64.b64decode(client_data_b64)
            client_data = json.loads(client_data_json)

            if client_data.get('challenge') != challenge_data['challenge']:
                return False

            # Verify origin
            if client_data.get('origin') != self.origin:
                return False

            # Store credential
            credential_id = credential_data['id']
            public_key = credential_data['response']['publicKey']
            sign_count = credential_data['response']['signCount']

            self.credentials[user_id] = PasskeyCredential(
                credential_id=credential_id,
                public_key=public_key,
                sign_count=sign_count,
                user_id=user_id,
                created_at=datetime.utcnow()
            )

            # Clean up challenge
            del self.challenges[user_id]

            return True

        except Exception:
            return False

    def verify_authentication(self, credential_data: Dict[str, Any]) -> Optional[str]:
        """Verify WebAuthn authentication response"""
        try:
            # Extract credential ID
            credential_id_b64 = credential_data.get('id')
            if not credential_id_b64:
                return None

            credential_id = base64.b64decode(credential_id_b64).decode('utf-8')

            # Find credential
            user_id = None
            credential = None
            for uid, cred in self.credentials.items():
                if cred.credential_id == credential_id:
                    user_id = uid
                    credential = cred
                    break

            if not credential:
                return None

            # Get stored challenge (we need to find it by challenge value)
            challenge_b64 = None
            challenge_id = None

            client_data_b64 = credential_data.get('response', {}).get('clientDataJSON')
            if client_data_b64:
                client_data_json = base64.b64decode(client_data_b64)
                client_data = json.loads(client_data_json)
                challenge_b64 = client_data.get('challenge')

            if not challenge_b64:
                return None

            # Find challenge
            for cid, cdata in self.challenges.items():
                if cdata['challenge'] == challenge_b64 and cdata['type'] == 'authentication':
                    challenge_id = cid
                    break

            if not challenge_id:
                return None

            challenge_data = self.challenges[challenge_id]

            # Check challenge timeout
            if datetime.utcnow() - challenge_data['timestamp'] > timedelta(seconds=self.challenge_timeout):
                del self.challenges[challenge_id]
                return None

            # Verify origin
            if client_data.get('origin') != self.origin:
                return None

            # Verify signature (simplified - in production use proper WebAuthn verification)
            # This is a placeholder - real implementation needs cryptographic verification

            # Update sign count and last used
            credential.sign_count = max(credential.sign_count,
                                      credential_data.get('response', {}).get('signCount', 0))
            credential.last_used_at = datetime.utcnow()

            # Clean up challenge
            del self.challenges[challenge_id]

            return user_id

        except Exception:
            return None

    def get_user_credentials(self, user_id: str) -> List[PasskeyCredential]:
        """Get all credentials for a user"""
        return [cred for cred in self.credentials.values() if cred.user_id == user_id]

    def remove_credential(self, user_id: str, credential_id: str) -> bool:
        """Remove a credential for a user"""
        if user_id in self.credentials and self.credentials[user_id].credential_id == credential_id:
            del self.credentials[user_id]
            return True
        return False


class PasskeyMiddleware:
    """Middleware for handling passkey authentication"""

    def __init__(self, backend: PasskeyBackend):
        self.backend = backend

    async def __call__(self, request, call_next):
        # Add passkey helpers to request
        request.passkey = self.backend
        return await call_next(request)
