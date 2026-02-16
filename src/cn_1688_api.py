"""
1688 API 集成模块
================
支持以图搜图获取采购价格

方案选择：
1. TMAPI (第三方) - 简单快速，需要apiToken
2. 1688官方API - 免费，需要企业资质申请
3. 爬虫方案 - 不稳定，不推荐
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
    """1688供应商报价"""
    offer_id: str
    title: str
    price: float  # 人民币
    moq: int  # 最小起订量
    unit: str
    image_url: str
    supplier_name: str
    supplier_years: int
    is_verified: bool
    rating: float
    sales_count: int
    match_score: float  # 图片匹配度 0-1
    product_url: str
    

class TMAPI1688Client:
    """
    TMAPI 1688 API 客户端
    官网: https://tmapi.top
    特点：简单、快速，需要付费订阅
    """
    
    BASE_URL = "http://api.tmapi.top"  # TMAPI使用HTTP协议
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        
    def search_by_image(self, image_url: str, page: int = 1, page_size: int = 20,
                       sort: str = "default", price_start: float = None,
                       price_end: float = None) -> Dict:
        """
        以图搜图
        
        Args:
            image_url: 图片URL（必须是阿里系平台的图片，或先转换）
            page: 页码
            page_size: 每页数量 (最大20)
            sort: 排序方式 (default/sales/price_up/price_down)
            price_start: 最低价格
            price_end: 最高价格
            
        Returns:
            API响应结果
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
        获取商品详情
        
        Args:
            product_id: 1688商品ID
            
        Returns:
            商品详情
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
        """解析API响应为报价列表"""
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
                    unit=item.get("unit", "件"),
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
    1688 官方开放平台 API 客户端
    官网: https://open.1688.com
    特点：免费，需要企业资质申请
    """
    
    GATEWAY_URL = "https://gw.open.1688.com/openapi"
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        
    def _generate_sign(self, params: Dict) -> str:
        """生成API签名"""
        # 按参数名排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 拼接字符串
        sign_str = ""
        for key, value in sorted_params:
            sign_str += f"{key}{value}"
        
        # 添加secret
        sign_str = self.app_secret + sign_str + self.app_secret
        
        # MD5加密
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    def search_by_image(self, image_url: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        以图搜图 (alibaba.product.image.similar.offer.search)
        
        注意：需要先申请API权限
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
    采购价格查找器
    整合多种方式获取1688采购价格
    """
    
    def __init__(self, 
                 tmapi_token: Optional[str] = None,
                 alibaba_app_key: Optional[str] = None,
                 alibaba_app_secret: Optional[str] = None):
        """
        初始化
        
        Args:
            tmapi_token: TMAPI的apiToken（推荐，最简单）
            alibaba_app_key: 1688开放平台App Key
            alibaba_app_secret: 1688开放平台App Secret
        """
        self.tmapi_client = None
        self.alibaba_client = None
        
        if tmapi_token:
            self.tmapi_client = TMAPI1688Client(tmapi_token)
        
        if alibaba_app_key and alibaba_app_secret:
            self.alibaba_client = Alibaba1688Client(alibaba_app_key, alibaba_app_secret)
    
    @classmethod
    def from_env(cls) -> "CNProcurementFinder":
        """从环境变量创建实例"""
        return cls(
            tmapi_token=os.getenv("TMAPI_TOKEN"),
            alibaba_app_key=os.getenv("ALIBABA_APP_KEY"),
            alibaba_app_secret=os.getenv("ALIBABA_APP_SECRET")
        )
    
    def search_best_price(self, image_url: str, target_moq: int = 1,
                          max_results: int = 10) -> Optional[CNSupplierOffer]:
        """
        搜索最优价格
        
        Args:
            image_url: 产品图片URL
            target_moq: 目标起订量
            max_results: 最大结果数
            
        Returns:
            最优报价，或None
        """
        if not self.tmapi_client:
            raise ValueError("需要提供TMAPI_TOKEN或使用其他方式")
        
        # 调用TMAPI搜索
        response = self.tmapi_client.search_by_image(
            image_url=image_url,
            page_size=min(max_results, 20),
            sort="price_up"  # 按价格升序
        )
        
        if response.get("status") != "success":
            return None
        
        offers = self.tmapi_client.parse_offers(response)
        
        if not offers:
            return None
        
        # 筛选符合起订量的报价，并按价格排序
        suitable_offers = [
            o for o in offers 
            if o.moq <= target_moq * 2  # 允许MOQ稍高一些
        ]
        
        if not suitable_offers:
            suitable_offers = offers
        
        # 综合评分排序（价格权重0.6，匹配度权重0.2，销量权重0.2）
        def score_offer(o: CNSupplierOffer) -> float:
            price_score = 1 / (o.price + 1)  # 价格越低分越高
            match_score = o.match_score
            sales_score = min(o.sales_count / 1000, 1)  # 销量归一化
            
            # 认证商家加分
            verified_bonus = 0.2 if o.is_verified else 0
            
            return price_score * 0.6 + match_score * 0.2 + sales_score * 0.1 + verified_bonus
        
        suitable_offers.sort(key=score_offer, reverse=True)
        
        return suitable_offers[0] if suitable_offers else None
    
    def search_multiple_prices(self, image_url: str, 
                               count: int = 5) -> List[CNSupplierOffer]:
        """
        搜索多个报价供选择
        
        Args:
            image_url: 产品图片URL
            count: 返回数量
            
        Returns:
            报价列表
        """
        if not self.tmapi_client:
            raise ValueError("需要提供TMAPI_TOKEN")
        
        response = self.tmapi_client.search_by_image(
            image_url=image_url,
            page_size=min(count, 20)
        )
        
        return self.tmapi_client.parse_offers(response)


