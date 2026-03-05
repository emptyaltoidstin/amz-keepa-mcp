"""
1688 API integration module
================
Supports image search to obtain purchase price

Plan options:
1. TMAPI (third party) - Simple and fast, requires apiToken
2. 1688 official API - Free, enterprise qualification application required
3. Crawler solution - Unstable, not recommended
"""

import os
import json
import hashlib
import time
import base64
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass
class CNSupplierOffer:
    """1688 supplier quotation"""
    offer_id: str
    title: str
    price: float  # RMB
    moq: int  # MOQ
    unit: str
    image_url: str
    supplier_name: str
    supplier_years: int
    is_verified: bool
    rating: float
    sales_count: int
    match_score: float  # Image matching degree 0-1
    product_url: str
    

class TMAPI1688Client:
    """
    TMAPI 1688 API client
    Official website: https://tmapi.top
    Features: Simple, fast, requires paid subscription
    """
    
    BASE_URL = "http://api.tmapi.top"  # TMAPI uses HTTP protocol
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        
    def search_by_image(self, image_url: str, page: int = 1, page_size: int = 20,
                       sort: str = "default", price_start: float = None,
                       price_end: float = None) -> Dict:
        """
        Search pictures by pictures
        
        Args:
            image_url: Image URL (must be an image from the Alibaba platform, or convert it first)
            page: Page number
            page_size: Quantity per page (Max 20)
            sort: sort by (default/sales/price_up/price_down)
            price_start: lowest price
            price_end: highest price
            
        Returns:
            API response result
        """
        endpoint = f"{self.BASE_URL}/platforms/1688/search/items_by_image"
        
        params = {
            "apiToken": self.api_token,
            "img_url": image_url,
            "page": page,
            "page_size": page_size,
            "sort": sort
        }
        
        if price_start is not None:
            params["price_start"] = str(price_start)
        if price_end is not None:
            params["price_end"] = str(price_end)
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    def get_product_detail(self, product_id: str) -> Dict:
        """
        Get product details
        
        Args:
            product_id: 1688 Product ID
            
        Returns:
            Product details
        """
        endpoint = f"{self.BASE_URL}/platforms/1688/product/detail"
        
        params = {
            "apiToken": self.api_token,
            "product_id": product_id
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}
    
    def parse_offers(self, response: Dict) -> List[CNSupplierOffer]:
        """Parse API response into list of quotes"""
        offers = []
        
        if response.get("status") != "success":
            return offers
        
        data = response.get("data", {})
        items = data.get("items", [])
        
        for item in items:
            try:
                offer = CNSupplierOffer(
                    offer_id=str(item.get("offer_id", "")),
                    title=item.get("title", ""),
                    price=float(item.get("price", 0)),
                    moq=int(item.get("min_order_quantity", 1)),
                    unit=item.get("unit", "pieces"),
                    image_url=item.get("image_url", ""),
                    supplier_name=item.get("supplier_name", ""),
                    supplier_years=int(item.get("supplier_years", 0)),
                    is_verified=bool(item.get("is_verified", False)),
                    rating=float(item.get("rating", 0)),
                    sales_count=int(item.get("sales_count", 0)),
                    match_score=float(item.get("match_score", 0)),
                    product_url=item.get("product_url", "")
                )
                offers.append(offer)
            except (ValueError, TypeError):
                continue
        
        return offers


