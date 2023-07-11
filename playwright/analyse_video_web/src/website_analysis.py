import asyncio
import os
import re
import time
import uu
from urllib.parse import urljoin, urlparse

import playwright
import requests
import tldextract
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from utils.my_url_util import get_source_with_playwright_by_mobile, is_valid_url, get_page_source_with_playwright, \
    capture_long_website_screenshot, base_url, is_valid_domain, base_url_with_http, remove_quotes
from utils.my_db import db_full_dbname, db_clear_by_name
from datetime import datetime, timedelta


def db():
    return db_full_dbname('website_analysis')


def db_urls():
    return db_full_dbname('website_analysis_urls')


def db_images():
    return db_full_dbname('website_analysis_image')


def get_url_source_mobile(url):
    # 判断是否在1小时内更新的
    update_sec_count = 36000
    # 判断source_mobile长度是否大于300
    source_mobile_len = 300
    if not is_valid_url(url):
        print(f"url not valid :{url}")
        return None
    # 查询URL是否存在记录
    query = {"url": url}
    result = db().find_one(query)
    need_update = False
    if result and "source_mobile_updated_at" in result:
        updated_at = result["source_mobile_updated_at"]
        current_time = datetime.now()
        diff = current_time - updated_at

        # 判断在 update_sec_count 秒内更新的
        if diff.total_seconds() < update_sec_count:
            source_mobile = result["source_mobile"]
            print(f"get source_mobile by db url:{url} ")
            return source_mobile
    # 如果不是在1小时内更新的，则重新获取源码
    source_mobile = get_source_with_playwright_by_mobile(url)
    print(f"source_mobile:{source_mobile}")
    # 判断source_mobile长度是否大于300
    if len(source_mobile) > source_mobile_len:
        # 更新source_mobile和source_mobile_updated_at字段
        # 检查是否存在记录
        existing_record = db().find_one({'url': url})
        if existing_record:
            query = {"url": url, "type": "mobile"}
            update = {"$set": {
                "source_mobile": source_mobile,
                "source_mobile_updated_at": datetime.now()
            }}
            db().update_one(query, update)
        else:
            new_record = {
                'url': url,
                'source_mobile': source_mobile,
                'source_mobile_updated_at': datetime.now()
            }
            db().insert_one(new_record)
            print(f"URL '{url}' inserted successfully.")
    return source_mobile


def get_url_source_pc(url):
    # 判断是否在1小时内更新的
    update_sec_count = 36000
    # 判断source_pc长度是否大于300
    source_pc_len = 300
    if not is_valid_url(url):
        print(f"url not valid :{url}")
        return None
    # 查询URL是否存在记录
    query = {"url": url}
    result = db().find_one(query)
    need_update = False
    if result and "source_pc_updated_at" in result:
        updated_at = result["source_pc_updated_at"]
        current_time = datetime.now()
        diff = current_time - updated_at

        # 判断在1小时内更新的
        if diff.total_seconds() < update_sec_count:
            source_pc = result["source_pc"]
            print(f"get source_pc by db url:{url} ")
            return source_pc
    # 如果不是在1小时内更新的，则重新获取源码
    source_pc = get_page_source_with_playwright(url)
    # 判断source_pc长度是否大于300
    if len(source_pc) > source_pc_len:
        # 更新source_pc和source_pc_updated_at字段
        # 检查是否存在记录
        existing_record = db().find_one({'url': url})
        if existing_record:
            query = {"url": url}
            update = {"$set": {
                "source_pc": source_pc,
                "source_pc_updated_at": datetime.now()
            }}
            db().update_one(query, update)
        else:
            new_record = {
                'url': url,
                'source_pc': source_pc,
                'source_pc_updated_at': datetime.now()
            }
            db().insert_one(new_record)
            print(f"URL '{url}' inserted successfully.")
    return source_pc


