import time
# https://m.ss-gate.org/2321.html
# https://m.ss-gate.org/12121.html
# page.goto('https://www.ss-gate.org/42933.html')
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import asyncio

with sync_playwright() as p:
    iphone = p.devices['iPhone 12 Pro Max']
    browser = p.webkit.launch(headless=False)
    context = browser.new_context(**iphone, locale='zh-CN')
    page = context.new_page()

    # time.sleep(3)
    # page.wait_for_load_state(state='networkidle')
    # page.screenshot(path='browser-iphone.png')
    # browser.close()

async def main_demo():
      async with async_playwright() as pw:
          browser = await pw.chromium.launch()
          page = await browser.new_page()
          await page.goto('https://books.toscrape.com')

          all_items = await page.query_selector_all('.product_pod') # item class name
          books = []
          for item in all_items:
             book = {}
             name_el = await item.query_selector('h3')
             book['name'] = await name_el.inner_text()
             # price_el = await item.query_selector('.price_color')
             # book['price'] = await price_el.inner_text()
             # stock_el = await item.query_selector('.availability')
             # book['stock'] = await stock_el.inner_text()
             books.append(book)
          print(books)
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

async def get_url_list(url):
    print("Url List:")
    book_info = {}
    async with async_playwright() as pw:

        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.ss-gate.org/'+url)
        all_items = await page.query_selector_all('div>dl>dd')
        # book_title_el = await page.query_selector('.book div>.info div>.h1')
        title_el = await page.query_selector('.book>.info>h1')
        book_info['title'] = await title_el.inner_text()

        title_el = await page.query_selector('.book>.info>.cover>img')
        book_info['url'] = await title_el.get_attribute('src')

        el = await page.query_selector('.book>.info>.small>span')
        book_info['author'] = await el.inner_text()

        title_list = []
        for item in all_items:
            try:
                # book = {}
                title_el = await item.query_selector('a')
                # book['title'] = await title_el.text_content()
                title = await title_el.text_content()
                # price_el = await item.query_selector('.s2')
                # book['title'] = await price_el.inner_text()
                # url_el = await item.query_selector('.s2 a')
                # book['url'] = await url_el.get_attribute('href')
                title_list.append(title)
            except:
                {
                    print("get_url_list bug ")
                }
            else:
                {}

        print("get_url_list Result:")
        print(title_list)
        book_info['list'] = title_list
        print("Book Info:")
        print(book_info)

        # book_list.append(book_info)
        book_list[book_info['title']] = book_info

        await browser.close()

def start():
    idx = 0
    for url in url_list:
        if idx > 1:
            continue
        asyncio.run(get_url_list(url))
        print("idx:%d" % idx)
        idx = idx + 1;

book_list = {}

if __name__ == '__main__':
      # 获取列表
      asyncio.run(main_huang())
      # asyncio.run(get_url_list('10815.html'))
      # 循环拿数据
      start()
      # print("================================")
      print(book_list)

