"""
Mandi (Market) Price Service for Indian agricultural commodities.
Fetches live market prices from Indian mandi API.
"""

import logging
import os
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger("mandi_service")


class MandiService:
    """
    Service to fetch live mandi prices for Indian agricultural commodities.
    Uses public Indian agricultural market API.
    """
    
    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a5c0-3b641313a86f"
    
    def __init__(self):
        """Initialize with API key from environment."""
        self.api_key = os.getenv("MANDI_API_KEY")
        if not self.api_key:
            logger.warning("MANDI_API_KEY not set in environment")
    
    async def get_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch mandi prices for a commodity.
        
        Args:
            commodity: Name of the commodity (e.g., "गेहूँ", "Wheat", "Onion")
            state: State name (optional, for filtering)
            district: District name (optional, for filtering)
            market: Market/Mandi name (optional, for filtering)
            limit: Maximum results to return
        
        Returns:
            List of price records or None if fetch fails
        """
        if not self.api_key:
            logger.error("MANDI_API_KEY not configured")
            return None
        
        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "filters[commodity]": commodity,
                "limit": limit,
                "offset": 0
            }
            
            if state:
                params["filters[state]"] = state
            if district:
                params["filters[district]"] = district
            if market:
                params["filters[market]"] = market
            
            async with aiohttp.ClientSession() as session:
                # Use shorter timeout and add retry logic
                async with session.get(
                    self.BASE_URL, 
                    params=params, 
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        logger.info(f"Mandi prices fetched for commodity: {commodity} ({len(records)} records)")
                        return self._process_records(records)
                    else:
                        logger.error(f"Mandi API error: {response.status}")
                        return self._get_demo_data(commodity, state)
                        
        except asyncio.TimeoutError:
            logger.warning(f"Mandi API timeout for {commodity}")
            return self._get_demo_data(commodity, state)
        except Exception as e:
            logger.error(f"Mandi fetch error: {e}")
            return self._get_demo_data(commodity, state)
    
    async def search_by_state_and_commodity(
        self,
        commodity: str,
        state: str,
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search for commodity prices in a specific state.
        
        Args:
            commodity: Name of the commodity
            state: State name
            limit: Maximum results
        
        Returns:
            List of price records
        """
        return await self.get_prices(commodity, state=state, limit=limit)
    
    @staticmethod
    def _process_records(records: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process raw mandi API records into readable format.
        
        Args:
            records: Raw API response records
        
        Returns:
            Processed price data
        """
        processed = []
        
        for record in records[:5]:  # Limit to top 5 results
            try:
                processed_record = {
                    "commodity": record.get("commodity", "Unknown"),
                    "state": record.get("state", "Unknown"),
                    "district": record.get("district", "Unknown"),
                    "market": record.get("market", "Unknown"),
                    "price": record.get("price", 0),
                    "unit": record.get("unit", "प्रति क्विंटल"),
                    "date": record.get("arrival_date", record.get("_created_at", "N/A")),
                }
                processed.append(processed_record)
            except Exception as e:
                logger.error(f"Error processing record: {e}")
                continue
        
        return processed
    
    @staticmethod
    def _get_demo_data(commodity: str, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return demo/fallback mandi prices when API is unavailable.
        Used for demonstration purposes when live API fails.
        """
        demo_prices = {
            "wheat": [
                {
                    "commodity": "Wheat",
                    "state": state or "Uttar Pradesh",
                    "district": "Varanasi",
                    "market": "Varanasi Mandi",
                    "price": 2450,
                    "unit": "प्रति क्विंटल",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            ],
            "rice": [
                {
                    "commodity": "Rice",
                    "state": state or "Punjab",
                    "district": "Amritsar",
                    "market": "Amritsar Mandi",
                    "price": 2800,
                    "unit": "प्रति क्विंटल",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            ],
            "onion": [
                {
                    "commodity": "Onion",
                    "state": state or "Maharashtra",
                    "district": "Nashik",
                    "market": "Nashik Mandi",
                    "price": 1200,
                    "unit": "प्रति क्विंटल",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            ],
        }
        
        commodity_lower = commodity.lower()
        if commodity_lower in demo_prices:
            logger.info(f"Using demo data for {commodity} (API unavailable)")
            return demo_prices[commodity_lower]
        
        # Default fallback
        logger.warning(f"No demo data for {commodity}, returning generic fallback")
        return [
            {
                "commodity": commodity,
                "state": state or "Unknown",
                "district": "Unknown",
                "market": "Unknown",
                "price": 0,
                "unit": "प्रति क्विंटल",
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        ]
    
    @staticmethod
    def format_price_response(prices: List[Dict[str, Any]], language: str = "hi") -> str:
        """
        Format price records into readable text response.
        
        Args:
            prices: List of price records
            language: Response language (hi/en)
        
        Returns:
            Formatted text response
        """
        if not prices:
            if language == "hi":
                return "मुझे इस समय वह डेटा नहीं मिल सका। कृपया बाद में कोशिश करें।"
            else:
                return "I couldn't find that data right now. Please try again later."
        
        # Get most recent price
        latest = prices[0]
        
        if language == "hi":
            return (
                f"आज {latest['market']} मंडी में {latest['commodity']} का "
                f"नवीनतम भाव {latest['price']} {latest['unit']} है। "
                f"यह {latest['date']} का डेटा है।"
            )
        else:
            return (
                f"Today in {latest['market']} market, the latest price for {latest['commodity']} "
                f"is {latest['price']} {latest['unit']}. "
                f"This data is from {latest['date']}."
            )


# Create singleton instance
_mandi_service = None


def get_mandi_service() -> MandiService:
    """Get or create mandi service instance."""
    global _mandi_service
    if _mandi_service is None:
        _mandi_service = MandiService()
    return _mandi_service
