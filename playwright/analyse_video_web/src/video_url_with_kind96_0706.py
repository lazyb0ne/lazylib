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
import time

from utils.my_url_util import get_page_source_with_playwright, get_source_with_playwright_by_mobile, \
    get_source_with_iframe, get_page_source_with_iframes
from utils.my_db import db_urls, db_urls96, db_urls_dbname
from utils.my_data import urls_96


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
def download_website_text_and_links(url, is_phone=False, headless=True):

    s = get_website_source(url)
    print(f"url={url}  s={s[:300]}")
    print(f"source = {s[:300]}")
    soup = BeautifulSoup(s, 'html.parser')

    page_text = soup.find('body')  # 获取页面的文本内容
    page_text = page_text.split("\n")
    unique_list = list(dict.fromkeys(page_text))
    # page_links = [link.get_attribute('href') for link in page.query_selector_all('a')]  # 获取页面中所有链接的 href 属性值
    links = soup.find_all('a')
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


def get_link_by_url(base_url, deep):
    page_text, internal_links, external_links, s = download_website_text_and_links(base_url, True)
    # 设置要更新的字段和值
    if s and len(s) > 100:
        update_data = {
            '$set': {
                'source_mobile': s,
                'source_updated_at': datetime.now()
            }
        }
        # 设置查询条件
        query = {'url': base_url}
        # 执行更新操作
        db().update_one(query, update_data)
    # 遍历内部链接数组
    for link in internal_links:
        # 补充为完整的URL
        url = urljoin(base_url, link)
        # 判断URL是否已存在
        if db().find_one({'url': url,'kind': 'in_pc'}):
            print(f"URL '{deep} {url}' already exists in the database.")
        else:
            # 插入URL到数据库
            db().insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 'in_pc'})
            print(f"URL '{deep} {url}' inserted into the database.")
    # 遍历外部链接数组
    for url in external_links:
        # 判断URL是否已存在
        if db().find_one({'url': url, 'kind': 'in_pc'}):
            print(f"URL '{deep} {url}' already exists in the database.")
        else:
            # 插入URL到数据库
            db().insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 'out_pc'})
            print(f"URL '{deep} {url}' inserted into the database.")

    page_text_mobile, internal_links_mobile, external_links_mobile, s = download_website_text_and_links(base_url, False)
    # 设置要更新的字段和值
    if s and len(s) > 100:
        update_data = {
            '$set': {
                'source_pc': s,
                'source_updated_at': datetime.now()
            }
        }
        # 设置查询条件
        query = {'url': base_url}
        # 执行更新操作
        db().update_one(query, update_data)

    # 遍历内部链接数组
    for link in internal_links_mobile:
        # 补充为完整的URL
        url = urljoin(base_url, link)
        # 判断URL是否已存在
        if db().find_one({'url': url, 'kind': 'in_mobile'}):
            print(f"URL '{deep} {url}' already exists in the database.")
        else:
            # 插入URL到数据库
            db().insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 'in_mobile'})
            print(f"URL '{deep} {url}' inserted into the database.")
    # 遍历外部链接数组
    for url in external_links_mobile:
        # 判断URL是否已存在
        if db().find_one({'url': url, 'kind': 'in_mobile'}):
            print(f"URL '{deep} {url}' already exists in the database.")
        else:
            # 插入URL到数据库
            db().insert_one({'url': url, 'from_url': base_url, 'deep': deep, 'kind': 'out_mobile'})
            print(f"URL '{deep} {url}' inserted into the database.")


def start_by_deep(deep):
    urls = []
    # 根据deep字段查询数据
    query = {'deep': deep}
    cursor = db().find(query)
    # 遍历查询结果，将url字段添加到urls数组
    for document in cursor:
        urls.append(document['url'])
    for url in urls:
        # 获取当前时间
        current_time = datetime.now()
        # 计算 1 小时前的时间
        one_hour_ago = current_time - timedelta(hours=12)
        # 构建查询条件
        query = {
            'url': url,
            '$or': [
                {'updated_at': None},
                {'source_mobile': None},
                {'updated_at': {'$lt': one_hour_ago}}
            ]
        }
        # 执行查询
        results = db().find(query)
        # 遍历结果并打印 URL
        results_list = list(results)
        if len(results_list) > 0:
            get_link_by_url(url, deep + 1)
            # ---------------------------------------
            # try:
            #     get_link_by_url(url, deep + 1)
            # except Exception as e:
            #     print(f"An exception occurred: {str(e)}")
            # # 构建更新操作
            # update = {'$set': {'updated_at': current_time}}
            # # 执行更新操作
            # try:
            #     db().update_many(query, update)
            # except Exception as e:
            #     time.sleep(10);
            #     try:
            #         db().update_many(query, update)
            #     except Exception as e:
            #         print(f"Error occurred: {str(e)}")
            # ---------------------------------------


