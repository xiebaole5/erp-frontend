# erp_prices/items.py
import scrapy


class MetalPriceItem(scrapy.Item):
    """金属价格数据 Item"""
    metal = scrapy.Field()      # 金属名称: copper/zinc/nickel/lead
    buy_price = scrapy.Field()  # 买入价
    sell_price = scrapy.Field() # 卖出价
    avg_price = scrapy.Field()  # 均价
    unit = scrapy.Field()       # 单位: 元/吨
    source = scrapy.Field()     # 数据来源: ccmn/smm
    timestamp = scrapy.Field()   # 抓取时间
    raw_html = scrapy.Field()   # 原始HTML片段(调试用)


class ErpPriceItem(scrapy.Item):
    """最终ERP报价 Item"""
    copper = scrapy.Field()
    zinc = scrapy.Field()
    nickel = scrapy.Field()
    lead = scrapy.Field()
    updated_at = scrapy.Field()
    source = scrapy.Field()