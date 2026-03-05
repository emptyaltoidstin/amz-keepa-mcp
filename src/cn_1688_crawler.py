"""
1688 Image search crawler module
=====================
Image search based on 1688 internal API
Features:
- No browser required, call API directly
- Support URL/File/base64 image input
- Get complete information on prices, MOQ, suppliers and more

Reference: https://github.com/Zhui-CN/1688_image_search_crawler
"""

import re
import os
import time
import json
import base64
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
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
    company_name: str
    province: str
    city: str
    shop_url: str
    is_verified: bool
    credit_level: str
    years: int  # Credit Pass Period
    repurchase_rate: str  # Repurchase rate
    product_url: str
    quantity_prices: List[Dict]  # Ladder price
    scores: Dict  # Store rating
    position_labels: List[str]  # tags (such as"Source factory"）


class CN1688Crawler:
    """
    1688 Image search crawler
    
    Implemented based on 1688 H5 API
    """
    
    # API configuration
    JSV = "2.7.2"
    API_VERSION = "1.0"
    API_KEY = "12574478"
    APP_NAME = "searchImageUpload"
    APP_KEY = "pvvljh1grxcmaay2vgpe9nb68gg9ueg2"
    
    UPLOAD_API_PATH = "mtop.1688.imageService.putImage"
    TOKEN_API_PATH = "mtop.ovs.traffic.landing.seotaglist.queryHotSearchWord"
    
    API_HOST = "https://h5api.m.1688.com"
    
    # Data extraction regularity
    DATA_REG = re.compile(r"window\.data\.offerresultData\s?=\s?successDataCheck\((.*?)\);", re.S | re.I)
    
    def __init__(self, timeout: int = 30, use_proxy: bool = False):
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        
        # Disable SSL verification (Troubleshoot SSL issues for some environments)
        self.session.verify = False
        
        # Ignore SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.token = ""
        self._img_id = None
        self._req_id = None
        self._session_id = None
    
    def _set_cookie_cna(self) -> str:
        """Set cna cookie"""
        timestamp = str(int(time.time() * 1000))
        url = f"https://log.mmstat.com/eg.js?t={timestamp}"
        headers = {"referer": "https://www.1688.com/"}
        
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        cna = self.session.cookies.get("cna")
        
        if not cna:
            raise Exception("Unable to get cna cookie")
        
        return cna
    
    def _set_token(self) -> str:
        """Get token"""
        url = f"{self.API_HOST}/h5/{self.TOKEN_API_PATH.lower()}/{self.API_VERSION}/"
        headers = {
            "origin": "https://www.1688.com",
            "referer": "https://www.1688.com/"
        }
        
        params = {
            "jsv": self.JSV,
            "appKey": self.API_KEY,
            "t": str(int(time.time() * 1000)),
            "api": self.TOKEN_API_PATH,
            "v": self.API_VERSION,
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp1",
            "preventFallback": True,
            "data": {},
        }
        
        resp = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
        
        # Get token from cookie
        m_h5_tk = self.session.cookies.get("_m_h5_tk")
        if not m_h5_tk:
            raise Exception("Unable to obtain_m_h5_tk cookie")
        
        self.token = m_h5_tk.split("_")[0]
        return self.token
    
    def _upload_image(self, b64_image: str) -> str:
        """
        Upload pictures to 1688
        
        Args:
            b64_image: base64 encoded image
            
        Returns:
            img_id: Image ID
        """
        url = f"{self.API_HOST}/h5/{self.UPLOAD_API_PATH.lower()}/{self.API_VERSION}/"
        headers = {
            "origin": "https://www.1688.com",
            "referer": "https://www.1688.com/"
        }
        
        timestamp = str(int(time.time() * 1000))
        upload_data = json.dumps({
            "imageBase64": b64_image,
            "appName": self.APP_NAME,
            "appKey": self.APP_KEY
        }, separators=(",", ":"))
        
        # Generate signature
        sign_str = f"{self.token}&{timestamp}&{self.API_KEY}&{upload_data}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            "jsv": self.JSV,
            "appKey": self.API_KEY,
            "t": timestamp,
            "sign": sign,
            "api": self.UPLOAD_API_PATH,
            "ignoreLogin": "true",
            "prefix": "h5api",
            "v": self.API_VERSION,
            "ecode": "0",
            "dataType": "jsonp",
            "jsonpIncPrefix": "search1688",
            "timeout": "20000",
            "type": "originaljson"
        }
        
        data = {"data": upload_data}
        resp = self.session.post(url, headers=headers, params=params, 
                                  data=data, timeout=self.timeout)
        
        result = resp.json()
        
        if not result.get("data") or not result["data"].get("imageId"):
            raise Exception(f"Failed to upload image: {result}")
        
        self._img_id = result["data"]["imageId"]
        self._req_id = result["data"]["requestId"]
        self._session_id = result["data"]["sessionId"]
        
        return self._img_id
    
    def _search_offers(self, page: int = 1, use_api: bool = True) -> List[Dict]:
        """
        Search product list
        
        Args:
            page: Page number
            use_api: Whether to use API mode (False uses web mode)
            
        Returns:
            Product list
        """
        if use_api:
            return self._search_api(page)
        else:
            return self._search_web()
    
    def _search_api(self, page: int = 1) -> List[Dict]:
        """API pattern search"""
        url = "https://search.1688.com/service/imageSearchOfferResultViewService"
        headers = {
            "origin": "https://s.1688.com",
            "referer": "https://s.1688.com/"
        }
        
        params = {
            "tab": "imageSearch",
            "imageAddress": "",
            "imageId": self._img_id,
            "imageIdList": self._img_id,
            "beginPage": page,
            "pageSize": "40",
            "pageName": "image",
            "sessionId": self._session_id
        }
        
        resp = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
        result = resp.json()
        
        data = result.get("data", {}).get("data", {})
        offer_list = data.get("offerList", [])
        
        return offer_list
    
    def _search_web(self) -> List[Dict]:
        """Web mode search (backup)"""
        url = "https://s.1688.com/youyuan/index.htm"
        headers = {"referer": "https://www.1688.com/"}
        
        params = {
            "tab": "imageSearch",
            "imageAddress": "",
            "spm": "a260k.dacugeneral.searchbox.input",
            "imageId": self._img_id,
            "imageIdList": self._img_id,
        }
        
        resp = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
        html = resp.text
        
        # Extract JSON data
        match = self.DATA_REG.search(html)
        if not match:
            return []
        
        json_data = json.loads(match.group(1))
        offer_list = json_data.get("data", {}).get("offerList", [])
        
        return offer_list
    
    def _parse_offers(self, offer_list: List[Dict]) -> List[CNSupplierOffer]:
        """Parse product data"""
        offers = []
        
        for offer in offer_list:
            try:
                # Extract company information
                company = offer.get("company") or {}
                # Extract product information
                information = offer.get("information") or {}
                # Extract transaction service information
                trade_service = offer.get("tradeService") or {}
                # Extract transaction quantity information
                trade_quantity = offer.get("tradeQuantity") or {}
                # Extract price information
                offer_price = (offer.get("tradePrice") or {}).get("offerPrice") or {}
                # Extract tags
                position_labels = (offer.get("commonPositionLabels") or {}).get("offerMiddle") or []
                
                # parse price
                price = 0.0
                price_info = offer_price.get("priceInfo") or {}
                if price_info.get("price"):
                    price = float(price_info["price"])
                else:
                    # Parse from originalValue
                    original = offer_price.get("originalValue") or {}
                    integer = original.get("integer", 0)
                    decimals = original.get("decimals", 0)
                    price = float(f"{integer}.{decimals}")
                
                # Analyze tiered prices
                quantity_prices = []
                for q in offer_price.get("quantityPrices", []):
                    q_price_info = q.get("value") or {}
                    q_integer = q_price_info.get("integer", 0)
                    q_decimals = q_price_info.get("decimals", 0)
                    quantity_prices.append({
                        "quantity": q.get("quantity"),
                        "price": float(f"{q_integer}.{q_decimals}")
                    })
                
                # Analyze repurchase rate
                repurchase = information.get("rePurchaseRate", "")
                if repurchase and "%" not in str(repurchase):
                    repurchase = f"{round(float(repurchase) * 100, 2)}%"
                
                # Build results
                offer_id = str(offer.get("id", ""))
                supplier_offer = CNSupplierOffer(
                    offer_id=offer_id,
                    title=information.get("subject", ""),
                    price=price,
                    moq=trade_quantity.get("quantityBegin", 1),
                    unit=trade_quantity.get("unit", "pieces"),
                    image_url=(offer.get("image") or {}).get("imgUrl", ""),
                    company_name=company.get("name", ""),
                    province=company.get("province", ""),
                    city=company.get("city", ""),
                    shop_url=company.get("url", ""),
                    is_verified=bool(company.get("tpMember")),
                    credit_level=company.get("creditLevelText", ""),
                    years=trade_service.get("tpYear", 0),
                    repurchase_rate=repurchase,
                    product_url=f"https://detail.1688.com/offer/{offer_id}.html",
                    quantity_prices=quantity_prices,
                    scores={
                        "composite": self._parse_score(trade_service.get("compositeNewScore")),
                        "consultation": self._parse_score(trade_service.get("consultationScore")),
                        "goods": self._parse_score(trade_service.get("goodsScore")),
                        "logistics": self._parse_score(trade_service.get("logisticsScore")),
                    },
                    position_labels=[l.get("text", "") for l in position_labels if l.get("text")]
                )
                
                offers.append(supplier_offer)
                
            except Exception as e:
                continue
        
        return offers
    
    def _parse_score(self, score) -> float:
        """Analyze scoring"""
        try:
            return round(float(score or 0), 1)
        except:
            return 0.0
    
    def search_by_image_url(self, image_url: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        Search by image URL
        
        Args:
            image_url: Image URL
            max_results: Maximum number of results
            
        Returns:
            Supplier quotation list
        """
        # Download pictures
        resp = requests.get(image_url, timeout=self.timeout)
        resp.raise_for_status()
        
        # Convert to base64
        b64_image = base64.b64encode(resp.content).decode()
        
        return self.search_by_base64(b64_image, max_results)
    
    def search_by_file(self, image_path: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        Search by local image files
        
        Args:
            image_path: Image file path
            max_results: Maximum number of results
            
        Returns:
            Supplier quotation list
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file does not exist: {image_path}")
        
        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode()
        
        return self.search_by_base64(b64_image, max_results)
    
    def search_by_base64(self, b64_image: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        Search by base64 image
        
        Args:
            b64_image: base64 encoded image
            max_results: Maximum number of results
            
        Returns:
            Supplier quotation list
        """
        # Initialize session
        self._set_cookie_cna()
        self._set_token()
        
        # Upload pictures
        self._upload_image(b64_image)
        
        # Search for products
        all_offers = []
        page = 1
        
        while len(all_offers) < max_results:
            offer_list = self._search_offers(page=page, use_api=True)
            
            if not offer_list:
                break
            
            offers = self._parse_offers(offer_list)
            all_offers.extend(offers)
            
            page += 1
            
            # Simple anti-climbing
            time.sleep(0.5)
        
        return all_offers[:max_results]
    
    def find_best_price(self, image_url: str, target_moq: int = 100) -> Optional[CNSupplierOffer]:
        """
        Find the best price
        
        Args:
            image_url: Image URL
            target_moq: Target minimum order quantity
            
        Returns:
            best offer
        """
        offers = self.search_by_image_url(image_url, max_results=20)
        
        if not offers:
            return None
        
        # Screen those that meet the MOQ
        suitable = [o for o in offers if o.moq <= target_moq * 2]
        if not suitable:
            suitable = offers
        
        # Comprehensive rating ranking
        def score(o: CNSupplierOffer) -> float:
            price_score = 1 / (o.price + 1)
            verified_bonus = 0.3 if o.is_verified else 0
            year_score = min(o.years / 10, 0.2)
            return price_score * 0.6 + verified_bonus + year_score
        
        suitable.sort(key=score, reverse=True)
        
        return suitable[0] if suitable else None


def extract_image_url_from_keepa(product: Dict) -> Optional[str]:
    """
    Extract main image URL from Keepa product data
    
    Support multiple formats:
    - imagesCSV returned by Keepa API (Comma separated image IDs)
    - Image field for Keepa CSV export (Semicolon separated full URLs)
    - Image field in 163 indicators
    
    Args:
        product: Keepa Product Data Dictionary
        
    Returns:
        Image URL or None
    """
    # Method 1: Get from 163 indicator Image field (Semicolon separated list of URLs)
    image_field = product.get("Image", "")
    if image_field and "https://" in image_field:
        urls = image_field.split(";")
        if urls and urls[0].startswith("http"):
            return urls[0].strip()
    
    # Method 2: Get from imagesCSV (Comma separated image IDs)
    images = product.get("imagesCSV", "")
    if images:
        image_ids = images.split(",")
        if image_ids and image_ids[0]:
            image_id = image_ids[0].strip()
            if image_id:
                return f"https://m.media-amazon.com/images/I/{image_id}.jpg"
    
    # Method 3: Get from data.images
    data = product.get("data", {})
    image_list = data.get("images", [])
    if image_list:
        return image_list[0]
    
    # Method 4: from metrics_163 dictionary acquisition
    metrics = product.get('metrics_163', {})
    if metrics:
        image_value = metrics.get('Image', '')
        if image_value:
            if 'https://' in image_value:
                urls = image_value.split(';')
                if urls:
                    return urls[0].strip()
            else:
                # Comma separated image IDs
                ids = image_value.split(',')
                if ids and ids[0]:
                    return f"https://m.media-amazon.com/images/I/{ids[0].strip()}.jpg"
    
    return None


# Convenience function
def find_1688_price(image_url: str, target_moq: int = 100) -> Optional[Dict]:
    """
    Quickly find 1688 purchase price
    
    Args:
        image_url: Product image URL
        target_moq: Target minimum order quantity
        
    Returns:
        Price Information Dictionary
    """
    crawler = CN1688Crawler()
    
    try:
        offer = crawler.find_best_price(image_url, target_moq)
        
        if offer:
            return {
                "found": True,
                "price_rmb": offer.price,
                "moq": offer.moq,
                "unit": offer.unit,
                "supplier": offer.company_name,
                "location": f"{offer.province} {offer.city}".strip(),
                "is_verified": offer.is_verified,
                "years": offer.years,
                "product_url": offer.product_url,
                "image_url": offer.image_url,
                "quantity_prices": offer.quantity_prices
            }
        else:
            return {"found": False, "error": "No matching product found"}
            
    except Exception as e:
        return {"found": False, "error": str(e)}


def find_1688_price_for_product(keepa_product: Dict, 
                                 target_moq: int = 100) -> Optional[Dict]:
    """
    Find 1688 purchase prices for Keepa products
    
    Automatically extract image URLs from product data and search
    
    Args:
        keepa_product: Keepa product data
        target_moq: Target minimum order quantity
        
    Returns:
        Price Information Dictionary
    """
    image_url = extract_image_url_from_keepa(keepa_product)
    
    if not image_url:
        return {"found": False, "error": "Unable to extract image URL from product data"}
    
    return find_1688_price(image_url, target_moq)


if __name__ == "__main__":
    # test
    print("1688 Image search crawler module")
    print("=" * 60)
    
    # Test image extraction
    test_products = [
        # Keepa CSV format
        {'Image': 'https://m.media-amazon.com/images/I/71h2vMaS4bL.jpg;https://m.media-amazon.com/images/I/71GErqPh7DL.jpg'},
        # Keepa API format
        {'imagesCSV': '41ZulE5Q6OL,51Q3+gP8+WL'},
        # metrics_163 format
        {'metrics_163': {'Image': '71h2vMaS4bL,71GErqPh7DL'}},
    ]
    
    print("\nImage URL extraction test:")
    for i, product in enumerate(test_products, 1):
        url = extract_image_url_from_keepa(product)
        print(f"  test{i}: {url}")
    
    print("\nUsage examples:")
    print("  from cn_1688_crawler import CN1688Crawler, extract_image_url_from_keepa")
    print("  crawler = CN1688Crawler()")
    print("  offers = crawler.search_by_image_url('Image URL')")
    print("\n  # Or directly pass in Keepa product data")
    print("  result = find_1688_price_for_product(keepa_product)")