def start_deep_start(deep):
    count = db().count_documents({})
    print(f"count{count}")
    if count == 0:
        video_url_list = urls_96();
        print("video_read_url() count = " + str(len(video_url_list)))
        for link in video_url_list:
            domain = extract(link).registered_domain
            if len(domain) < 4:
                continue
            url_tmp = add_http_prefix(domain)
            print(url_tmp)
            if db().find_one({'url': url_tmp}):
                print(f"URL 0' {url_tmp}' already exists in the database.")
            else:
                # 插入URL到数据库
                db().insert_one({'url': url_tmp, 'from_url': '', 'deep': 0, 'kind': 'init'})
                print(f"URL 0' {url_tmp}' inserted into the database.")
    else:
        for i in range(deep) if deep != 0 else [0]:
            print("----------------")
            iteration_start_time = time.time()
            start_by_deep(i)
            iteration_end_time = time.time()  # 记录每次迭代的结束时间
            iteration_time = iteration_end_time - iteration_start_time  # 计算每次迭代的运行时间
            print(f"Iteration {i + 1} time: {iteration_time:.2f} seconds")


def check_diff_in_pc_mobile():
    # 使用聚合管道更新数据
    pipeline = [
        {
            '$addFields': {
                'diff': {
                    '$cond': {
                        'if': {'$eq': [{'$ifNull': ['$source_mobile', '']}, {'$ifNull': ['$source_pc', '']}]},
                        'then': 'same',
                        'else': 'diff'
                    }
                },
                'diff_size': {
                    '$cond': {
                        'if': {'$eq': [{'$ifNull': ['$source_mobile', '']}, {'$ifNull': ['$source_pc', '']}]},
                        'then': 0,
                        'else': {'$subtract': [{'$strLenCP': {'$ifNull': ['$source_pc', '']}},
                                               {'$strLenCP': {'$ifNull': ['$source_mobile', '']}}]}
                    }
                },
                'diff_count': {
                    '$cond': {
                        'if': {'$eq': [{'$ifNull': ['$source_mobile', '']}, {'$ifNull': ['$source_pc', '']}]},
                        'then': -1,
                        'else': {
                            '$cond': {
                                'if': {'$eq': [{'$strLenCP': {'$ifNull': ['$source_pc', '']}}, 0]},
                                'then': -1,
                                'else': {
                                    '$multiply': [
                                        {
                                            '$trunc': {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            {
                                                                '$subtract': [
                                                                    {'$strLenCP': {'$ifNull': ['$source_pc', '']}},
                                                                    {'$strLenCP': {'$ifNull': ['$source_mobile', '']}}
                                                                ]
                                                            },
                                                            {'$strLenCP': {'$ifNull': ['$source_pc', '']}}
                                                        ]
                                                    },
                                                    100  # 保留四位小数，乘以10000
                                                ]
                                            }
                                        },
                                        1  # 将结果除以1，恢复小数位
                                    ]
                                }
                            }
                        }
                    }
                },
                'source_pc_size': {'$strLenCP': {'$ifNull': ['$source_pc', '0']}},
                'source_mobile_size': {'$strLenCP': {'$ifNull': ['$source_mobile', '0']}}
            }
        },
        {
            '$out': 'urls'  # 将更新结果保存回 urls 表中
        }
    ]

    # 执行聚合操作
    db().aggregate(pipeline)
    print('Database update complete.')


def db():
    return db_urls_dbname('0706')


def get_website_source(url):
    # try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve website source. Status code: {response.status_code}")
    # except requests.RequestException as e:
    #     print(f"An error occurred: {str(e)}")
    #     return str(e)


