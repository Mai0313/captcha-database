from playwright.sync_api import sync_playwright
from captcha_resolver import CaptchaResolver
import base64
import datetime
import os
import tqdm
import requests
import urllib


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
            if screenshot.startswith('data:image'):
                base64_screenshot = screenshot.split(',')[1]
            else:
                base_url = page.url
                full_url = urllib.parse.urljoin(base_url, screenshot)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                    "Referer": base_url
                    }
                response = requests.get(url = full_url, headers=headers)
                base64_screenshot = base64.b64encode(response.content).decode()


        # 調用解析驗證碼的函數
        captcha_code = CaptchaResolver().get_captcha_code(base64_screenshot)

        # base64 -> bytes
        if isinstance(screenshot, str):
            screenshot = base64.b64decode(base64_screenshot)

        # bytes -> image
        with open(f'{output_path}/{captcha_code}.png', 'wb') as f:
            f.write(screenshot)

        browser.close()
        return captcha_code

if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%Y%m%d")

    # # 綠界科技
    # website_name = "綠界科技"
    # website = "https://www.ecpay.com.tw/IntroTransport/Logistics_Search"
    # target_element = "img#code"
    # version = 3

    # # 台灣高鐵
    # website_name = "台灣高鐵"
    # website = "https://irs.thsrc.com.tw/IMINT/"
    # target_element = "img#BookingS1Form_homeCaptcha_passCode"
    # version = 3

    # # 7-11
    # website_name = "7-ELEVEN"
    # website = "https://auth.openpoint.com.tw/SETMemberAuth/Register.html?client_id=c2cpm&v=QAKlbK%2fWYVT%2bPprVONWnt6P8Ft9WFTfS3z3e0qLMc%2f3om1ol96bG1VvapOjSaIkG3XtClvzMBJZhJ%2bHlA%2bxLtCRh%2f78JNthYSH56stXhdR8eCNXL9c1o4azZOvksw%2beba5snZUUtAt2idVFLVZDA2Fo30MehTl0BFcVX%2bqnumNC4m0OriprWiiY7ncgRByinLZIcqoVZwzsnarKAz1Rr6fe0kAYF06d3zXxC%2fG5we8XcTYhRY7rz%2fABNGeeFKSS%2bpNBIk8zcfOrf1%2fAg1FNctD9c3VC9V8Oy5dlH7ntI8Hbqg3w2dpbaDEkNWS%2bX5%2bp4Bdb%2fegk7Ya0l8QK9ZGnKd31idRqV8%2bSYtu5e98HU9wA%3d"
    # target_element = "img#imgVerify"
    # version = 3

    # 賣貨便
    website_name = "賣貨便"
    website = "https://eservice.7-11.com.tw/e-tracking/search.aspx"
    target_element = "img#ImgVCode"
    version = 2

    output_path = f"data/{website_name}_{today}"
    os.makedirs(f"{output_path}", exist_ok=True)

    pbar = tqdm.tqdm(range(1000), desc="Processing captchas")
    n = 0
    for i in pbar:
        captcha_code = get_captcha_to_database(website, target_element, output_path, version)
        pbar.set_description(f"Processing captchas (current code: {captcha_code})")
        if n != 0 and n % 500 == 0:
            print("500 images saved, push to github first")
            cmd = "git add . && git commit -m 'update' && git push"
            os.system(cmd)
        n+=1
