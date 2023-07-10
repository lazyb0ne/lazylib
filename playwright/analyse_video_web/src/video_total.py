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


def db():
    return collection['urls']

def total_info():
    count = db().count_documents({})
    print(f"Count: {count}")
    print()

    # 构建聚合管道
    pipeline = [
        {"$group": {"_id": "$deep", "count": {"$sum": 1}}}
    ]
    # 执行聚合操作
    results = db().aggregate(pipeline)
    # 遍历输出结果
    for result in results:
        deep = result['_id']
        count = result['count']
        print(f"Deep: {deep}, Count: {count}")
    print()
    # 构建聚合管道
    pipeline = [
        {"$group": {"_id": "$kind", "count": {"$sum": 1}}}
    ]
    # 执行聚合操作
    results = db().aggregate(pipeline)

    # 遍历输出结果
    for result in results:
        kind = result['_id']
        count = result['count']
        print(f"Kind: {kind}, Count: {count}")
    print("")


    # 构建查询条件
    query = {"kind": {"$in": ["out_pc", "out_mobile"]}}

    # 执行查询操作
    results = db().find(query)

    # 存储url字段的数组
    url_list = []
    url_map = {}
    url_map2 = {}

    # 遍历查询结果，将url字段存储到数组中
    for result in results:
        url = result['url']
        url_map[result['url']] = result['from_url']
        url_list.append(url)
    # 打印url数组
    print(f"out url_list = {len(url_list)}")

    # 存储域名的数组
    url_list_uniq = []

    # 遍历URL数组
    for url in url_list:
        try:
            parsed_url = urlparse(url)
            # 判断是否为正常的链接
            if parsed_url.scheme and parsed_url.netloc:
                # 提取域名
                domain = parsed_url.netloc
                url_list_uniq.append(domain)
                url_map2[domain] = url
        except Exception as e:
            # 处理异常情况
            print(f"Error processing URL '{url}': {str(e)}")
    # 去重
    url_list_uniq = list(set(url_list_uniq))
    # 打印结果
    for u in url_list_uniq:
        print(u + " - " + str(url_map2[u]))
    print(f"out url_list_uniq = {len(url_list_uniq)}")


if __name__ == '__main__':
    total_start_time = time.time()  # 记录总的开始时间
    total_info()
    total_end_time = time.time()  # 记录总的结束时间
    total_time = total_end_time - total_start_time  # 计算总的运行时间
    print(f"Total time: {total_time:.2f} seconds")