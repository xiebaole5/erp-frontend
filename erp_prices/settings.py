# Define project name
BOT_NAME = "erp_prices"
SPIDER_MODULES = ["erp_prices.spiders"]
NEWSPIDER_MODULE = "erp_prices.spiders"

# ==================== 核心反爬配置 ====================
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# 禁用 robots.txt
ROBOTSTXT_OBEY = False

# 下载延迟(秒), 避免请求过快被封
DOWNLOAD_DELAY = 1.5

# 自动限速(根据服务器响应自动调整)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.5
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# 重试配置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# 超时(秒)
DOWNLOAD_TIMEOUT = 30

# Cookie 启用(关键! 很多网站依赖Cookie做反爬验证)
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# 默认请求头(模拟浏览器)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# 启用 HTTP 缓存(减少重复请求)
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
HTTPCACHE_POLICY = "scrapy.extensions.httpcache.RFC2616Policy"

# Telnet 控制台(调试用)
TELNETCONSOLE_ENABLED = False

# Log 级别
LOG_LEVEL = "INFO"

# ==================== Item Pipeline ====================
ITEM_PIPELINES = {
    "erp_prices.pipelines.PriceValidationPipeline": 300,
    "erp_prices.pipelines.HtmlUpdatePipeline": 301,
}