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
word_list_url = '/Users/lazybone/git-wh/lazylib/playwright/input/word_list_test.xlsx'
word_list = []

def read_searchkey_from_excel():
    print(os.getcwd())
    # 读取Excel文件
    df = pd.read_excel(word_list_url)
    # 按行读取数据R
    for index, row in df.iterrows():
        # print(row['column1'], row['column2'], row['column3'])
        # print(row['column1'], row['column2'])
        word_list.append(row['column2'])
    # print(word_list)


# 百度搜索
async def do_baidu_search( keyword, maxPageNum=1):
    # config
    xls_row = 1
    pageNum = 1
    sleep_time_per_page = 1
    return_result = []

    async with async_playwright() as pw:
        # browser = await pw.chromium.launch(headless=False)
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://baidu.com/')
        await page.fill('input[name="wd"]', keyword )
        await page.press('input[name="wd"]', 'Enter')
        while pageNum <= maxPageNum:
            print(f'pageNum={pageNum}')
            await page.wait_for_selector('#content_left')
            search_results_el = await page.query_selector_all('#content_left .result')
            for result in search_results_el:
                title_el = await result.query_selector('div>h3>a')
                title = await title_el.text_content()
                link_el = await result.query_selector('.t a')
                link = await link_el.get_attribute('href')
                print(f'total={xls_row} maxPageNum={maxPageNum} cur_page={pageNum}  Title: {title} Link: {link}')
                # .append({ title: title, link: link})

                # xls_row, pageNum, keyword, title, link
                return_result.append([pageNum, keyword, title, link])

            # 点击下一页
            await page.wait_for_selector('#page .n:last-child', state='visible')
            next_btn = await page.query_selector('#page .n:last-child')
            if next_btn:
                time.sleep(sleep_time_per_page)
                try:
                    await next_btn.click()
                except Exception as e:
                    print(e)
            else:
                time.sleep(sleep_time_per_page)
                print('最后一页')
            pageNum += 1

        # 输出所有
        print(f"total={xls_row} maxPageNum={maxPageNum} ")
        # 保存 xls 文件
        await browser.close()
        return return_result

# sougou 搜索
async def do_sougou_search( keyword, maxPageNum=1):
    # config
    xls_row = 1
    pageNum = 1
    sleep_time_per_page = 1
    return_result = []

    async with async_playwright() as pw:
        # browser = await pw.chromium.launch(headless=False)
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://baidu.com/')
        await page.fill('input[name="wd"]', keyword )
        await page.press('input[name="wd"]', 'Enter')
        while pageNum <= maxPageNum:
            print(f'pageNum={pageNum}')
            await page.wait_for_selector('#content_left')
            search_results_el = await page.query_selector_all('#content_left .result')
            for result in search_results_el:
                title_el = await result.query_selector('div>h3>a')
                title = await title_el.text_content()
                link_el = await result.query_selector('.t a')
                link = await link_el.get_attribute('href')
                print(f'total={xls_row} maxPageNum={maxPageNum} cur_page={pageNum}  Title: {title} Link: {link}')
                # .append({ title: title, link: link})

                # xls_row, pageNum, keyword, title, link
                return_result.append([pageNum, keyword, title, link])

            # 点击下一页
            await page.wait_for_selector('#page .n:last-child', state='visible')
            next_btn = await page.query_selector('#page .n:last-child')
            if next_btn:
                time.sleep(sleep_time_per_page)
                try:
                    await next_btn.click()
                except Exception as e:
                    print(e)
            else:
                time.sleep(sleep_time_per_page)
                print('最后一页')
            pageNum += 1

        # 输出所有
        print(f"total={xls_row} maxPageNum={maxPageNum} ")
        # 保存 xls 文件
        await browser.close()
        return return_result

async def scrape_sogou_results(query):
    async with async_playwright() as p:
        # 设置无头浏览器
        browser = await p.chromium.launch(headless=True)
        # browser = await p.chromium.launch()
        # 创建新的页面
        page = await browser.new_page()
        # 访问搜狗搜索首页
        await page.goto(f'https://www.sogou.com/web?query={query}')
        # 等待搜索结果加载完成
        await page.wait_for_selector('#main')
        # 收集第一页的搜索结果
        results = await page.eval_on_selector_all(
            '#main .vrwrap',
            'nodes => nodes.map(n => ({ title: n.querySelector(".vrTitle a").textContent, url: n.querySelector(".vrTitle a").href }))'
        )
        # 打印第一页的搜索结果
        print(f'Page 1 results:')
        for result in results:
            print(f'Title: {result["title"]}')
            print(f'URL: {result["url"]}')
        # 获取总页数
        total_pages = await page.eval('Number(document.querySelector(".p.f13 > span").textContent.match(/\\d+/)[0])')
        # 翻页并收集搜索结果
        for page_num in range(2, total_pages+1):
            # 点击下一页按钮
            await page.click(f'.p.f13 > a:nth-child({page_num})')
            # 等待搜索结果加载完成
            await page.wait_for_selector('#main')
            # 收集当前页的搜索结果
            results = await page.eval_on_selector_all(
                '#main .vrwrap',
                'nodes => nodes.map(n => ({ title: n.querySelector(".vrTitle a").textContent, url: n.querySelector(".vrTitle a").href }))'
            )
            # 打印当前页的搜索结果
            print(f'Page {page_num} results:')
            for result in results:
                print(f'Title: {result["title"]}')
                print(f'URL: {result["url"]}')
        # 关闭浏览器
        await browser.close()

# 按关键字搜索
async def search_by_key():
    # xls config
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('BaiduSearchResult')
    sheet.write(0, 0, 'ID')
    sheet.write(0, 1, 'FROM')
    sheet.write(0, 2, 'PAGE')
    sheet.write(0, 3, 'SEAECH_KEY')
    sheet.write(0, 4, 'TITLE')
    sheet.write(0, 5, 'URL')
    cur_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    search_results_path = f'../target/search_results_{cur_time}.xls'
    xls_row = 1
    for item in word_list:
        return_result = await do_baidu_search(item, maxPageNum=3)
        if return_result:
            print(return_result)
            for item in return_result:
                sheet.write(xls_row, 0, xls_row)
                sheet.write(xls_row, 1, 'Baidu')
                for idx in range(len(item)):
                    sheet.write(xls_row, idx+2, item[idx])
                xls_row += 1
    if search_results_path:
        workbook.save(search_results_path)


if __name__ == '__main__':
    # read_searchkey_from_excel()
    # asyncio.run(search_by_key())

    asyncio.run(scrape_sogou_results('小说'))