class Alibaba1688Client:
    """
    1688 official open platform API client
    Official website: https://open.1688.com
    Features: Free, enterprise qualification application required
    """
    
    GATEWAY_URL = "https://gw.open.1688.com/openapi"
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        
    def _generate_sign(self, params: Dict) -> str:
        """Generate API signature"""
        # Sort by parameter name
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # Concatenate strings
        sign_str = ""
        for key, value in sorted_params:
            sign_str += f"{key}{value}"
        
        # Add secret
        sign_str = self.app_secret + sign_str + self.app_secret
        
        # MD5 encryption
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    def search_by_image(self, image_url: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        Search pictures by pictures (alibaba.product.image.similar.offer.search)
        
        Note: You need to apply for API permission first
        """
        api_namespace = "com.alibaba.product"
        api_name = "alibaba.product.image.similar.offer.search"
        api_version = "1"
        
        params = {
            "appKey": self.app_key,
            "timestamp": str(int(time.time() * 1000)),
            "apiName": api_name,
            "apiNamespace": api_namespace,
            "apiVersion": api_version,
            "imageUrl": image_url,
            "page": str(page),
            "pageSize": str(page_size)
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            url = f"{self.GATEWAY_URL}/{api_namespace}/{api_name}/{api_version}"
            response = requests.post(url, data=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}


class CNProcurementFinder:
    """
    Purchase price finder
    Integrate multiple methods to obtain 1688 purchase price
    """
    
    def __init__(self, 
                 tmapi_token: Optional[str] = None,
                 alibaba_app_key: Optional[str] = None,
                 alibaba_app_secret: Optional[str] = None):
        """
        initialization
        
        Args:
            tmapi_token: TMAPI’s apiToken (recommended, the simplest)
            alibaba_app_key: 1688 Open Platform App Key
            alibaba_app_secret: 1688 Open Platform App Secret
        """
        self.tmapi_client = None
        self.alibaba_client = None
        
        if tmapi_token:
            self.tmapi_client = TMAPI1688Client(tmapi_token)
        
        if alibaba_app_key and alibaba_app_secret:
            self.alibaba_client = Alibaba1688Client(alibaba_app_key, alibaba_app_secret)
    
    @classmethod
    def from_env(cls) -> "CNProcurementFinder":
        """Create instance from environment variables"""
        return cls(
            tmapi_token=os.getenv("TMAPI_TOKEN"),
            alibaba_app_key=os.getenv("ALIBABA_APP_KEY"),
            alibaba_app_secret=os.getenv("ALIBABA_APP_SECRET")
        )
    
    def search_best_price(self, image_url: str, target_moq: int = 1,
                          max_results: int = 10) -> Optional[CNSupplierOffer]:
        """
        Search for the best price
        
        Args:
            image_url: Product image URL
            target_moq: Target minimum order quantity
            max_results: Maximum number of results
            
        Returns:
            Best offer, or None
        """
        if not self.tmapi_client:
            raise ValueError("TMAPI is required_TOKEN or use other methods")
        
        # Call TMAPI search
        response = self.tmapi_client.search_by_image(
            image_url=image_url,
            page_size=min(max_results, 20),
            sort="price_up"  # Sort by price ascending
        )
        
        if response.get("status") != "success":
            return None
        
        offers = self.tmapi_client.parse_offers(response)
        
        if not offers:
            return None
        
        # Filter quotes that meet the minimum order quantity and sort by price
        suitable_offers = [
            o for o in offers 
            if o.moq <= target_moq * 2  # Allow MOQ to be slightly higher
        ]
        
        if not suitable_offers:
            suitable_offers = offers
        
        # Comprehensive score ranking (price weight 0.6, matching weight 0.2, sales weight 0.2)
        def score_offer(o: CNSupplierOffer) -> float:
            price_score = 1 / (o.price + 1)  # The lower the price, the higher the score
            match_score = o.match_score
            sales_score = min(o.sales_count / 1000, 1)  # Sales volume normalized
            
            # Bonus points for certified merchants
            verified_bonus = 0.2 if o.is_verified else 0
            
            return price_score * 0.6 + match_score * 0.2 + sales_score * 0.1 + verified_bonus
        
        suitable_offers.sort(key=score_offer, reverse=True)
        
        return suitable_offers[0] if suitable_offers else None
    
    def search_multiple_prices(self, image_url: str, 
                               count: int = 5) -> List[CNSupplierOffer]:
        """
        Search multiple quotes to choose from
        
        Args:
            image_url: Product image URL
            count: Return quantity
            
        Returns:
            Quotation list
        """
        if not self.tmapi_client:
            raise ValueError("TMAPI is required_TOKEN")
        
        response = self.tmapi_client.search_by_image(
            image_url=image_url,
            page_size=min(count, 20)
        )
        
        return self.tmapi_client.parse_offers(response)


def get_product_main_image(keepa_product: Dict) -> Optional[str]:
    """
    Get main image URL from Keepa product data
    
    Args:
        keepa_product: Product data returned by Keepa API
        
    Returns:
        Image URL or None
    """
    # Try to get the picture
    images = keepa_product.get("imagesCSV", "")
    if images:
        # Keepa’s image format is comma-separated image IDs
        image_ids = images.split(",")
        if image_ids:
            # Construct image URL
            # Note: Keepa’s images may require special processing to be used in 1688 searches
            image_id = image_ids[0]
            return f"https://images-na.ssl-images-amazon.com/images/I/{image_id}"
    
    # Try to get from data
    data = keepa_product.get("data", {})
    if data:
        image_list = data.get("images", [])
        if image_list:
            return image_list[0]
    
    return None


def find_procurement_price(keepa_product: Dict, 
                           tmapi_token: Optional[str] = None) -> Dict:
    """
    Find purchase prices for Keepa products
    
    Args:
        keepa_product: Keepa product data
        tmapi_token: TMAPI token
        
    Returns:
        Dictionary containing purchasing information
    """
    result = {
        "found": False,
        "price_rmb": 0,
        "moq": 1,
        "supplier": "",
        "source_url": "",
        "match_score": 0,
        "offers": []
    }
    
    # Get product pictures
    image_url = get_product_main_image(keepa_product)
    
    if not image_url:
        result["error"] = "Unable to get product image"
        return result
    
    # Create finder
    finder = CNProcurementFinder(tmapi_token=tmapi_token)
    
    try:
        # Search multiple quotes
        offers = finder.search_multiple_prices(image_url, count=5)
        
        if offers:
            best_offer = offers[0]
            result["found"] = True
            result["price_rmb"] = best_offer.price
            result["moq"] = best_offer.moq
            result["supplier"] = best_offer.supplier_name
            result["source_url"] = best_offer.product_url
            result["match_score"] = best_offer.match_score
            result["offers"] = [
                {
                    "price": o.price,
                    "moq": o.moq,
                    "supplier": o.supplier_name,
                    "verified": o.is_verified,
                    "url": o.product_url
                }
                for o in offers[:3]
            ]
    except Exception as e:
        result["error"] = str(e)
    
    return result


# Convenience function
def quick_find_price(asin: str, keepa_api_key: str, tmapi_token: str) -> Dict:
    """
    Quickly find the purchase price of an ASIN
    
    This function integrates Keepa and 1688 API
    """
    import keepa
    
    # Get Keepa data
    api = keepa.Keepa(keepa_api_key)
    products = api.product_finder({
        'asin': [asin],
        'perPage': 1
    })
    
    if not products:
        return {"error": "Keepa product not found"}
    
    # Find purchase price
    return find_procurement_price(products[0], tmapi_token)


if __name__ == "__main__":
    # test code
    print("1688 API module loaded")
    print("\nHow to use:")
    print("1. Set the environment variable TMAPI_TOKEN=your_token")
    print("2. Use CNProcurementFinder.from_env()")
    print("3. Call search_best_price(image_url)")
    print("\nGet TMAPI Token:")
    print("  access https://tmapi.top register and get")
