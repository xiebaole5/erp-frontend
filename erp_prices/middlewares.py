# erp_prices/middlewares.py
"""
Scrapy 下载中间件:
- User-Agent 轮换
- 随机代理(预留)
- 请求限流
"""
import random
from scrapy import signals


class RotateUserAgentMiddleware:
    """
    UA 轮换中间件:
    每次请求随机从列表中选择一个 User-Agent
    避免被识别为爬虫
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        # 移动端 UA(部分网站移动版更易抓取)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    ]

    def __init__(self):
        self.user_agent = random.choice(self.USER_AGENTS)

    def process_request(self, request, spider):
        # 随机选择 UA
        request.headers["User-Agent"] = random.choice(self.USER_AGENTS)


class ProxyMiddleware:
    """
    代理中间件(预留):
    通过 request.meta['proxy'] 设置代理
    例如: yield scrapy.Request(url, meta={'proxy': 'http://user:pass@host:port'})
    """
    def process_request(self, request, spider):
        # 如果 spider 设置了代理, 则使用
        proxy = getattr(spider, 'proxy', None)
        if proxy:
            request.meta['proxy'] = proxy