def extract_image_urls(html_source, url):
    try:
        soup = BeautifulSoup(html_source, 'html.parser')
        base_url = base_url_with_http(url)
        a_tags_data = []

        # 情况 1
        # 提取所有图片URL
        a_tags = [img.parent for img in soup.select('a img')]
        for a_tag in a_tags:
            title = a_tag.get('title')
            href = a_tag.get('href')
            img_tag = a_tag.find('img')
            image_url = img_tag.get('src') if img_tag else None
            href = remove_quotes(href)
            image_url = remove_quotes(image_url)

            # 补充完整的 href 和 src
            if href and not href.startswith('http'):
                href = urljoin(base_url, href)
            if image_url and not image_url.startswith('http'):
                src = urljoin(base_url, image_url)
            if not title:
                print("tags ")
                print(a_tags)
                print("tag ")
                print(a_tag)
                print("nl")

            a_tags_data.append({
                'href': href,
                'image_url': image_url,
                'kind': 1,
                'title': title,
                'url': url,
                'base_url':base_url
            })

        # 情况 2
        # 提取背景图片URL
        for a_tag in soup.find_all('a', style=True):
            href = a_tag.get('href')
            style = a_tag.get('style')
            title = a_tag.get('title')
            match = re.search(r"url\((.*?)\)", style)
            if match is not None:
                image_url = match.group(1)
            image_url = remove_quotes(image_url)
            href = remove_quotes(href)

            # 补充完整的 href 和 image_url
            if href and not href.startswith('http'):
                href = urljoin(base_url, href)
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(base_url, image_url)
            if not title:
                print("nl")

            a_tags_data.append({
                'href': href,
                'image_url': image_url,
                'kind': 2,
                'title': title,
                'url': url,
                'base_url': base_url
            })

        # 情况 3
        # 获取所有带有 data-original 属性的 a 标签
        # a_tags = soup.query_selector_all('a[data-original]')
        a_tags = soup.find_all('a', attrs={'data-original': True})
        for a_tag in a_tags:
            data_original = a_tag.get('data-original')
            href = a_tag.get('href')
            title = a_tag.get('title')
            # 判断 data-original 是否为图片地址
            if data_original.endswith(('.jpg', '.jpeg', '.png', '.gif', 'webp')):
                # 判断是否为内链图片地址，补全为完整地址
                data_original = remove_quotes(data_original)
                href = remove_quotes(href)
                if data_original and not data_original.startswith('http'):
                    data_original = url + data_original
                # 判断是否为内链图片地址，补全为完整地址
                if href and not href.startswith('http'):
                    href = base_url + href
                if not title:
                    print("nl")

                a_tags_data.append({
                    'image_url': data_original,
                    'href': href,
                    'kind': 3,
                    'title': title,
                    'page_url': url,
                    'base_page_url': base_url
                })

            # 打印结果
        for data in a_tags_data:
            print(data['href'], data['image_url'], data['kind'], data['title'], base_url)
    except Exception as e:
        print(f"error {str(e)}")
    return a_tags_data


def parse_img(url):
    try:
        source = get_page_source_with_playwright(url)
        # source = get_source_with_playwright_by_mobile(url)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        return

    a_tags_data = extract_image_urls(source, url)
    base_url = base_url_with_http(url)
    current_time = datetime.now()
    for link_data in a_tags_data:
        image_url = link_data['image_url']
        href = link_data['href']
        title = link_data['title']
        kind = link_data['kind']
        updated_at = current_time

        # 查询是否已存在相同的 image_url 和 updated_at
        existing_data = db_images().find_one({
            'image_url': image_url,
            'updated_at': {'$gte': datetime.now() - timedelta(days=1)}
        })

        if existing_data:
            # 如果已存在，则跳过插入操作
            print("continue ...")
            continue

        # 保存到 MongoDB 中
        db_images().insert_one({
            'page_url': url,
            'base_page_url': base_url,
            'image_url': image_url,
            'href': href,
            'updated_at': updated_at,
            'kind': kind,
            'title': title,
            'is_download': 0,
            'download_at': None
        })


