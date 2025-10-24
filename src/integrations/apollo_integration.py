"""Apollo Integration Stub"""
from typing import List

class ApolloIntegration:
    """Stub implementation for Apollo integration"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def connect(self):
        """Connect to Apollo"""
        pass

    async def search_people(self, keywords: List[str] = None, titles: List[str] = None,
                          company_names: List[str] = None):
        """Search for people"""
        return {"people": []}

    async def search_companies(self, keywords: List[str] = None, industries: List[str] = None):
        """Search for companies"""
        return {"companies": []}
