from flask import Flask, request, Response
from scrapling.fetchers import Fetcher

app = Flask(__name__)

def get_content(url):
    try:
        page = Fetcher.get(url, timeout=10)
        return page
    except Exception as e:
        return e

@app.route('/fetch', methods=['GET', 'POST'])
def get_html():
    try:
        url = request.args.get('url') or request.json.get('url')
        page = get_content(url)

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


if __name__ == "__main__":
    app.run(use_reloader=False)
