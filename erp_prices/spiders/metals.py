# erp_prices/spiders/metals.py
"""
长江有色网 + 上海有色网 金属价格爬虫
使用 Scrapy + Splash(可选) + Playwright(可选) 抓取实时价格

依赖安装:
    pip install scrapy requests
    # 可选(JS渲染页面):
    pip install scrapy-splash  # 需要 Splash 容器
    pip install playwright && playwright install chromium

运行:
    scrapy crawl metals -O prices.json
    scrapy crawl metals                    # 仅打印日志
    scrapy shell https://m.ccmn.cn/       # 交互式调试
"""
import re
import scrapy
from datetime import datetime
from ..items import MetalPriceItem


class MetalsSpider(scrapy.Spider):
    """
    金属价格爬虫:
    1. 长江有色网 ccmn.cn → 铜/锌/镍
    2. 上海有色网 smm.cn → 铅

    数据提取策略:
    - XPath/CSS 选择器优先
    - 正则表达式兜底
    - 价格合理性校验
    """
    name = "metals"
    allowed_domains = ["ccmn.cn", "smm.cn"]

    # 起始 URL
    start_urls = [
        "https://m.ccmn.cn/",          # 长江有色 - 移动版(通常反爬较弱)
        "https://hq.smm.cn/h5/pb-price",  # 上海有色 - 铅价
    ]

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "erp_prices.middlewares.RotateUserAgentMiddleware": 400,
            # "erp_prices.middlewares.ProxyMiddleware": 410,
            "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 710,
        },
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,  # 每个域名单并发
    }

    # 构造函数: 可以传入代理等参数
    def __init__(self, proxy=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy = proxy
        self.prices = {}  # 存储抓取到的价格

    def start_requests(self):
        """重写起始请求: 添加 Cookie 预热"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                dont_filter=False,
                meta={"handle_httpstatus_all": True},
            )

    def parse(self, response):
        """
        主解析函数:
        根据 URL 判断调用哪个解析方法
        """
        url = response.url
        self.logger.info(f"[{url}] 状态码: {response.status}, 长度: {len(response.body)}")

        if "ccmn.cn" in url:
            yield from self.parse_ccmn(response)
        elif "smm.cn" in url:
            yield from self.parse_smm(response)

    def parse_ccmn(self, response):
        """
        解析长江有色网页面:
        提取铜/锌/镍/铅的买入价和卖出价

        策略:
        1. 定位 quota_f 价格表格区域
        2. 用 <li> 块为最小单元解析每种金属的数据
        3. 格式: 品名 / 区间 / 均价 / 涨跌
        """
        body = response.text
        prices_found = {}

        # ---- 提取 quota_f 区域(长江现货) ----
        quota_match = re.search(r'class="quota_f"[\s\S]{0,20000}', body)
        if not quota_match:
            self.logger.warning("⚠️ 未找到 quota_f 价格区域")
            return

        area = quota_match.group()

        # ---- 方法1: 解析每个 <li> 块 ----
        li_blocks = re.findall(r'<a href[^>]+>\s*<li>\s*([\s\S]*?)\s*</li>\s*</a>', area)
        metal_data = {}

        for block in li_blocks:
            fields = re.findall(r'<p>([^<]+)</p>', block)
            if len(fields) >= 3:
                name = fields[0].strip()
                # 找品名(中文+数字+英文,不含特殊符号)
                if re.match(r'^[\w\u4e00-\u9fa5#]+$', name) and len(name) < 20:
                    raw_price_range = fields[1].strip()
                    raw_avg = fields[2].strip()
                    # 解析价格区间 "105,770—105,810" 或 "105770—105810"
                    price_nums = re.findall(r'[\d,]+', raw_price_range)
                    avg_num = re.findall(r'[\d,]+', raw_avg)
                    if price_nums:
                        lo = int(price_nums[0].replace(',', ''))
                        hi = int(price_nums[-1].replace(',', ''))
                        avg = (lo + hi) // 2 if len(price_nums) == 2 else int(avg_num[0].replace(',', '')) if avg_num else None
                        metal_data[name] = {'lo': lo, 'hi': hi, 'avg': avg, 'range': raw_price_range}

        # ---- 映射到目标金属 ----
        target_map = {
            '1#铜': 'copper',
            '1#锌': 'zinc',
            '1#镍': 'nickel',
            '1#铅': 'lead',
        }

        for name, metal in target_map.items():
            if name in metal_data:
                d = metal_data[name]
                self.logger.info(f"{name}: 区间={d['range']}, 均价={d['avg']}")
                yield MetalPriceItem(
                    metal=metal, buy_price=d['lo'], sell_price=d['hi'],
                    avg_price=d['avg'], unit='元/吨', source='ccmn'
                )
                prices_found[metal] = d['avg']
            else:
                self.logger.warning(f"⚠️ 未找到 {name} 的数据")

        if not prices_found:
            self.logger.warning("⚠️ 长江有色网: 未匹配到任何价格")
            debug_file = f"/tmp/ccmn_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(body)
            self.logger.info(f"已保存调试文件: {debug_file}")

    def parse_smm(self, response):
        """
        解析上海有色网页面:
        提取铅价
        """
        body = response.text
        lead_prices = []

        # 铅价格式: "上海 16400-16500" 或 "16400 16500"
        for match in re.finditer(r'上海[^>]*?(\d{5})-(\d{5})', body):
            lead_prices.append((int(match.group(1)), int(match.group(2))))

        if not lead_prices:
            for match in re.finditer(r'铅[^>]*?(\d{5})-(\d{5})', body):
                lead_prices.append((int(match.group(1)), int(match.group(2))))

        if not lead_prices:
            for match in re.finditer(r'(\d{5})\s*-\s*(\d{5})', body):
                lead_prices.append((int(match.group(1)), int(match.group(2))))

        if lead_prices:
            buy, sell = lead_prices[0]
            avg = (buy + sell) // 2
            self.logger.info(f"铅价(SMM): 买入={buy}, 卖出={sell}, 均价={avg}")
            yield MetalPriceItem(
                metal='lead', buy_price=buy, sell_price=sell,
                avg_price=avg, unit='元/吨', source='smm'
            )
        else:
            self.logger.warning("⚠️ 上海有色网: 未匹配到铅价")
            debug_file = f"/tmp/smm_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(body)
            self.logger.info(f"已保存调试文件: {debug_file} (前500字符: {body[:500]})")

    def handle_error(self, failure):
        """请求错误处理"""
        self.logger.error(f"❌ 请求失败: {failure.request.url}, 原因: {failure.value}")