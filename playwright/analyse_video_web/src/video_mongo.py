from playwright.sync_api import sync_playwright
import re
import os
import requests
from urllib.parse import urlparse

from pymongo import MongoClient


def is_external_link(link, url):
    print("is_external_link")
    print(link)
    if type(link) == tuple:
        url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
        url_only_array = [item for item in link if url_pattern.match(item)][0]
        # 打印结果
        print(url_only_array)
    if link.startswith('http'):  # 判断链接是否以 http 开头，即为绝对路径
        if url in link:  # 如果链接中包含基准 URL，即为内链
            return False;
        else:  # 否则为外链
            return True;
    else:  # 如果链接不是以 http 开头，即为相对路径，也视为内链
        return False;

def start(web_url, deep):

    # 创建一个Playwright实例
    with sync_playwright() as playwright:
        # 在Chromium浏览器上创建一个浏览器实例
        browser = playwright.chromium.launch()

        # 在浏览器上创建一个新的页面
        page = browser.new_page()
        # 设置操作的超时时间为60秒
        page.set_default_timeout(120000)  # 设置超时时间为60秒

        # 导航到目标网页
        page.goto(web_url)

        # 获取所有<a>标签元素
        links = page.query_selector_all('a')

        image_links = []
        txt_links = []

        for link in links:
            # 获取<a>标签下的background-image属性
            style = link.get_attribute('style')

            if style and 'background-image' in style:
                # 使用正则表达式提取背景图像链接
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                if match:
                    href = match.group(1)
                    image_links.append(href)
                # 获取<a>标签的文本内容和链接
                text_content = link.inner_text()
                href = link.get_attribute('href')
                if href:
                    txt_links.append((text_content, href))

            # 连接MongoDB数据库
            client = MongoClient('localhost', 27017)
            db = client['illegal_web']
            collection = db['illegal_web_table1']

            # 插入图片链接数据
            for image_link in image_links:
                external_link = is_external_link(image_link, web_url)
                collection.insert_one({'type': 'image', 'link': image_link, "deep": deep, "from": web_url, "external_link": external_link})

            # 插入文本链接数据
            for text_link in txt_links:
                if type(text_link) == tuple:
                    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
                    text_link = [item for item in text_link if url_pattern.match(item)][0]
                external_link = is_external_link(text_link, web_url)
                collection.insert_one({'type': 'text', 'text': text_link, 'link': text_link, "deep": deep, "from":web_url, "external_link": external_link})

        # 创建保存图片的目录
        images_dir = os.path.join(os.getcwd(), 'images', urlparse(page.url).netloc)
        os.makedirs(images_dir, exist_ok=True)

        # 下载图片并保存到对应的目录
        # for i, image_link in enumerate(image_links):
        #     response = requests.get(web_url+image_link)
        #     print(str(i)+" "+web_url+image_link)
        #     fn = "image_"+str(i+1) + "_" + image_link[-20:].replace('/', '_').replace('}', '')
        #     image_path = os.path.join(images_dir, fn)
        #     with open(image_path, 'wb') as file:
        #         file.write(response.content)
        #     print(f'Downloaded image: {image_path}')


        # 打印结果
        print('Image Links:')
        print(image_links)
        print('txt_links:')
        print(txt_links)

        # 关闭浏览器
        browser.close()


if __name__ == '__main__':
    start_url = "http://www.nongkenfang.com/"
    start_url = "http://www.caominyy5.com/"
    start_deep = 1
    start(start_url, start_deep);


