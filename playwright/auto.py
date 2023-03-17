from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.ss-gate.org/42933.html")
    page.get_by_role("link", name="第1章 女朋友为啥睡过后很粘人").click()
    page.locator("div").filter(has_text="书书阁楼 搜 索").first.click()
    page.get_by_role("definition").filter(has_text="第10章 掐奶头一女多男玩弄折磨").click()
    page.get_by_text("书书阁楼 > 历史军事 > 掐奶头一女多男玩弄折磨").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