def save_screenshot(url):
    current_directory = os.getcwd()

    # 创建存储图片的目录
    image_directory = os.path.join(current_directory, 'images_screenshot')
    os.makedirs(image_directory, exist_ok=True)

    current_dir = os.getcwd()  # 获取当前目录
    parent_dir = os.path.dirname(current_dir)  # 获取上级目录
    folder_name = url.replace('/', '').replace(':', '_')  # 以URL创建文件夹名称
    save_path_pc = parent_dir + "/output/" + folder_name + "/screen_shot/pc/"
    save_path_mobile = parent_dir + "/output/" + folder_name + "/screen_shot/mobile"
    # 获取文件名
    now = datetime.now()
    formatted_time = now.strftime('%Y%m%d_')

    file_name_pc = formatted_time + url.replace('/', '_')[-30:] + "_screenshot_pc.png"
    file_name_mobile = formatted_time + url.replace('/', '_')[-30:] + "_screenshot_mobile.png"

    # 下载图片
    file_path_pc = os.path.join(save_path_pc, file_name_pc)
    file_path_mobile = os.path.join(save_path_mobile, file_name_mobile)
    # 判断文件是否存在，若存在则跳过
    if os.path.exists(file_path_pc):
        print(f"skip screen_shot file_path_pc:{file_path_pc}")
        return
    # 判断文件是否存在，若存在则跳过
    if os.path.exists(file_path_mobile):
        print(f"skip screen_shot file_path_pc:{file_path_mobile}")
        return
    asyncio.run(capture_long_website_screenshot(url, file_path_pc))
    asyncio.run(capture_long_website_screenshot(url, file_path_mobile, True))


def parse_text_and_links(url, is_mobile=False):
    if is_mobile:
        source = get_url_source_mobile(url)
    else:
        source = get_url_source_pc(url)
    # 存储图片链接和文字链接的列表
    db_links = []
    soup = BeautifulSoup(source, 'html.parser')

    # 提取图片链接信息
    img_tags = soup.find_all('img')
    for img in img_tags:
        img_url = img.get('src')  # 图片完整地址
        if img_url is None:
            continue
        if "57581" in img_url:
            print("")
        img_a_tag = img.find_parent('a', href=True)
        if img_a_tag:
            img_href = img_a_tag['href']
        else:
            img_href = None
        is_external = not img_url.startswith('/')  # 是否是外部链接
        if is_external:
            image_url_whole = ""
        else:
            image_url_whole = url + img_url
        db_links.append({
            'url': url,
            'image_url': img_url,
            'image_url_whole': image_url_whole,
            'href': img_href,
            'is_external': is_external,
            'kind': 'image',
            'is_mobile': is_mobile,
            'updated_at': datetime.now(),
        })

    # 提取文字链接信息
    a_tags = soup.find_all('a')
    filtered_a_tags = [tag for tag in a_tags if not tag.find('img')]
    for a in filtered_a_tags:
        text = a.get_text()  # 文本内容
        href = a.get('href')  # 跳转地址，可能需要补全
        if href is None:
            continue
        is_external = not href.startswith('/')  # 是否是外部链接
        db_links.append({
            'url': url,
            'text': text,
            'href': href,
            'is_external': is_external,
            'kind': 'image',
            'is_mobile': is_mobile,
            'updated_at': datetime.now()
        })

    print(f"db_links:{len(db_links)}")
    print(db_links)

    # 入库
    for link in db_links:
        url = link['url']
        href = link['href']
        kind = link['kind']

        # existing_link = db().find_one({'url': url, 'href': href})
        # if existing_link:
        #     # 如果已存在记录，则执行更新操作
        #     db().update_one({'_id': existing_link['_id']}, {'$set': link})
        #     print(f"update ok {url}")
        # else:
            # 如果不存在记录，则执行插入操作
        db_urls().insert_one(link)
        # print(f"insert ok url:{url} kind:{kind} is_external:{is_external} href:{href} ")
    return db_links


def init_dir(url):
    if is_valid_domain(url):
        print(f"url vaild: {url}")
    else:
        print(f"url not valid :{url}")
        return

    current_dir = os.getcwd()  # 获取当前目录
    parent_dir = os.path.dirname(current_dir) # 获取上级目录
    folder_name = url.replace('/', '').replace(':', '_')  # 以URL创建文件夹名称
    os.makedirs(parent_dir + "/output/" + folder_name, exist_ok=True)
    os.makedirs(parent_dir + "/output/" + folder_name + "/images/pc/", exist_ok=True)
    os.makedirs(parent_dir + "/output/" + folder_name + "/images/mobile/", exist_ok=True)
    os.makedirs(parent_dir + "/output/" + folder_name + "/screen_shot/pc/", exist_ok=True)
    os.makedirs(parent_dir + "/output/" + folder_name + "/screen_shot/mobile/", exist_ok=True)


