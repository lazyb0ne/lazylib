import asyncio
from datetime import datetime, timedelta

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import re
import os
import requests
from urllib.parse import urlparse

from pymongo import MongoClient, collection
from bs4 import BeautifulSoup
import re
from tldextract import extract
import pandas as pd
import tempfile
from urllib.parse import urljoin


# 1、源码要保存
# 2、区分后台上传的图片、静态的图片
# 3、要保留网站快照
# 4、deep 跑3-4层
# 5、把网址跑下来

def is_external_link(link, url):
    print("is_external_link")
    print(link)
    if type(link) == list:
        return False;
    if isinstance(link, str) and len(link) < 8:
        return False;
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
        # browser = playwright.chromium.launch()
        iphone = playwright.devices['iPhone 12 Pro Max']
        browser = playwright.webkit.launch(headless=False)
        context = browser.new_context(**iphone, locale='zh-CN')
        page = context.new_page()

        # 在浏览器上创建一个新的页面
        page = browser.new_page()
        # 设置操作的超时时间为60秒
        page.set_default_timeout(120000)  # 设置超时时间为60秒

        # 导航到目标网页
        page.goto(web_url)

        # 获取所有<a>标签元素
        links = page.query_selector_all('a')

        print("-------------links")
        print(links)

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

            # 连接本地MongoDB数据库
            # client = MongoClient('localhost', 27017)
            # db = client['illegal_web']
            # collection = db['illegal_web_table1']
            # 连接线上MongoDB数据库
            client = MongoClient('mongodb://zhuoheng:Qweqwe123_@101.43.113.210:27017')
            # 选择要使用的数据库
            db = client['illegal_web']
            # 选择要使用的集合（表）
            collection = db['illegal_web_list']

            # 插入图片链接数据
            for image_link in image_links:
                external_link = is_external_link(image_link, web_url)
                collection.insert_one({'type': 'image', 'link': image_link, "deep": deep, "from": web_url, "external_link": external_link})

            # 插入文本链接数据
            for text_link in txt_links:
                if type(text_link) == tuple:
                    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
                    text_link = [item for item in text_link if url_pattern.match(item)]
                external_link = is_external_link(text_link, web_url)
                collection.insert_one({'type': 'text', 'text': text_link, 'link': text_link, "deep": deep, "from":web_url, "external_link": external_link})

        # 创建保存图片的目录
        images_dir = os.path.join(os.getcwd(), 'images', urlparse(page.url).netloc)
        os.makedirs(images_dir, exist_ok=True)

        # 下载图片并保存到对应的目录
        for i, image_link in enumerate(image_links):
            real_url = image_link if "http" in image_link else web_url+image_link

            response = requests.get(real_url)
            print(str(i)+" "+real_url)
            fn = "image_"+str(i+1) + "_" + image_link[-20:].replace('/', '_').replace('}', '')
            image_path = os.path.join(images_dir, fn)
            with open(image_path, 'wb') as file:
                file.write(response.content)
            print(f'Downloaded image: {image_path}')

        # 打印结果
        print('Image Links:')
        print(image_links)
        print('txt_links:')
        print(txt_links)

        # 关闭浏览器
        browser.close()


async def get_page_source(url):
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            s = await page.content()
            await browser.close()
            return s
    except Exception as e:
        print(f"Error retrieving page source for URL: {url}\nError: {str(e)}")
        return ''


def get_last_updated_time(url):
    document = collection['url_list'].find_one({'url': url}, {'updated_at': 1})
    if document and 'updated_at' in document:
        return document['updated_at']
    return None


def get_source_by_url(url):
    document = collection['url_list'].find_one({'url': url}, {'source': 1})
    if document and 'source' in document:
        return document['source']
    return None


def update_page_source(url, source):
    query = {'url': url}
    update = {'$set': {'source': source, 'updated_at': datetime.now()}}
    collection['url_list'].update_one(query, update)


