"""
1688 以图搜图爬虫模块
=====================
基于1688内部API实现的图片搜索
特点：
- 无需浏览器，直接调用API
- 支持URL/文件/base64图片输入
- 获取价格、MOQ、供应商等完整信息

参考: https://github.com/Zhui-CN/1688_image_search_crawler
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
    """1688供应商报价"""
    offer_id: str
    title: str
    price: float  # 人民币
    moq: int  # 最小起订量
    unit: str
    image_url: str
    company_name: str
    province: str
    city: str
    shop_url: str
    is_verified: bool
    credit_level: str
    years: int  # 诚信通年限
    repurchase_rate: str  # 复购率
    product_url: str
    quantity_prices: List[Dict]  # 阶梯价格
    scores: Dict  # 店铺评分
    position_labels: List[str]  # 标签（如"源头工厂"）


class CN1688Crawler:
    """
    1688以图搜图爬虫
    
    基于1688 H5 API实现
    """
    
    # API配置
    JSV = "2.7.2"
    API_VERSION = "1.0"
    API_KEY = "12574478"
    APP_NAME = "searchImageUpload"
    APP_KEY = "pvvljh1grxcmaay2vgpe9nb68gg9ueg2"
    
    UPLOAD_API_PATH = "mtop.1688.imageService.putImage"
    TOKEN_API_PATH = "mtop.ovs.traffic.landing.seotaglist.queryHotSearchWord"
    
    API_HOST = "https://h5api.m.1688.com"
    
    # 数据提取正则
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
        
        # 禁用SSL验证 (解决某些环境的SSL问题)
        self.session.verify = False
        
        # 忽略SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.token = ""
        self._img_id = None
        self._req_id = None
        self._session_id = None
    
    def _set_cookie_cna(self) -> str:
        """设置cna cookie"""
        timestamp = str(int(time.time() * 1000))
        url = f"https://log.mmstat.com/eg.js?t={timestamp}"
        headers = {"referer": "https://www.1688.com/"}
        
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        cna = self.session.cookies.get("cna")
        
        if not cna:
            raise Exception("无法获取cna cookie")
        
        return cna
    
    def _set_token(self) -> str:
        """获取token"""
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
        
        # 从cookie获取token
        m_h5_tk = self.session.cookies.get("_m_h5_tk")
        if not m_h5_tk:
            raise Exception("无法获取_m_h5_tk cookie")
        
        self.token = m_h5_tk.split("_")[0]
        return self.token
    
    def _upload_image(self, b64_image: str) -> str:
        """
        上传图片到1688
        
        Args:
            b64_image: base64编码的图片
            
        Returns:
            img_id: 图片ID
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
        
        # 生成签名
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
            raise Exception(f"上传图片失败: {result}")
        
        self._img_id = result["data"]["imageId"]
        self._req_id = result["data"]["requestId"]
        self._session_id = result["data"]["sessionId"]
        
        return self._img_id
    
    def _search_offers(self, page: int = 1, use_api: bool = True) -> List[Dict]:
        """
        搜索商品列表
        
        Args:
            page: 页码
            use_api: 是否使用API模式（False使用网页模式）
            
        Returns:
            商品列表
        """
        if use_api:
            return self._search_api(page)
        else:
            return self._search_web()
    
    def _search_api(self, page: int = 1) -> List[Dict]:
        """API模式搜索"""
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
        """网页模式搜索（备用）"""
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
        
        # 提取JSON数据
        match = self.DATA_REG.search(html)
        if not match:
            return []
        
        json_data = json.loads(match.group(1))
        offer_list = json_data.get("data", {}).get("offerList", [])
        
        return offer_list
    
    def _parse_offers(self, offer_list: List[Dict]) -> List[CNSupplierOffer]:
        """解析商品数据"""
        offers = []
        
        for offer in offer_list:
            try:
                # 提取公司信息
                company = offer.get("company") or {}
                # 提取商品信息
                information = offer.get("information") or {}
                # 提取交易服务信息
                trade_service = offer.get("tradeService") or {}
                # 提取交易数量信息
                trade_quantity = offer.get("tradeQuantity") or {}
                # 提取价格信息
                offer_price = (offer.get("tradePrice") or {}).get("offerPrice") or {}
                # 提取标签
                position_labels = (offer.get("commonPositionLabels") or {}).get("offerMiddle") or []
                
                # 解析价格
                price = 0.0
                price_info = offer_price.get("priceInfo") or {}
                if price_info.get("price"):
                    price = float(price_info["price"])
                else:
                    # 从originalValue解析
                    original = offer_price.get("originalValue") or {}
                    integer = original.get("integer", 0)
                    decimals = original.get("decimals", 0)
                    price = float(f"{integer}.{decimals}")
                
                # 解析阶梯价格
                quantity_prices = []
                for q in offer_price.get("quantityPrices", []):
                    q_price_info = q.get("value") or {}
                    q_integer = q_price_info.get("integer", 0)
                    q_decimals = q_price_info.get("decimals", 0)
                    quantity_prices.append({
                        "quantity": q.get("quantity"),
                        "price": float(f"{q_integer}.{q_decimals}")
                    })
                
                # 解析复购率
                repurchase = information.get("rePurchaseRate", "")
                if repurchase and "%" not in str(repurchase):
                    repurchase = f"{round(float(repurchase) * 100, 2)}%"
                
                # 构建结果
                offer_id = str(offer.get("id", ""))
                supplier_offer = CNSupplierOffer(
                    offer_id=offer_id,
                    title=information.get("subject", ""),
                    price=price,
                    moq=trade_quantity.get("quantityBegin", 1),
                    unit=trade_quantity.get("unit", "件"),
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
        """解析评分"""
        try:
            return round(float(score or 0), 1)
        except:
            return 0.0
    
    def search_by_image_url(self, image_url: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        通过图片URL搜索
        
        Args:
            image_url: 图片URL
            max_results: 最大结果数
            
        Returns:
            供应商报价列表
        """
        # 下载图片
        resp = requests.get(image_url, timeout=self.timeout)
        resp.raise_for_status()
        
        # 转base64
        b64_image = base64.b64encode(resp.content).decode()
        
        return self.search_by_base64(b64_image, max_results)
    
    def search_by_file(self, image_path: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        通过本地图片文件搜索
        
        Args:
            image_path: 图片文件路径
            max_results: 最大结果数
            
        Returns:
            供应商报价列表
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode()
        
        return self.search_by_base64(b64_image, max_results)
    
    def search_by_base64(self, b64_image: str, max_results: int = 10) -> List[CNSupplierOffer]:
        """
        通过base64图片搜索
        
        Args:
            b64_image: base64编码的图片
            max_results: 最大结果数
            
        Returns:
            供应商报价列表
        """
        # 初始化session
        self._set_cookie_cna()
        self._set_token()
        
        # 上传图片
        self._upload_image(b64_image)
        
        # 搜索商品
        all_offers = []
        page = 1
        
        while len(all_offers) < max_results:
            offer_list = self._search_offers(page=page, use_api=True)
            
            if not offer_list:
                break
            
            offers = self._parse_offers(offer_list)
            all_offers.extend(offers)
            
            page += 1
            
            # 简单防爬
            time.sleep(0.5)
        
        return all_offers[:max_results]
    
    def find_best_price(self, image_url: str, target_moq: int = 100) -> Optional[CNSupplierOffer]:
        """
        查找最优价格
        
        Args:
            image_url: 图片URL
            target_moq: 目标起订量
            
        Returns:
            最优报价
        """
        offers = self.search_by_image_url(image_url, max_results=20)
        
        if not offers:
            return None
        
        # 筛选符合MOQ的
        suitable = [o for o in offers if o.moq <= target_moq * 2]
        if not suitable:
            suitable = offers
        
        # 综合评分排序
        def score(o: CNSupplierOffer) -> float:
            price_score = 1 / (o.price + 1)
            verified_bonus = 0.3 if o.is_verified else 0
            year_score = min(o.years / 10, 0.2)
            return price_score * 0.6 + verified_bonus + year_score
        
        suitable.sort(key=score, reverse=True)
        
        return suitable[0] if suitable else None


def extract_image_url_from_keepa(product: Dict) -> Optional[str]:
    """
    从Keepa产品数据中提取主图URL
    
    支持多种格式:
    - Keepa API返回的imagesCSV (逗号分隔的图片ID)
    - Keepa CSV导出的Image字段 (分号分隔的完整URL)
    - 163指标中的Image字段
    
    Args:
        product: Keepa产品数据字典
        
    Returns:
        图片URL或None
    """
    # 方法1: 从163指标Image字段获取 (分号分隔的URL列表)
    image_field = product.get("Image", "")
    if image_field and "https://" in image_field:
        urls = image_field.split(";")
        if urls and urls[0].startswith("http"):
            return urls[0].strip()
    
    # 方法2: 从imagesCSV获取 (逗号分隔的图片ID)
    images = product.get("imagesCSV", "")
    if images:
        image_ids = images.split(",")
        if image_ids and image_ids[0]:
            image_id = image_ids[0].strip()
            if image_id:
                return f"https://m.media-amazon.com/images/I/{image_id}.jpg"
    
    # 方法3: 从data.images获取
    data = product.get("data", {})
    image_list = data.get("images", [])
    if image_list:
        return image_list[0]
    
    # 方法4: 从metrics_163字典获取
    metrics = product.get('metrics_163', {})
    if metrics:
        image_value = metrics.get('Image', '')
        if image_value:
            if 'https://' in image_value:
                urls = image_value.split(';')
                if urls:
                    return urls[0].strip()
            else:
                # 逗号分隔的图片ID
                ids = image_value.split(',')
                if ids and ids[0]:
                    return f"https://m.media-amazon.com/images/I/{ids[0].strip()}.jpg"
    
    return None


# 便捷函数
def find_1688_price(image_url: str, target_moq: int = 100) -> Optional[Dict]:
    """
    快速查找1688采购价格
    
    Args:
        image_url: 产品图片URL
        target_moq: 目标起订量
        
    Returns:
        价格信息字典
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
            return {"found": False, "error": "未找到匹配商品"}
            
    except Exception as e:
        return {"found": False, "error": str(e)}


def find_1688_price_for_product(keepa_product: Dict, 
                                 target_moq: int = 100) -> Optional[Dict]:
    """
    为Keepa产品查找1688采购价格
    
    自动从产品数据中提取图片URL并搜索
    
    Args:
        keepa_product: Keepa产品数据
        target_moq: 目标起订量
        
    Returns:
        价格信息字典
    """
    image_url = extract_image_url_from_keepa(keepa_product)
    
    if not image_url:
        return {"found": False, "error": "无法从产品数据中提取图片URL"}
    
    return find_1688_price(image_url, target_moq)


if __name__ == "__main__":
    # 测试
    print("1688 以图搜图爬虫模块")
    print("=" * 60)
    
    # 测试图片提取
    test_products = [
        # Keepa CSV格式
        {'Image': 'https://m.media-amazon.com/images/I/71h2vMaS4bL.jpg;https://m.media-amazon.com/images/I/71GErqPh7DL.jpg'},
        # Keepa API格式
        {'imagesCSV': '41ZulE5Q6OL,51Q3+gP8+WL'},
        # metrics_163格式
        {'metrics_163': {'Image': '71h2vMaS4bL,71GErqPh7DL'}},
    ]
    
    print("\n图片URL提取测试:")
    for i, product in enumerate(test_products, 1):
        url = extract_image_url_from_keepa(product)
        print(f"  测试{i}: {url}")
    
    print("\n使用示例:")
    print("  from cn_1688_crawler import CN1688Crawler, extract_image_url_from_keepa")
    print("  crawler = CN1688Crawler()")
    print("  offers = crawler.search_by_image_url('图片URL')")
    print("\n  # 或直接传入Keepa产品数据")
    print("  result = find_1688_price_for_product(keepa_product)")