def parse_img(url, is_mobile=False):
    if is_mobile:
        source = get_url_source_mobile(url)
    else:
        source = get_url_source_pc(url)

    a_tags_data = extract_image_urls(source, url)
    base_url = base_url_with_http(url)
    current_time = datetime.now()
    for link_data in a_tags_data:
        image_url = link_data['image_url']
        if image_url and not image_url.startswith('http'):
            image_url = base_url + image_url

        href = link_data['href']
        title = link_data['title']
        kind = link_data['kind']
        updated_at = current_time

        # 查询是否已存在相同的 image_url 和 updated_at
        existing_data = db_images().find_one({
            'image_url': image_url,
            'is_mobile': is_mobile,
            'updated_at': {'$gte': datetime.now() - timedelta(days=1)}
        })

        if existing_data:
            # 如果已存在，则跳过插入操作
            continue

        # 保存到 MongoDB 中
        db_images().insert_one({
            'page_url': url,
            'base_page_url': base_url,
            'image_url': image_url,
            'href': href,
            'updated_at': updated_at,
            'kind': kind,
            'title': title,
            'is_download': 0,
            'download_at': None,
            'is_mobile': is_mobile
        })


def download_image():
    print("Start download_image() ...")
    # TODO
    url = "https://www.wodou99.com/"

    current_dir = os.getcwd()  # 获取当前目录
    parent_dir = os.path.dirname(current_dir)  # 获取上级目录
    folder_name = url.replace('/', '').replace(':', '_')  # 以URL创建文件夹名称
    # 创建存储图片的目录
    image_directory_pc = parent_dir + "/output/" + folder_name + "/images/pc/"
    image_directory_mobile = parent_dir + "/output/" + folder_name + "/images/mobile/"

    os.makedirs(image_directory_pc, exist_ok=True)
    os.makedirs(image_directory_mobile, exist_ok=True)

    # 获取待下载的数据
    query = {'$or': [{'is_download': {'$exists': False}}, {'is_download': 0}]}
    results = db_images().find(query)

    # 遍历数据并下载图片
    for result in results:
        title = result['title'] or ""
        image_url = result['image_url']
        if not image_url or image_url is None:
            continue
        base_page_url = result['base_page_url']
        is_mobile = result['is_mobile']

        # 获取文件名
        if title:
            title_str = str(title).replace('/', '_')[-30:]
        else:
            title_str = ""

        file_name = title_str + '_' + image_url.replace('/', '_')[-30:]

        # 下载图片
        if is_mobile:
            save_dir = image_directory_mobile
        else:
            save_dir = image_directory_pc
        file_path = os.path.join(save_dir, file_name)
        # 判断文件是否存在，若存在则跳过
        if os.path.exists(file_path):
            print(f"next file_path:{file_path}")
            continue
        try:
            if not image_url.startswith('http'):
                image_url = base_page_url + image_url
            response = requests.get(image_url)
            with open(file_path, 'wb') as file:
                file.write(response.content)
        except Exception as e:
            print(f"An exception occurred: aaa {str(e)}")
            if "No such file or directory" in str(e):
                print("stop")
            continue

        # 更新数据状态为已下载
        db_images().update_one({'_id': result['_id']}, {'$set': {'is_download': 1, 'download_at': datetime.now()}})
        print(f" update image record image_url:{image_url}")


def start():
    url = "https://www.wodou99.com/"
    init_dir(url)
    save_screenshot(url)
    return

    db_clear_by_name("website_analysis_urls")
    db_clear_by_name("website_analysis_image")
    parse_text_and_links(url, is_mobile=False)
    parse_text_and_links(url, is_mobile=True)
    db_clear_by_name("website_analysis_image")
    parse_img(url, is_mobile=False)
    parse_img(url, is_mobile=True)
    download_image()


if __name__ == '__main__':
    total_start_time = time.time()  # 记录总的开始时间

    start()

    total_end_time = time.time()  # 记录总的结束时间
    total_time = total_end_time - total_start_time  # 计算总的运行时间
    print(f"Total time: {total_time:.2f} seconds")
