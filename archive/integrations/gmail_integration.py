"""Gmail Integration Stub"""
from typing import Any, List

class GmailIntegration:
    """Stub implementation for Gmail integration"""

    def __init__(self, credentials_json: str, token_path: str = '') -> Any:
        self.credentials_json = credentials_json
        self.token_path = token_path

    async def connect(self) -> Any:
        """Connect to Gmail"""
        pass

    async def send_email(self, to: List[str], subject: str, body: str) -> Any:
        """Send email"""
        return {"status": "sent"}

    async def search_emails(self, query: str, max_results: int = 10) -> Any:
        """Search emails"""
        return {"messages": []}
