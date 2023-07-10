import re

import requests
from playwright.sync_api import sync_playwright
from pymongo import MongoClient

# def get_image():
#     image_links = []
#
#
#     # 创建保存图片的目录
#     images_dir = os.path.join(os.getcwd(), 'images', urlparse(page.url).netloc)
#     os.makedirs(images_dir, exist_ok=True)
#
#     # 下载图片并保存到对应的目录
#     for i, image_link in enumerate(image_links):
#         real_url = image_link if "http" in image_link else web_url + image_link
#
#         response = requests.get(real_url)
#         print(str(i) + " " + real_url)
#         fn = "image_" + str(i + 1) + "_" + image_link[-20:].replace('/', '_').replace('}', '')
#         image_path = os.path.join(images_dir, fn)
#         with open(image_path, 'wb') as file:
#             file.write(response.content)
#         print(f'Downloaded image: {image_path}')
#
#     # 打印结果
#     print('Image Links:')
#     print(image_links)


# 下载某个url所有的标签、文本
def download_website_text_and_links(url, is_phone=False, headless=True):
    with sync_playwright() as playwright:
        if is_phone:
            iphone = playwright.devices['iPhone 12 Pro Max']
            browser = playwright.webkit.launch(headless=headless)
            context = browser.new_context(**iphone, locale='zh-CN')
            page = context.new_page()
        else:
            browser = playwright.chromium.launch(headless=headless)
            # browser = playwright.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
        page.goto(url, timeout=8*1000)
        s = page.content()
        page_text = page.inner_text('body')  # 获取页面的文本内容
        page_text = page_text.split("\n")
        unique_list = list(dict.fromkeys(page_text))

        # page_links = [link.get_attribute('href') for link in page.query_selector_all('a')]  # 获取页面中所有链接的 href 属性值
        links = page.query_selector_all('a')
        image_links = []
        txt_links = []
        browser.close()
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

        internal_links = []  # 保存内链
        external_links = []  # 保存外链
        internal_links_image = []  # 保存内链
        external_links_image = []  # 保存外链
        for link in links:
            if link.startswith('http'):  # 判断链接是否以 http 开头，即为绝对路径
                if url in link:  # 如果链接中包含基准 URL，即为内链
                    internal_links.append(link)
                else:  # 否则为外链
                    external_links.append(link)
            else:  # 如果链接不是以 http 开头，即为相对路径，也视为内链
                internal_links.append(link)

    return unique_list, internal_links, external_links, s

def get_website_source(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve website source. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred: {str(e)}")


if __name__ == '__main__':
    # client = MongoClient('mongodb://zhuoheng:Qweqwe123_@101.43.113.210:27017')
    # # 选择要使用的数据库
    # db = client['illegal_web']
    # # 选择要使用的集合（表）
    # collection = db['illegal_web_list']
    # collection.insert_one({'type': 'text'})

    url = "https://dymiji.com/"
    # unique_list, internal_links, external_links, s = download_website_text_and_links(url)
    # print(internal_links)
    # print(s)

    source_code = get_website_source(url)
    print(source_code)



