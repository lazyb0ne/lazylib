import datetime
import shutil

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

from pymongo import collection
import re
import time
import tldextract
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pymongo import MongoClient

from utils.my_data import urls_96
from utils.my_db import db_images
from utils.my_db import db_images_clear
import utils.my_url_util as uu
from datetime import datetime, timedelta

def download_images(url, base_url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html = response.text
            image_urls = extract_image_urls(html, base_url)

            for image_url in image_urls:
                save_image(image_url, base_url)

                # 判断是否是当前网站下的图片地址
                is_internal = is_internal_url(image_url, base_url)

                # 将图片信息保存到MongoDB表
                # save_image_info(url, image_url, is_internal, True)
        else:
            print(f"Failed to download page from URL: {url}")
    except Exception as e:
        print(f"An exception occurred: {str(e)}")


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


def extract_background_image_url(style_value):
    # 提取背景图片URL的逻辑
    # 你可以使用正则表达式或其他方法来提取URL
    # 使用正则表达式提取URL
    pattern = r'url\(["\']?(.*?)["\']?\)'
    match = re.search(pattern, style_value)
    if match:
        return match.group(1)
    else:
        return None


def save_image(url, base_url):
    response = requests.get(url, stream=True)

    images_dir = os.path.join(os.getcwd(), 'images', urlparse(url).netloc)
    os.makedirs(images_dir, exist_ok=True)

    if response.status_code == 200:
        # 提取文件名
        filename = os.path.basename(url)

        # 判断文件夹是否存在，不存在则创建
        image_dir = os.path.join("url", base_url)
        os.makedirs(image_dir, exist_ok=True)

        # 保存图片文件
        filepath = os.path.join(image_dir, filename)
        with open(filepath, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

        print(f"Image downloaded: {filepath}")
    else:
        print(f"Failed to download image from URL: {url}")


def is_internal_url(url, base_url):
    # 判断URL是否是当前网站下的图片地址
    return url.startswith(base_url)


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


def download_image():
    print("Start download_image() ...")
    # 获取当前目录
    current_directory = os.getcwd()
    current_time = datetime.now()

    # 创建存储图片的目录
    image_directory = os.path.join(current_directory, 'images')
    os.makedirs(image_directory, exist_ok=True)

    # 获取待下载的数据
    query = {'$or': [{'is_download': {'$exists': False}}, {'is_download': 0}]}
    results = db_images().find(query)

    # 遍历数据并下载图片
    for result in results:
        title = result['title']
        image_url = result['image_url']
        base_page_url = result['base_page_url']

        # 获取文件夹路径
        folder_name = urlparse(base_page_url).netloc
        folder_path = os.path.join(image_directory, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # 替换图片地址中的斜线
        # 获取文件名
        file_name = str(title).replace('/', '_')[-30:] + '_' + image_url.replace('/', '_')[-30:]

        # 下载图片
        file_path = os.path.join(folder_path, file_name)
        # 判断文件是否存在，若存在则跳过
        if os.path.exists(file_path):
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
        db_images().update_one({'_id': result['_id']}, {'$set': {'is_download': 1, 'download_at': current_time}})


def start():
    print("start")
    for index, url in enumerate(urls_96()):
        print(f"{url}")
        parse_img(url)


# 后台上传，还是静态的
def check_img_is_local():
    # 查询所有数据
    data = db_images().find()

    # 更新数据
    for item in data:
        image_url = item['image_url']
        page_url = item['page_url']
        parsed_image_url = urlparse(image_url)
        parsed_page_url = urlparse(page_url)

        is_img_local = parsed_image_url.netloc in parsed_page_url.netloc

        db_images().update_one(
            {'_id': item['_id']},
            {'$set': {'is_img_local': is_img_local}}
        )

    print('数据更新完成')


if __name__ == '__main__':
    total_start_time = time.time()  # 记录总的开始时间

    # url = "https://www.cmvvd.com/"  # 替换为你要下载图片的网页URL
    # url = "https://www.lovedan.net/"
    # url = "https://www.lovedan.net/voddetail/80.html"
    # # db_images_clear()
    # url = "https://4kyk.com/"


    # urls = urls_96()
    # for index, url in enumerate(urls):
    #     try:
    #         print(f"start img:{index}")
    #         parse_img(url)
    #     except Exception as e:
    #         print(f"parse_img e:{str(e)}")

    url = "https://www.wodou99.com/"
    parse_img(url)
    download_image()

    # check_img_is_local()
    # start()

    total_end_time = time.time()  # 记录总的结束时间
    total_time = total_end_time - total_start_time  # 计算总的运行时间
    print(f"Total time: {total_time:.2f} seconds")






