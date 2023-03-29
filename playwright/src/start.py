import asyncio

import pandas as pd
import os
import time
import openpyxl
import json
from playwright.async_api import async_playwright
import xlwt
from datetime import datetime

# config
word_list_url = '/Users/lazybone/git-wh/lazylib/playwright/input/word_list.xlsx'
word_list = []

search_result = {}


def read_url_from_excel():
    print(os.getcwd())
    # 读取Excel文件
    df = pd.read_excel(word_list_url)
    # 按行读取数据R
    for index, row in df.iterrows():
        # print(row['column1'], row['column2'], row['column3'])
        print(row['column1'], row['column2'])
        word_list.append(row['column2'])
    print(word_list)


async def get_baidu_search():
    # xls config
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('BaiduSearchResult')
    sheet.write(0, 0, 'ID')
    sheet.write(0, 1, 'BAIDU_PAGE')
    sheet.write(0, 2, 'TITLE')
    sheet.write(0, 3, 'URL')
    # config
    xls_row = 1
    pageNum = 1
    maxPageNum = 1
    cur_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    search_results_path = f'../target/search_results_{cur_time}.xls'

    async with async_playwright() as pw:
        # browser = await pw.chromium.launch(headless=False)
        browser = await pw.chromium.launch()
        page = await browser.new_page()

        await page.goto('http://baidu.com/')
        await page.fill('input[name="wd"]', 'playwright')
        await page.press('input[name="wd"]', 'Enter')


        while pageNum <= maxPageNum:
            print(f'pageNum={pageNum}')
            page_data = []
            await page.wait_for_selector('#content_left')

            search_results_el = await page.query_selector_all('#content_left .result')
            for result in search_results_el:
                title_el = await result.query_selector('div>h3>a')
                title = await title_el.text_content()
                link_el = await result.query_selector('.t a')
                link = await link_el.get_attribute('href')
                print(f'total={xls_row} maxPageNum={maxPageNum} cur_page={pageNum}  Title: {title} Link: {link}')
                page_data.append({ title: title, link: link})
                search_result[pageNum] = page_data
                #write to xls
                sheet.write(xls_row, 0, xls_row)
                sheet.write(xls_row, 1, pageNum)
                sheet.write(xls_row, 2, title)
                sheet.write(xls_row, 3, link)
                xls_row += 1

            # 点击下一页
            next_btn = await page.query_selector('#page .n:last-child')
            if next_btn:
                await next_btn.click()
            else:
                time.sleep(5)
                print('最后一页')
            pageNum += 1

        # 输出所有
        print(f"total={xls_row} maxPageNum={maxPageNum} ")
        # 保存 xls 文件
        workbook.save(search_results_path)
        await browser.close()

if __name__ == '__main__':
    # read_url_from_excel()
    asyncio.run(get_baidu_search())
    # asyncio.run(open_iphone())
