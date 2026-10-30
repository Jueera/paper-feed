"""Build a static reading page; publish only feed and generated public outputs."""
import datetime
import html
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit


def safe_url(value):
    try:
        return value if urlsplit(value).scheme in {"http", "https"} else "#"
    except ValueError:
        return "#"


def main():
    site = Path('_site')
    site.mkdir(exist_ok=True)
    root = ET.parse('filtered_feed.xml').getroot()
    items = root.findall('./channel/item')
    status = json.loads(Path('fetch_status.json').read_text(encoding='utf-8'))
    timestamp = datetime.datetime.fromisoformat(status['updated_at'].replace('Z', '+00:00'))
    timestamp = timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    cards = []
    for item in items[:100]:
        title = html.escape(item.findtext('title', ''))
        link = html.escape(safe_url(item.findtext('link', '')), quote=True)
        journal = html.escape(item.findtext('{http://purl.org/dc/elements/1.1/}source', ''))
        date = html.escape(item.findtext('pubDate', '')[:25])
        cards.append(f'<article><small>{journal} · {date}</small><h2><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h2></article>')
    failures = ''.join(
        '<li>' + html.escape(s.get('source') or s['url']) + ' — ' + html.escape(s.get('error', '')) + '</li>'
        for s in status['sources'] if not s['ok']
    )
    issues = f'<details><summary>查看未成功抓取的期刊源</summary><ul>{failures}</ul></details>' if failures else ''
    body = '\n'.join(cards) or '<p>本轮没有匹配的论文。</p>'
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>催化与非晶材料文献追踪</title>
<link rel="alternate" type="application/rss+xml" title="文献订阅" href="filtered_feed.xml">
<style>body{{font:16px/1.7 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 24px;color:#172b36;background:#f8fafb}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:19px;margin:8px 0}}a{{color:#155e75;text-decoration:none}}a:hover{{text-decoration:underline}}article{{background:white;border:1px solid #dbe5ea;border-radius:12px;padding:18px;margin:14px 0}}small,.muted{{color:#526873}}nav{{display:flex;gap:20px;flex-wrap:wrap}}details{{margin:20px 0;overflow-wrap:anywhere}}.tag{{display:inline-block;background:#e3f0f2;border-radius:6px;padding:3px 10px;margin:4px}}</style></head>
<body><h1>催化与非晶材料文献追踪</h1>
<p><span class="tag">电解水</span><span class="tag">非晶与局域有序</span><span class="tag">活性位点与结构演化</span><span class="tag">电荷与自旋</span></p>
<nav><a href="filtered_feed.xml">RSS 订阅地址</a><a href="https://github.com/Jueera/paper-feed/actions">自动更新状态</a><a href="https://github.com/Jueera/paper-feed/blob/main/keywords.dat">检索词</a></nav>
<p class="muted">最近抓取 {timestamp:%Y-%m-%d %H:%M}（北京时间） · 成功 {status['successful_sources']}/{status['total_sources']} 个期刊源 · 累积 {len(items)} 篇</p>
<p>每 8 小时计划更新。按标题和期刊 RSS 提供的摘要匹配，不能替代完整文献检索。非晶及机制类补充文献可能涉及其他催化反应。当前未启用 AI 摘要。</p>
{issues}<h2>最新论文（最多显示 100 篇）</h2>{body}
<footer class="muted">基于 <a href="https://github.com/Jarvis-Towne/paper-feed">paper-feed</a>。RSS 最多保留 1000 篇。部分出版社可能限制自动抓取。</footer>
</body></html>'''
    (site / 'index.html').write_text(page, encoding='utf-8')
    (site / '.nojekyll').touch()
    for name in ['filtered_feed.xml', 'fetch_status.json']:
        shutil.copyfile(name, site / name)
    for name in ['ai_summary.html', 'ai_summary_feed.xml']:
        if Path(name).is_file():
            shutil.copyfile(name, site / name)
    print(f'Built reading page with {len(items)} RSS items')


if __name__ == '__main__':
    main()