class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            client = MongoClient('mongodb://zhuoheng:Qweqwe123_@101.43.113.210:27017')
            database = client['illegal_web']
            cls._instance = database
            # cls._instance = database['web_src']
            # cls._instance = database['url_list']
        return cls._instance

collection = MongoDB()


def find_external_links(source):
    soup = BeautifulSoup(source, 'html.parser')
    external_links = set()

    # Find all <a> tags with href attribute
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']

        # Check if the link is an external link
        if is_external_link(href):
            external_links.add(href)

    return list(external_links)


def save_external_links(source, source_url, deep):
    external_links = find_external_links(source)
    print(external_links)
    for link in external_links:
        domain = extract(link).registered_domain
        document = {
            'url': domain,
            'last_crawled_at': datetime.now(),
            'source_url': source_url,
            'deep': deep,
        }
        collection['url_list'].update_one({'url': domain}, {'$set': document}, upsert=True)


def add_http_prefix(domain):
    if domain.startswith('http://') or domain.startswith('https://'):
        return domain
    else:
        return 'http://' + domain


def get_url():
    query = {'deep': 1}
    urls = collection['url_list'].find(query)
    for url in urls:
        url_tmp = add_http_prefix(url['url'])
        print("url_tmp - " + url_tmp)
        last_updated_time = get_last_updated_time(url['url'])
        source_saved = get_source_by_url(url['url'])
        print("last_updated_time=" + str(last_updated_time) + " url="+url['url'])
        if last_updated_time is None or datetime.now() - last_updated_time > timedelta(hours=20) or len(source_saved) == 0:
            source = asyncio.get_event_loop().run_until_complete(get_page_source(url_tmp))
            update_page_source(url['url'], source)
        else:
            print("next")


def video_read_url():
    print(os.getcwd())
    video_url_list = []
    video_url_list_url = '../input/视频网站整理.xlsx'

    # 读取Excel文件
    df = pd.read_excel(video_url_list_url)
    # 按行读取数据R
    for index, row in df.iterrows():
        video_url_list.append(row['首页'])
        # if index > 100:
        #     break
    print("video_read_url() count = " + str(len(video_url_list)))
    print(video_url_list)
    for link in video_url_list:
        domain = extract(link).registered_domain
        document = {
            'url': domain,
            'last_crawled_at': datetime.now(),
            'source_url': "",
            'deep': 1,
        }
        collection['url_list'].update_one({'url': domain}, {'$set': document}, upsert=True)


