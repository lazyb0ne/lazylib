import asyncio
import time
from urllib.parse import urlparse, urlunparse

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from tldextract import tldextract


def test():
    print("OK")


# 去掉字符串两边的引号
def remove_quotes(string):
    try:
        if string.startswith("'") and string.endswith("'"):
            return string[1:-1]
        elif string.startswith('"') and string.endswith('"'):
            return string[1:-1]
        else:
            return string
    except Exception as e:
        return string


# 获取url的主域名
def base_url(url):
    return tldextract.extract(url).registered_domain


def base_url_with_http(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        # 如果URL中没有协议或主机名，则默认为http://
        parsed_url = parsed_url._replace(scheme='http', netloc=url)
    protocol_host = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return protocol_host


def get_page_source_with_playwright(url):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state('networkidle')
            page_content = page.content()
            browser.close()
        return page_content
    except Exception as e:
        try:
            time.sleep(10);
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto(url)
                page.wait_for_load_state('networkidle')
                page_content = page.content()
                browser.close()
            return page_content
        except Exception as e:
            return None;


def get_source_with_playwright_by_mobile(url):
    # try:
    with sync_playwright() as playwright:
        iphone_12 = playwright.devices['iPhone 12']
        # browser = playwright.webkit.launch(headless=False)
        browser = playwright.webkit.launch(headless=False)
        context = browser.new_context(**iphone_12, locale='zh-CN')
        page = context.new_page()
        page.goto(url)
        # 滚动到页面底部，加载所有内容
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        # 滚动到页面顶部，加载中间内容
        page.evaluate('window.scrollTo(0, 0)')
        # 逐步滚动到页面底部，等待加载中间内容
        while True:
            page.evaluate('window.scrollBy(0, 200)')
            time.sleep(1)  # 等待加载
            if page.evaluate(
                    'document.documentElement.scrollHeight - window.innerHeight <= window.pageYOffset'):
                break

        page.wait_for_load_state('networkidle')
        time.sleep(3)
        page_source = page.content()
        # page.close()
        # context.close()
        print(page_source)
        print("get_source_with_playwright_by_mobile_nb")
        browser.close()
        return page_source
    # except Exception as e:
    #     print(f"Error occurred: {str(e)}")
    #     return None


def get_source_with_iframe(url, by_phone=True, headless=False):
    with sync_playwright() as playwright:
        if by_phone:
            iphone_12 = playwright.devices['iPhone 12']
            browser = playwright.webkit.launch(headless=headless)
            context = browser.new_context(**iphone_12)
        else:
            browser = playwright.chromium.launch()
            context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        # page.wait_for_load_state()

        # 获取主页面的源码
        main_page_source = page.content()

        # 获取所有的iframe元素
        iframe_elements = page.query_selector_all('iframe')
        print("--------")
        print(iframe_elements)


        iframe_sources = []
        for iframe_element in iframe_elements:
            # 获取每个iframe元素的src属性值
            iframe_src = iframe_element.get_attribute('src')
            iframe_sources.append(iframe_src)

        # 获取每个iframe的源码
        iframe_contents = []
        for iframe_src in iframe_sources:
            if iframe_src:
                iframe_page = context.new_page()
                iframe_page.goto(iframe_src)
                # iframe_page.wait_for_load_state()
                iframe_content = iframe_page.content()
                iframe_contents.append(iframe_content)
                iframe_page.close()

        page.close()
        context.close()
        browser.close()

        print("iframe_sources")
        print(iframe_sources)

        print("iframe_contents")
        print(iframe_contents)

        return main_page_source, iframe_sources, iframe_contents


def get_page_source_with_iframes(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(**playwright.devices["iPhone 12"])

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
            return None,None

        finally:
            context.close()
            browser.close()


def is_valid_url(url):
    # # 使用示例
    # url1 = 'https://www.example.com'
    # url2 = 'www.example.com'
    # url3 = 'example.com'
    # url4 = 'https://'
    #
    # print(is_valid_url(url1))  # 输出: True
    # print(is_valid_url(url2))  # 输出: False
    # print(is_valid_url(url3))  # 输出: False
    # print(is_valid_url(url4))  # 输出: False
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])


