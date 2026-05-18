#!/usr/bin/env python3
"""
ERP 报价自动更新 - Scrapy 驱动版
每天凌晨1点自动抓取长江有色/上海有色金属价格, 更新 index.html 并推送到 GitHub

依赖:
    pip install scrapy

使用:
    python run_spider.py           # 正常抓取并更新
    python run_spider.py --debug   # 调试模式(保存原始HTML)
"""
import sys
import subprocess
import re
import argparse
from datetime import datetime
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.utils.project import get_project_settings

# 导入 spider
sys.path.insert(0, str(Path(__file__).parent))
from erp_prices.spiders.metals import MetalsSpider


def git_push(html_file: Path, prices: dict):
    """推送更新到 GitHub"""
    try:
        repo_dir = Path(__file__).parent

        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True,
                       capture_output=True, text=True)

        date_str = datetime.now().strftime("%Y%m%d")
        price_str = ", ".join([f"{k}={v}" for k, v in prices.items() if v])
        commit_msg = f"Fairy自动更新-{date_str} ({price_str})"

        result = subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=repo_dir, check=True, capture_output=True, text=True
        )
        print(f"📝 提交: {commit_msg}")

        result = subprocess.run(
            ['git', 'push'],
            cwd=repo_dir, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ 已推送到 GitHub Pages")
            return True
        else:
            print(f"❌ 推送失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Git 操作失败: {e}")
        return False


def update_html(html_file: Path, prices: dict):
    """更新 index.html 中的价格"""
    if not html_file.exists():
        print(f"❌ 找不到 {html_file}")
        return False

    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = []

    for metal, price in prices.items():
        if not price:
            continue
        content = re.sub(
            rf'{metal}:\s*\d+',
            f'{metal}: {price}',
            content
        )
        updated.append(f"{metal}={price}")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"💾 已更新 HTML: {', '.join(updated)}")
    return True


class PriceCollector:
    """Scrapy 信号收集器"""
    def __init__(self):
        self.prices = {"copper": None, "zinc": None, "nickel": None, "lead": None}

    def item_scraped(self, item, response, spider):
        metal = item.get('metal')
        avg = item.get('avg_price')
        if metal and avg:
            self.prices[metal] = avg
            print(f"  ✅ {metal}: {avg} 元/吨")


def run_spider():
    """运行 Scrapy 爬虫并收集结果"""
    settings = get_project_settings()
    collector = PriceCollector()

    process = CrawlerProcess(settings={
        **dict(settings),
        "LOG_LEVEL": "INFO",
    })

    crawler = process.create_crawler(MetalsSpider)
    crawler.signals.connect(collector.item_scraped, signal=signals.item_scraped)

    print("🕷️  启动 Scrapy 爬虫...")
    process.crawl(crawler)
    process.start()

    return collector.prices


def main():
    print(f"\n[{datetime.now()}] === ERP报价 Scrapy 抓取开始 ===\n")

    prices = run_spider()

    print("\n" + "=" * 50)
    print("抓取结果:")
    for metal, price in prices.items():
        status = f"✅ {price}" if price else "❌ 未抓到"
        print(f"  {metal:8s}: {status}")
    print("=" * 50 + "\n")

    # 默认值兜底
    defaults = {
        "copper": 94850,
        "zinc": 24650,
        "nickel": 144350,
        "lead": 16450,
    }
    for k, v in defaults.items():
        if not prices.get(k):
            prices[k] = v
            print(f"⚠️  {k} 使用默认值: {v}")

    html_file = Path(__file__).parent / "index.html"
    if update_html(html_file, prices):
        git_push(html_file, prices)

    print(f"\n[{datetime.now()}] === 更新完成 ===\n")


if __name__ == "__main__":
    main()