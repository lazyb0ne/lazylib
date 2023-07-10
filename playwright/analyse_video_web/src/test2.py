import asyncio
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

import asyncio
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright

async def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def get_page_links(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 访问网页
        await page.goto(url)

        # 获取网页源代码
        source_code = await page.content()

        # 获取所有链接
        links = await page.evaluate('''() => {
            const anchorElements = Array.from(document.querySelectorAll('a'));
            const imageElements = Array.from(document.querySelectorAll('img'));

            const links = [];

            // 提取文本链接
            for (const anchor of anchorElements) {
                const text = anchor.textContent?.trim();
                const href = anchor.href?.trim() || '';
                const isInternal = href.startsWith(window.location.origin);

                links.push({
                    type: 'text',
                    text,
                    href,
                    isInternal,
                });
            }

            // 提取图片链接
            for (const image of imageElements) {
                const src = image.src?.trim() || '';
                const href = image.parentElement.href?.trim() || '';
                const isInternal = href.startsWith(window.location.origin);

                links.push({
                    type: 'image',
                    src,
                    href,
                    isInternal,
                });
            }

            return links;
        }''')

        # 检查链接的有效性并删除非法链接
        valid_links = []
        for link in links:
            if link['isInternal']:
                valid_links.append(link)
            else:
                if await is_valid_url(link['href']):
                    valid_links.append(link)

        # 关闭浏览器
        await browser.close()

        return source_code, valid_links


def start():
    # 调用示例函数
    url = 'https://www.lovedan.net/'
    source_code, links = asyncio.run(get_page_links(url))

    # 打印源代码和链接
    # print("Source Code:")
    # print(source_code)

    print("\nLinks:")
    for link in links:
        link_type = 'Image' if link['type'] == 'image' else 'Text'
        link_location = 'Internal' if link['isInternal'] else 'External'
        print(f"Type: {link_type}")
        print(f"Location: {link_location}")
        print(f"URL: {link['href']}")
        if link['type'] == 'image':
            print(f"Image Source: {link['src']}")
        else:
            print(f"Text: {link['text']}")
        print("------")


if __name__ == '__main__':
    # client = MongoClient('mongodb://zhuoheng:Qweqwe123_@101.43.113.210:27017')
    # # 选择要使用的数据库
    # db = client['illegal_web']
    # # 选择要使用的集合（表）
    # collection = db['illegal_web_list']
    # collection.insert_one({'type': 'text'})

    # url = "https://www.lovedan.net/"
    # unique_list, internal_links, external_links, s = download_website_text_and_links(url)
    # print(internal_links)
    # print(s)
    start()


