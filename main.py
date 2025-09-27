from flask import Flask, request, Response, json
from scrapling.fetchers import Fetcher
from readability import Document
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from scrapling.fetchers import DynamicFetcher
from datetime import datetime

app = Flask(__name__)

def get_content():
    try:
        url = request.args.get('url') or request.json.get('url')
        is_spa = request.args.get('is_spa') == '1' or (request.is_json and request.json.get('is_spa') == True)
        
        page = None
        if is_spa:
            page = DynamicFetcher.fetch(url, network_idle=True, load_dom=True)
        else:
            page = Fetcher.get(url, timeout=10, retries=1)

        return page
    except Exception as e:
        return e

@app.route('/fetch', methods=['GET', 'POST'])
def get_html():
    try:
        page = get_content()

        if isinstance(page, Exception):
            return str(page), 500
        
        content_type = page.headers.get("content-type", "text/plain")

        return Response(
            response=page._raw_body,      
            status=page.status,         
            headers={"Content-Type": content_type}
        )
        
        

    except Exception as e:
        return str(e), 500
    
@app.route('/content', methods=['GET', 'POST'])
def get_article():
    try:
        page = get_content()

        if isinstance(page, Exception):
            return str(page), 500
        

        # doc = Document(page.html_content)
        page.encoding = 'utf-8'
        html = page._raw_body
        if isinstance(html, bytes):
            html = html.decode('utf-8')

        doc = Document(html)
        soup = BeautifulSoup(doc.summary(keep_all_images=True), "html.parser")
        text = soup.get_text(separator="\n")

        image = page.css_first("meta[property='og:image']::attr(content)")
        image_urls = []

        parsed = urlparse(page.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Regular <img> not inside <picture>
        for img in soup.find_all("img"):
            if img.find_parent("picture") is None:
                full_url = urljoin(base_url, img["src"])
                image_urls.append(full_url)

        # For <picture>, select the "largest" source (last <source> or fallback <img>)
        for picture in soup.find_all("picture"):
            sources = picture.find_all("source")
            if sources:
                largest_src = sources[-1]["srcset"]
                image_urls.append(urljoin(base_url, largest_src))
            else:
                img = picture.find("img")
                if img and "src" in img.attrs:
                    image_urls.append(urljoin(base_url, img["src"]))



        
        data = {
            "title": doc.title(),
            "content": re.sub(r'\n+', '\n', text).strip(),
            "image": image if image else None,
            "images": image_urls,
            "keywords": doc.positive_keywords,
            "url": doc.url,
            "p": page.url,
        }

        return Response(
            response=json.dumps(data, ensure_ascii=False),    
            status=page.status,         
            headers={"Content-Type": 'application/json; charset=utf-8'}
        )

    except Exception as e:
        return str(e), 500

@app.route('/rss', methods=['GET', 'POST'])
def get_links():
    try:
        page = get_content()
        html = page._raw_body
        if isinstance(html, bytes):
            html = html.decode('utf-8') 
        soup = BeautifulSoup(html, "html.parser")

        parsed = urlparse(page.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        links = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            title = a.get_text(separator=" ", strip=True)
            url = urljoin(base_url, a['href'])
            if len(title.split()) >= 5 and url not in seen_urls:  # keep only titles with 5+ words
                links.append({"title": title, "url": url, "pubDate": datetime.utcnow().isoformat() + 'Z'})
                seen_urls.add(url)


        rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
                        <rss version="2.0">
                        <channel>
                            <title>RSS Generator</title>
                            <language>en-us</language>
                """
        
        for item in links:
            rss += f"""
                <item>
                    <title>{item['title']}</title>
                    <link>{item['url']}</link>
                    <pubDate>{item['pubDate']}</pubDate>
                </item>
            """
            
        rss += "</channel></rss>"

        return Response(
            response=rss,
            status=200,
            headers={"Content-Type": 'application/rss+xml; charset=utf-8'}
        )


    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(use_reloader=False)