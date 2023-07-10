import asyncio
import os
import re
import time
import uu
from urllib.parse import urljoin, urlparse

import playwright
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from utils.my_url_util import get_source_with_playwright_by_mobile, is_valid_url, get_page_source_with_playwright, \
    capture_long_website_screenshot, base_url
from utils.my_db import db_full_dbname
from datetime import datetime, timedelta


def db():
    return db_full_dbname('website_analysis')


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

        # 判断在1小时内更新的
        if diff.total_seconds() < update_sec_count:
            source_mobile = result["source_mobile"]
            return source_mobile
    # 如果不是在1小时内更新的，则重新获取源码
    source_mobile = get_source_with_playwright_by_mobile(url)
    # 判断source_mobile长度是否大于300
    if len(source_mobile) > source_mobile_len:
        # 更新source_mobile和source_mobile_updated_at字段
        # 检查是否存在记录
        existing_record = db().find_one({'url': url})
        if existing_record:
            query = {"url": url}
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



# html源代码
# base_url
def extract_image_urls(html_source, url):
    try:
        soup = BeautifulSoup(html_source, 'html.parser')
        base_url = uu.base_url_with_http(url)
        a_tags_data = []

        # 情况 1
        # 提取所有图片URL
        a_tags = [img.parent for img in soup.select('a img')]
        for a_tag in a_tags:
            href = a_tag.get('href')
            img_tag = a_tag.find('img')
            title = a_tag.find('title')
            image_url = img_tag.get('src') if img_tag else None
            href = uu.remove_quotes(href)
            image_url = uu.remove_quotes(image_url)

            # 补充完整的 href 和 src
            if href and not href.startswith('http'):
                href = urljoin(base_url, href)
            if image_url and not image_url.startswith('http'):
                src = urljoin(base_url, image_url)

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
            image_url = uu.remove_quotes(image_url)
            href = uu.remove_quotes(href)

            # 补充完整的 href 和 image_url
            if href and not href.startswith('http'):
                href = urljoin(base_url, href)
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(base_url, image_url)

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
                data_original = uu.remove_quotes(data_original)
                href = uu.remove_quotes(href)
                if data_original and not data_original.startswith('http'):
                    data_original = url + data_original
                # 判断是否为内链图片地址，补全为完整地址
                if href and not href.startswith('http'):
                    href = base_url + href

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
        print("")
    return a_tags_data


def parse_img(url):
    try:
        source = uu.get_page_source_with_playwright(url)
        # source = uu.get_source_with_playwright_by_mobile(url)
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        return

    a_tags_data = extract_image_urls(source, url)
    base_url = uu.base_url_with_http(url)
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


def start(url):
    print(f"url={url}")
    count = db().count_documents({})
    print(f"count{count}")
    get_url_source_mobile(url)
    get_url_source_pc(url)


def save_screenshot(url):
    current_directory = os.getcwd()

    # 创建存储图片的目录
    image_directory = os.path.join(current_directory, 'images_screenshot')
    os.makedirs(image_directory, exist_ok=True)

    base_page_url = base_url(url)

    # 获取文件夹路径
    folder_name = urlparse(base_page_url).netloc
    folder_path = os.path.join(image_directory, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # 替换图片地址中的斜线
    # 获取文件名
    file_name_pc = url.replace('/', '_')[-30:] + "_screenshot_pc.png"
    file_name_mobile = url.replace('/', '_')[-30:] + "_screenshot_mobile.png"

    # 下载图片
    file_path_pc = os.path.join(folder_path, file_name_pc)
    file_path_mobile = os.path.join(folder_path, file_name_mobile)
    # # 判断文件是否存在，若存在则跳过
    # if os.path.exists(file_path_pc):
    #     return
    # # 判断文件是否存在，若存在则跳过
    # if os.path.exists(file_path_mobile):
    #     return
    # asyncio.run(capture_long_website_screenshot(url, file_path_pc))
    asyncio.run(capture_long_website_screenshot(url, file_path_mobile, True))


if __name__ == '__main__':
    total_start_time = time.time()  # 记录总的开始时间

    url = "https://www.wodou99.com/"
    # start(url)
    save_screenshot(url)

    total_end_time = time.time()  # 记录总的结束时间
    total_time = total_end_time - total_start_time  # 计算总的运行时间
    print(f"Total time: {total_time:.2f} seconds")
