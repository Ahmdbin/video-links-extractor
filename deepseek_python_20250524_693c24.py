import asyncio
from playwright.async_api import async_playwright
import re
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

async def extract_links(url):
    start_time = time.time()
    result = {"m3u8_links": [], "mp4_links": [], "time": 0, "error": None}
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            content = await page.content()
            
            result["m3u8_links"] = re.findall(r'https?://[^\'"]+\.m3u8[^\'"]*', content)
            result["mp4_links"] = re.findall(r'https?://[^\'"]+\.mp4[^\'"]*', content)
            
            await browser.close()
            result["time"] = time.time() - start_time
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>أداة استخراج روابط الفيديو</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                form { display: flex; flex-direction: column; gap: 10px; }
                input, button { padding: 10px; font-size: 16px; }
                .results { margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>🎬 أداة استخراج روابط الفيديو (M3U8 و MP4)</h1>
            <form action="/extract" method="get">
                <input type="url" name="url" placeholder="أدخل رابط الصفحة" required>
                <button type="submit">استخراج الروابط</button>
            </form>
            <div id="results" class="results"></div>
            <script>
                document.querySelector('form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const url = document.querySelector('input').value;
                    const response = await fetch(`/extract?url=${encodeURIComponent(url)}`);
                    const data = await response.json();
                    
                    let html = '<h2>النتائج:</h2>';
                    if (data.error) {
                        html += `<p style="color: red;">خطأ: ${data.error}</p>`;
                    } else {
                        html += `<p><strong>🔗 روابط M3U8:</strong><br>${data.m3u8_links.join('<br>') || 'لا توجد روابط M3U8'}</p>`;
                        html += `<p><strong>🎞️ روابط MP4:</strong><br>${data.mp4_links.join('<br>') || 'لا توجد روابط MP4'}</p>`;
                        html += `<p><strong>⏱️ زمن التنفيذ:</strong> ${data.time.toFixed(2)} ثانية</p>`;
                    }
                    
                    document.getElementById('results').innerHTML = html;
                });
            </script>
        </body>
    </html>
    """

@app.get("/extract")
async def extract(request: Request):
    url = request.query_params.get("url")
    if not url:
        return {"error": "يجب تقديم رابط URL"}
    
    result = await extract_links(url)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)