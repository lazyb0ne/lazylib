import time
# https://m.ss-gate.org/2321.html
# https://m.ss-gate.org/12121.html
# page.goto('https://www.ss-gate.org/42933.html')

# python3 -m playwright codegen --target python -o 'auto.py' -b chromium https://www.ss-gate.org/42933.html

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import asyncio
import wget
import requests

with sync_playwright() as p:
    iphone = p.devices['iPhone 12 Pro Max']
    browser = p.webkit.launch(headless=False)
    context = browser.new_context(**iphone, locale='zh-CN')
    page = context.new_page()

async def main_demo():
      async with async_playwright() as pw:
          browser = await pw.chromium.launch()
          page = await browser.new_page()
          await page.goto('https://https://www.baidu.com/s?wd=小说')
          time.sleep(3)

          # all_items = await page.query_selector_all('.product_pod') # item class name
          # books = []
          # for item in all_items:
          #    book = {}
          #    name_el = await item.query_selector('h3')
          #    book['name'] = await name_el.inner_text()
          #    # price_el = await item.query_selector('.price_color')
          #    # book['price'] = await price_el.inner_text()
          #    # stock_el = await item.query_selector('.availability')
          #    # book['stock'] = await stock_el.inner_text()
          #    books.append(book)
          # print(books)
          await browser.close()

# 全局url列表
url_list = []

async def main_huang():
      async with async_playwright() as pw:
          browser = await pw.chromium.launch()
          page = await browser.new_page()
          await page.goto('https://www.ss-gate.org/xuanhuan/')

          all_items = await page.query_selector_all('div.l>ul>li') # item class name
          books = []
          for item in all_items:
            try:
                 book = {}
                 name_el = await item.query_selector('.s1')
                 book['name'] = await name_el.text_content()
                 price_el = await item.query_selector('.s2')
                 book['title'] = await price_el.inner_text()
                 url_el = await item.query_selector('.s2 a')
                 book['url'] = await url_el.get_attribute('href')
                 books.append(book)
                 url_list.append(book['url'])
            except:
                print("main_huang bug ")
            else:
                {}

          print("main_huang Result:")
          print(books)
          await browser.close()

async def get_url_list_app(url):
    print("Url List:")
    comment_list = []

    async with async_playwright() as pw:

        iphone = pw.devices['iPhone 12 Pro Max']
        browser = await pw.webkit.launch(headless=False)
        context = await browser.new_context(**iphone, locale='zh-CN')
        page = await context.new_page()
        await page.goto('https://www.ss-gate.org/'+url)

        title_el = await page.query_selector('.container>.block>.htitle')
        title = await title_el.inner_text()

        info_el = await page.query_selector('.container>.block>.info')
        info = await info_el.inner_text()

        # video_el = await page.query_selector('.header_video>.video>.vjs-tech')
        video_el = await page.query_selector('#my-video_html5_api')
        video_url = await video_el.get_attribute('src')
        print('video_url id %s' % video_url)

        # 下载视频
        # download_video(video_url)

        comment_el = await page.query_selector_all('.item_pl>dl')
        for item in comment_el:
            try:
                avatar_el = await item.query_selector('dt>img')
                avatar = await avatar_el.get_attribute('src')

                name_el = await item.query_selector('dd')
                name = await name_el.inner_text()

                print("avatar %s" % avatar)
                print("name %s" % name)

            except:
                print("get_url_list bug ")
            else:
                {}

        # 模拟点击
        await page.click("class=down_btn")
        time.sleep(3)
        await browser.close()

def download_video(url):
    path = '../videos/a.m3u8'
    wget.download(url, path)


def start():
    idx = 0
    for url in url_list:
        if idx > 1:
            continue
        asyncio.run(get_url_list_app(url))
        print("idx:%d" % idx)
        idx = idx + 1;

book_list = {}

if __name__ == '__main__':
      # 获取列表
      asyncio.run(main_huang())
      # asyncio.run(get_url_list_app('2321.html'))
      # 循环拿数据
      # start()
      # print("================================")
      # print(book_list)

      # asyncio.run(get_url_list_app('2321.html'))

      # 下载1
      # https://www.cfcdnj1.top/filets/1637/dp.m3u8
      # video_url = 'https://www.cfcdnj1.top/filets/1637/dp.m3u8'
      # download_video(video_url)

      # 下载2
      # url = 'https://www.cfcdnj1.top/filets/1637/dp.m3u8'
      # res = requests.get(url)
      # with open('dp.m3u8', 'wb') as f:
      #     f.write(res.content)