def test():
    print("test")
    try:
        # 查询条件：status不等于ok
        query = {'status': {'$ne': 'ok'}}
        # 查询并获取url字段
        result = db().find(query, {'url': 1})

        # 将url字段组成一个数组
        urls = [data['url'] for data in result]
        # if not urls:
        #     urls = urls_96()
    except Exception as e:
        print(e)
        urls = urls_96()
    count = len(urls)
    for index, url in enumerate(urls):
        print(f"Index:{index} / {count}")
        source = get_website_source(url)
        if source and len(source) > 400:
            status = 'ok'
        else:
            status = 'error'
            print(f"{url} XXX")
            emsg = source
            source = None

        # 查询条件：url等于给定的URL
        query = {'url': url}
        # 更新操作时的更新内容
        update = {
            '$set': {
                'updated_at': datetime.now(),
                'updated_at': datetime.now(),
                'source': source,
                'status': status
            }
        }
        # 检查URL是否存在
        existing_url = db().find_one(query)

        if existing_url:
            # URL存在，执行更新操作
            db().update_one(query, update)
            print(f"URL '{url}' updated.")
        else:
            # URL不存在，执行插入操作
            new_url_data = {
                'url': url,
                'updated_at': datetime.now(),
                'source': source,
                'status': status,
                'error_msg': emsg
            }
            db().insert_one(new_url_data)
        print(f"insert {status}")


def update_title_field():
    # 查询条件：source字段不为空
    query = {"source": {"$exists": True, "$ne": ""}}

    # 获取符合条件的记录
    results = db().find(query)

    for result in results:
        source = result["source"]
        if source:
            soup = BeautifulSoup(source, 'html.parser')
            title_tag = soup.find("title")
            title = title_tag.text if title_tag else ""
        else:
            title = ""

        # 更新title字段
        db().update_one({"_id": result["_id"]}, {"$set": {"title": title}})
        print(f"Updated title for URL: {result['url']}")


def test():
    url = "https://4kyk.com/"
    # url = "https://semiao44.xyz/app.php?sogou"
    # s = get_website_source(url)
    # s = get_source_with_playwright_by_mobile(url)
    main_page_source, iframe_sources, iframe_contents = get_source_with_iframe(url)
    # 查询数据库中是否存在该URL的记录
    query = {"url": url}
    existing_record = db().find_one(query)

    # 构造要更新或插入的数据
    data = {
        "main_page_source": main_page_source,
        "iframe_sources": iframe_sources,
        "iframe_contents": iframe_contents,
        "updated_at": datetime.now()
    }

    # 如果存在记录，则更新数据
    if existing_record:
        db().update_one(query, {"$set": data})
    else:
        # 否则，插入新数据
        data["url"] = url
        db().insert_one(data)


def get_iframe_url(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()

        try:
            page = context.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_load_state()

            page_source = page.content()

            iframe_elements = page.query_selector_all('iframe')
            iframe_src_list = []
            for iframe_element in iframe_elements:
                iframe_src = iframe_element.get_attribute('src')
                if iframe_src:
                    iframe_src_list.append(iframe_src)

            return page_source, iframe_src_list

        except Exception as e:
            print(f"Error occurred: {str(e)}")

        finally:
            context.close()
            browser.close()


def update_urls_for_iframes(url, page_source, iframe_src_list):
    # 构造要更新的数据
    data = {
        "page_source": page_source,
        "iframe_src_list": iframe_src_list,
        "updated_at": datetime.now()
    }
    deep = 0

    # 根据URL更新数据
    db().update_one({"url": url}, {"$set": data}, upsert=True)
    for iframe_src in iframe_src_list:
        data = {
            "url": iframe_src,
            "kind": "iframe",
            "from_url": url,
            "deep": deep+1,
            "status": "",  # 根据原逻辑设置具体的状态
            "title": "",  # 根据原逻辑设置具体的标题
            "source": ""  # 根据原逻辑设置具体的源码
        }
        db().update_one({"url": iframe_src}, {"$set": data}, upsert=True)


def test2():
    # 使用示例
    # url = "https://4kyk.com/"
    url = "https://semiao44.xyz/app.php?sogou"
    page_source, iframe_src_list = get_page_source_with_iframes(url)
    if page_source:
        print("网页源码：", page_source)
        print("iframe的src地址：", iframe_src_list)

        update_urls_for_iframes(url, page_source, iframe_src_list)

    else:
        print("获取网页源码失败")


def do_start():
    print('start')


if __name__ == '__main__':
    total_start_time = time.time()  # 记录总的开始时间

    start_deep_start(0)
    # check_diff_in_pc_mobile()
    # update_title_field()

    test2();

    total_end_time = time.time()  # 记录总的结束时间
    total_time = total_end_time - total_start_time  # 计算总的运行时间
    print(f"Total time: {total_time:.2f} seconds")