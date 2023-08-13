from playwright.sync_api import sync_playwright
from captcha_resolver import CaptchaResolver
import base64
import datetime
import os
import tqdm


def get_captcha_to_database(website: str, target_element: str, output_path: str, version: int) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            java_script_enabled=True,
            accept_downloads=False,
            has_touch=False,
            is_mobile=False,
            locale='en-US',
            permissions=[],
            geolocation=None,
            color_scheme='light',
            timezone_id='Asia/Shanghai'
        )
        page = context.new_page()

        # 進入網站
        page.goto(website)

        if version == 1:
            # 直接截圖
            captcha_element = page.wait_for_selector(target_element)
            screenshot = captcha_element.screenshot()
            base64_screenshot = base64.b64encode(screenshot).decode()

        elif version == 2:
            # 找到圖片位置再截圖，跟直接截圖差不多；不穩定，但有時可用
            screenshot_element = page.query_selector(target_element)
            bounding_box = screenshot_element.bounding_box()
            screenshot = page.screenshot(clip=bounding_box)
            base64_screenshot = base64.b64encode(screenshot).decode()

        elif version == 3:
            # 直接找圖片的src
            captcha_element = page.wait_for_selector(target_element)
            screenshot = captcha_element.get_attribute('src')
            base64_screenshot = screenshot.split(',')[1]


        # 調用解析驗證碼的函數
        captcha_code = CaptchaResolver().get_captcha_code(base64_screenshot)

        # base64 -> bytes
        if isinstance(screenshot, str):
            screenshot = base64.b64decode(base64_screenshot)

        # bytes -> image
        today = datetime.datetime.now().strftime("%Y%m%d")
        output_path = f"{output_path}_{today}"
        os.makedirs(f"{output_path}", exist_ok=True)
        with open(f'{output_path}/{captcha_code}.png', 'wb') as f:
            f.write(screenshot)

        browser.close()
        return captcha_code

if __name__ == "__main__":
    website = "https://www.ecpay.com.tw/IntroTransport/Logistics_Search"
    target_element = "img#code"
    output_path = 'data/綠界科技'

    pbar = tqdm.tqdm(range(1000), desc="Processing captchas")
    n = 0
    for i in pbar:
        captcha_code = get_captcha_to_database(website, target_element, output_path, 3)
        pbar.set_description(f"Processing captchas (current code: {captcha_code})")
        if n % 500 == 0:
            print("500 images saved, push to github first")
            cmd = "git add . && git commit -m 'update' && git push"
            os.system(cmd)
        n+=1
