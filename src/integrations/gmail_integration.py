"""Gmail Integration Stub"""
from typing import List

class GmailIntegration:
    """Stub implementation for Gmail integration"""

    def __init__(self, credentials_json: str, token_path: str = ''):
        self.credentials_json = credentials_json
        self.token_path = token_path

    async def connect(self):
        """Connect to Gmail"""
        pass

    async def send_email(self, to: List[str], subject: str, body: str):
        """Send email"""
        return {"status": "sent"}

    async def search_emails(self, query: str, max_results: int = 10):
        """Search emails"""
        return {"messages": []}