def is_valid_domain(url):
    ext = tldextract.extract(url)
    return all([ext.domain, ext.suffix])


async def capture_long_website_screenshot(url, output_path, by_phone=False):
    async with async_playwright() as playwright:
        if by_phone:
            iphone_12 = playwright.devices['iPhone 12']
            browser = await playwright.webkit.launch(headless=False)
            context = await browser.new_context(**iphone_12, locale='zh-CN')
        else:
            browser = await playwright.chromium.launch()
            context = await browser.new_context(locale='zh-CN')

        page = await context.new_page()
        await page.goto(url)
        # 滚动到页面底部，加载所有内容
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

        # 滚动到页面顶部，加载中间内容
        await page.evaluate('window.scrollTo(0, 0)')

        # 逐步滚动到页面底部，等待加载中间内容
        while True:
            await page.evaluate('window.scrollBy(0, 200)')
            if await page.evaluate('document.documentElement.scrollHeight - window.innerHeight <= window.pageYOffset'):
                break

        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')

        await page.screenshot(path=output_path, full_page=True)
        await browser.close()
        print(f"screenshot saved ok {url}")


def get_source_with_playwright_by_mobile_nb(url):
    with sync_playwright() as playwright:
        iphone_12 = playwright.devices['iPhone 12']
        browser = playwright.webkit.launch(headless=True)
        # browser = playwright.webkit.launch(headless=False,
        #                                    args=["--start-maximized"],
        #                                    ignore_default_args=["--disable-extensions"],
        #                                    )
        context = browser.new_context(**iphone_12, locale='zh-CN')
        page = context.new_page()
        page.goto(url)

        page.wait_for_load_state('networkidle')
        time.sleep(5)

        # 查找第一个包含img标签的a标签
        img_a_tag = page.query_selector('a:has(img)')

        if img_a_tag:
            # 点击第一个包含img标签的a标签
            img_a_tag.click()
            # 等待一段时间
            time.sleep(5)
            # 浏览器回退
            page.evaluate('history.back()')
            page.wait_for_load_state('networkidle')
            time.sleep(5)

            # 逐步滚动到页面底部，等待加载中间内容
            while True:
                page.evaluate('window.scrollBy(0, 200)')
                time.sleep(1)  # 等待加载
                if page.evaluate(
                        'document.documentElement.scrollHeight - window.innerHeight <= window.pageYOffset'):
                    break

            page_source = page.content()
            print(page_source)
            # 等待用户输入
            # input("请在浏览器中进行操作，完成后按Enter键继续...")

        browser.close()
        return page_source


def get_source_with_playwright_by_pc_nb(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        # browser = playwright.webkit.launch(headless=False)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        # 查找第一个包含img标签的a标签
        img_a_tag = page.query_selector('a:has(img)')
        if img_a_tag:
            print(img_a_tag)
            # 点击第一个包含img标签的a标签
            img_a_tag.click()
            # 等待一段时间
            time.sleep(3)
            # 浏览器回退
            page.evaluate('history.back()')
            page.wait_for_load_state('networkidle')
            time.sleep(3)
            page.evaluate('history.forward()')
            page.wait_for_load_state('networkidle')
            time.sleep(3)

            # 逐步滚动到页面底部，等待加载中间内容
            while True:
                page.evaluate('window.scrollBy(0, 200)')
                asyncio.sleep(1)  # 等待加载
                if page.evaluate(
                        'document.documentElement.scrollHeight - window.innerHeight <= window.pageYOffset'):
                    break

            page_source = page.content()
            print(page_source)
            print("get_source_with_playwright_by_pc_nb")
            # 等待用户输入
            # input("请在浏览器中进行操作，完成后按Enter键继续...")

        browser.close()
        return page_source