def get_product_main_image(keepa_product: Dict) -> Optional[str]:
    """
    从Keepa产品数据中获取主图URL
    
    Args:
        keepa_product: Keepa API返回的产品数据
        
    Returns:
        图片URL或None
    """
    # 尝试获取图片
    images = keepa_product.get("imagesCSV", "")
    if images:
        # Keepa的图片格式是逗号分隔的图片ID
        image_ids = images.split(",")
        if image_ids:
            # 构造图片URL
            # 注意：Keepa的图片可能需要特殊处理才能用于1688搜索
            image_id = image_ids[0]
            return f"https://images-na.ssl-images-amazon.com/images/I/{image_id}"
    
    # 尝试从data中获取
    data = keepa_product.get("data", {})
    if data:
        image_list = data.get("images", [])
        if image_list:
            return image_list[0]
    
    return None


def find_procurement_price(keepa_product: Dict, 
                           tmapi_token: Optional[str] = None) -> Dict:
    """
    为Keepa产品查找采购价格
    
    Args:
        keepa_product: Keepa产品数据
        tmapi_token: TMAPI token
        
    Returns:
        包含采购信息的字典
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
    
    # 获取产品图片
    image_url = get_product_main_image(keepa_product)
    
    if not image_url:
        result["error"] = "无法获取产品图片"
        return result
    
    # 创建finder
    finder = CNProcurementFinder(tmapi_token=tmapi_token)
    
    try:
        # 搜索多个报价
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


# 便捷函数
def quick_find_price(asin: str, keepa_api_key: str, tmapi_token: str) -> Dict:
    """
    快速查找ASIN的采购价格
    
    这个函数整合Keepa和1688 API
    """
    import keepa
    
    # 获取Keepa数据
    api = keepa.Keepa(keepa_api_key)
    products = api.product_finder({
        'asin': [asin],
        'perPage': 1
    })
    
    if not products:
        return {"error": "Keepa未找到产品"}
    
    # 查找采购价格
    return find_procurement_price(products[0], tmapi_token)


if __name__ == "__main__":
    # 测试代码
    print("1688 API模块已加载")
    print("\n使用方法:")
    print("1. 设置环境变量 TMAPI_TOKEN=your_token")
    print("2. 使用 CNProcurementFinder.from_env()")
    print("3. 调用 search_best_price(image_url)")
    print("\n获取TMAPI Token:")
    print("  访问 https://tmapi.top 注册并获取")
