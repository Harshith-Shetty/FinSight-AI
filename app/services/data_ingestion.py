"""
SEC EDGAR data fetcher.
Fetches 10-K filings from SEC EDGAR API.
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re

from app.core.exceptions import SECAPIError


class SECDataFetcher:
    """
    Fetches and parses SEC EDGAR filings.
    """
    
    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        "User-Agent": "FinSight AI harshithdshetty@gmail.com"  # SEC requires user agent
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(headers=self.HEADERS, timeout=30.0)
    
    async def fetch_10k(self, ticker: str, year: int) -> str:
        """
        Fetch 10-K filing for a given ticker and year.
        
        Args:
            ticker: Stock ticker symbol
            year: Filing year
            
        Returns:
            Cleaned text content of the 10-K filing
            
        Raises:
            SECAPIError: If filing cannot be fetched
        """
        try:
            # For MVP, we'll use a simplified approach
            # In production, you'd search for the exact filing URL
            
            # This is a placeholder - real implementation would:
            # 1. Search SEC EDGAR for the company CIK
            # 2. Find the specific 10-K filing for the year
            # 3. Download and parse the filing
            
            # For now, return mock data for testing
            return self._get_mock_filing(ticker, year)
            
        except Exception as e:
            raise SECAPIError(f"Failed to fetch 10-K for {ticker} ({year}): {str(e)}")
    
    def _get_mock_filing(self, ticker: str, year: int) -> str:
        """
        Return mock filing data for testing.
        In production, this would be replaced with actual SEC API calls.
        """
        return f"""
        UNITED STATES SECURITIES AND EXCHANGE COMMISSION
        FORM 10-K
        
        {ticker} Inc. - Annual Report for Fiscal Year {year}
        
        ITEM 1A. RISK FACTORS
        
        Our business faces various risks including:
        
        Supply Chain Risks: We depend on a limited number of suppliers for critical components.
        Any disruption in the supply chain could materially impact our operations and financial results.
        
        Market Competition: The technology sector is highly competitive. We face competition from 
        established companies and new entrants, which could reduce our market share and pricing power.
        
        Regulatory Risks: Changes in government regulations, particularly in data privacy and 
        environmental standards, could increase our compliance costs and limit our business operations.
        
        Cybersecurity Risks: We store sensitive customer and business data. Any security breach 
        could result in significant financial losses and reputational damage.
        
        Economic Conditions: Global economic downturns could reduce customer spending and 
        negatively impact our revenue and profitability.
        
        ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
        
        Revenue for fiscal year {year} increased by 15% compared to the prior year, driven by 
        strong product sales and expansion into new markets. Operating expenses increased by 10% 
        due to investments in research and development.
        
        Our cash position remains strong with $50 billion in cash and marketable securities.
        We continue to invest in innovation while maintaining financial discipline.
        """
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
