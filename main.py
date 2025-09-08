from flask import Flask, request, Response
from scrapling.fetchers import Fetcher

app = Flask(__name__)

async def get_content(url):
    try:
        page = Fetcher.get(url)
        return page
    except Exception as e:
        return e

@app.route('/fetch', methods=['GET', 'POST'])
async def get_html():
    try:
        url = request.args.get('url') or request.json.get('url')
        page = await get_content(url)

        if isinstance(page, Exception):
            return str(page), 500

        # رجّع نفس الاستجابة الأصلية
        return Response(
            response=page._raw_body,      
            status=page.status,         
            headers={"Content-Type": page.headers.get("content-type", "text/plain")}
        )

    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    app.run(use_reloader=False)
