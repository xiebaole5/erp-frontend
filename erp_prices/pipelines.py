# erp_prices/pipelines.py
import re
import json
from datetime import datetime
from pathlib import Path


class PriceValidationPipeline:
    """
    价格数据验证管道:
    - 检查价格是否合理范围
    - 计算均价
    - 清洗数据
    """
    PRICE_RANGES = {
        'copper': (60000, 120000),   # 铜: 6万-12万/吨
        'zinc': (15000, 35000),      # 锌: 1.5万-3.5万/吨
        'nickel': (100000, 250000),  # 镍: 10万-25万/吨
        'lead': (14000, 22000),     # 铅: 1.4万-2.2万/吨
    }

    def process_item(self, item, spider):
        metal = item.get('metal', '').lower()
        avg = item.get('avg_price')

        if avg and metal in self.PRICE_RANGES:
            lo, hi = self.PRICE_RANGES[metal]
            if not (lo <= avg <= hi):
                spider.logger.warning(
                    f"[{metal}] 价格 {avg} 超出合理范围 [{lo}-{hi}], 已忽略"
                )
                return None  # 丢弃异常价格

        item['timestamp'] = datetime.now().isoformat()
        return item


class HtmlUpdatePipeline:
    """
    HTML 更新管道:
    - 从 Item 中提取最新价格
    - 更新 index.html 中的 basePrices
    - 写入文件并触发 Git push
    """
    HTML_FILE = Path(__file__).parent.parent / "index.html"

    def open_spider(self, spider):
        if not self.HTML_FILE.exists():
            raise FileNotFoundError(f"找不到 {self.HTML_FILE}")
        with open(self.HTML_FILE, "r", encoding="utf-8") as f:
            self.html_content = f.read()

    def process_item(self, item, spider):
        metal = item.get('metal', '').lower()
        avg = item.get('avg_price')
        if not avg:
            return item

        # 替换 index.html 中的硬编码价格
        patterns = {
            'copper': (r'copper:\s*\d+', f'copper: {avg}'),
            'zinc':   (r'zinc:\s*\d+',     f'zinc: {avg}'),
            'nickel': (r'nickel:\s*\d+',   f'nickel: {avg}'),
            'lead':   (r'lead:\s*\d+',     f'lead: {avg}'),
        }

        if metal in patterns:
            pattern, replacement = patterns[metal]
            new_content = re.sub(pattern, replacement, self.html_content)
            if new_content != self.html_content:
                self.html_content = new_content
                spider.logger.info(f"✅ 已更新 {metal} 价格: {avg}")

        return item

    def close_spider(self, spider):
        with open(self.HTML_FILE, "w", encoding="utf-8") as f:
            f.write(self.html_content)
        spider.logger.info(f"💾 已写入 {self.HTML_FILE}")