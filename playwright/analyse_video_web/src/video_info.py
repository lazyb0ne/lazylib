import asyncio

import numpy as np
import pandas as pd
import os
import time
import openpyxl
import json
from playwright.async_api import async_playwright
import xlwt
from datetime import datetime
from playwright.sync_api import sync_playwright


# 20230413 config
video_url_list = []
video_url_list_url = '../input/视频网站整理.xlsx'

def video_read_url():
    print(os.getcwd())
    # 读取Excel文件
    df = pd.read_excel(video_url_list_url)
    # 按行读取数据R
    for index, row in df.iterrows():
        # print(row['序号'], row['首页'], row['展示渠道'], row['恶意域名'])
        # print(row['column1'], row['column2'])
        video_url_list.append(row['首页'])
    print("video_read_url() count = " + str(len(video_url_list)))

def clearText(text):
    # 检查参数是否为空
    if not text:
        return False
    text = text.strip()
    if len(text) <= 3:
        return False
    return text

# async def video_content_by_url():
def video_content_by_url():
    # xls config
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('VideoUrlResult')
    sheet.set_panes_frozen(1)  # 冻结行数
    sheet.set_horz_split_pos(1)  # 设置水平分割位置，1表示第1行之上
    sheet.write(0, 0, 'Web - All - Kind')
    sheet.write(0, 1, 'FROM')
    sheet.write(0, 2, 'Web/Mobile')
    sheet.write(0, 3, 'Kind:text/external_url/internal_url/text_mobile/external_url_mobile/internal_url_mobile')
    sheet.write(0, 4, 'Content')
    sheet.col(0).width = 256 * 20
    sheet.col(1).width = 256 * 20
    sheet.col(3).width = 256 * 20
    sheet.col(4).width = 256 * 100
    cur_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    search_results_path = f'../output/VideoUrlResult{cur_time}.xls'
    xls_row = 1
    new_url = 1
    web_index = 1
    kind_index = 1
    toWrite = []
    for video_url in video_url_list:
        new_url = 1
        # video_url = 'http://www.nongkenfang.com' # 测试站点
        try:
            page_text, internal_links, external_links = download_website_text_and_links(video_url, False)
            page_text_mobile, internal_links_mobile, external_links_mobile = download_website_text_and_links(video_url, False)
        except:
            continue

        list_all = [page_text, internal_links, external_links, page_text_mobile, internal_links_mobile, external_links_mobile]
        list_web_mobile = ['web', 'web', 'web', 'mobile', 'mobile', 'mobile']
        list_kink = ['text', 'internal_links', 'external_links', 'text_mobi', 'internal_links_mobi', 'external_links_mobi']
        for i in range(6):
            kind_index = 0
            for item in list_all[i]:
                item = clearText(item)
                if item is False:
                    continue
                kind_index += 1
                if list_kink[i] in ['internal_links', 'internal_links_mobi']:
                    toWrite.append([web_index, video_url, list_web_mobile[i], list_kink[i], video_url + item, kind_index])
                else:
                    toWrite.append([web_index, video_url, list_web_mobile[i], list_kink[i], item, kind_index])

        if toWrite:
            for item in toWrite:
                sheet.write(xls_row, 0, str(item[0]) + " - " + str(xls_row) + " - " + str(item[5]))
                sheet.write(xls_row, 1, item[1])
                sheet.write(xls_row, 2, item[2])
                sheet.write(xls_row, 3, item[3])
                sheet.write(xls_row, 4, item[4])
                xls_row += 1
            web_index += 1

        print(f"Current Index: {web_index}")
        # if web_index > 5:
        #     break

    if search_results_path:
        workbook.save(search_results_path)

# 下载某个url所有的标签、文本
def download_website_text_and_links(url, isPhone = False, headless = True):
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

if __name__ == '__main__':
    video_read_url()
    video_content_by_url()