def save_baidu_snapshot(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    params = {
        'wd': 'cache:{}'.format(url),
    }
    response = requests.get('https://www.baidu.com/s', headers=headers, params=params)

    if response.status_code == 200:
        save_dir = 'snapshot'
        os.makedirs(save_dir, exist_ok=True)

        folder_name = url.replace('/', '_').replace(':', '_')  # 以URL创建文件夹名称
        folder_path = os.path.join(save_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        save_path = os.path.join(folder_path, 'snapshot.html')
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Snapshot saved successfully at {save_path}.")
    else:
        print('Failed to save the snapshot.')


def get_wayback_machine_snapshot(url):
    api_url = f"https://archive.is/submit/{url}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        snapshot_url = data['archived_snapshots']['closest']['url']
        print(f"Snapshot URL: {snapshot_url}")
    else:
        print("Failed to fetch the snapshot.")


def init_url():
    result = collection['url_list'].delete_many({})
    print(f"Deleted {result.deleted_count} documents from url_list collection.")


def save_snapshot():
    urls = collection['url_list'].distinct('url')
    print(urls)
    print("url count: " + str(len(urls)))
    for url in urls:
        save_baidu_snapshot(url);


# 下载某个url所有的标签、文本
def download_website_text_and_links(url, isPhone=False, headless=True):
    with sync_playwright() as playwright:
        if isPhone:
            iphone = playwright.devices['iPhone 12 Pro Max']
            browser = playwright.webkit.launch(headless=headless)
            context = browser.new_context(**iphone, locale='zh-CN')
            page = context.new_page()
        else:
            browser = playwright.chromium.launch(headless=headless)
            # browser = playwright.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
        page.goto(url)
        # await page.wait_for_selector('body')
        page_text = page.inner_text('body')  # 获取页面的文本内容
        page_text = page_text.split("\n")
        unique_list = list(dict.fromkeys(page_text))

        page_links = [link.get_attribute('href') for link in page.query_selector_all('a')]  # 获取页面中所有链接的 href 属性值
        browser.close()

        internal_links = []  # 保存内链
        external_links = []  # 保存外链
        for link in page_links:
            if link.startswith('http'):  # 判断链接是否以 http 开头，即为绝对路径
                if url in link:  # 如果链接中包含基准 URL，即为内链
                    internal_links.append(link)
                else:  # 否则为外链
                    external_links.append(link)
            else:  # 如果链接不是以 http 开头，即为相对路径，也视为内链
                internal_links.append(link)

    return unique_list, internal_links, external_links


def get_link_by_url(base_url, deep):
    # download_website_text_and_links
    page_text, internal_links, external_links = download_website_text_and_links(base_url, False)
    page_text_mobile, internal_links_mobile, external_links_mobile = download_website_text_and_links(base_url, False)

    # 遍历内部链接数组
    for link in internal_links:
        # 补充为完整的URL
        url = urljoin(base_url, link)
        # 判断URL是否已存在
        if collection['urls'].find_one({'url': url}):
            print(f"URL '{url}' already exists in the database.")
        else:
            # 插入URL到数据库
            collection['urls'].insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 0})
            print(f"URL '{url}' inserted into the database.")
    # 遍历外部链接数组
    for url in external_links:
        # 判断URL是否已存在
        if collection['urls'].find_one({'url': url}):
            print(f"URL '{url}' already exists in the database.")
        else:
            # 插入URL到数据库
            collection['urls'].insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 1})
            print(f"URL '{url}' inserted into the database.")


def start_by_deep(deep):
    urls = []
    # 查询deep字段为1的数据
    query = {'deep': deep}
    cursor = collection['urls'].find(query)
    # 遍历查询结果，将url字段添加到urls数组
    for document in cursor:
        urls.append(document['url'])
    for url in urls:
        print(url)
        try:
            get_link_by_url(url, deep+1)
        except Exception as e:
            print(f"An exception occurred: {str(e)}")


def start_deep_0():
    video_url_list = []
    video_url_list_url = '../input/视频网站整理.xlsx'
    # 读取Excel文件
    df = pd.read_excel(video_url_list_url)
    # 按行读取数据R
    for index, row in df.iterrows():
        video_url_list.append(row['首页'])
    print("video_read_url() count = " + str(len(video_url_list)))
    # print(video_url_list)
    for link in video_url_list:
        domain = extract(link).registered_domain
        if len(domain) < 4:
            continue
        url_tmp = add_http_prefix(domain)
        print(url_tmp)
        if collection['urls'].find_one({'url': url_tmp}):
            print(f"URL '{url_tmp}' already exists in the database.")
        else:
            # 插入URL到数据库
            collection['urls'].insert_one({'url': url_tmp, 'from_url': '', 'deep': 0, 'kind': -1})
            print(f"URL '{url_tmp}' inserted into the database.")

    start_by_deep(0)


if __name__ == '__main__':
    # video_read_url()
    # get_url()
    # save_snapshot();

    # str = get_source_by_url("aaqqs.com")
    # str = ""
    # if len(str) == 0:
    #     # 字符串不为空
    #     print("kong")
    # else:
    #     print("x kong")
    # 图片
    # start("https://www.wydcn.com", 1)

    # start_by_deep(3)
    # get_link_by_url('https://www.wydcn.com')

    start_deep_0()






