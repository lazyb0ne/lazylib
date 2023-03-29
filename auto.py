from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.ss-gate.org/42933.html")
    page.get_by_text("将本站设为首页 | 收藏本站 书书阁楼 搜 索 首页玄幻武侠都市历史网游科幻女生同人 书书阁楼 > 玄幻奇幻 > 男生带我去他家 男生带我去他家 作者：大学女生").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
