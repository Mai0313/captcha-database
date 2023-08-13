from playwright.sync_api import sync_playwright
from captcha_resolver import CaptchaResolver
import base64
import datetime
import os
import tqdm
import requests
import urllib
from omegaconf import OmegaConf
import subprocess

def save_image(output_path, captcha_code, screenshot: bytes):
    with open(f'{output_path}/{captcha_code}.png', 'wb') as f:
        f.write(screenshot)

def get_captcha_to_database(website: str, target_element: str, output_path: str, version: int, length: int, type: list) -> str:
    print(type)
    if not target_element:
        # 除非可以用網址直接打開圖片，不然不建議用這個版本
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}
        full_url = website
        response = requests.get(url = full_url, headers=headers)
        base64_screenshot = base64.b64encode(response.content).decode("utf-8")
    else:
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
                base64_screenshot = base64.b64encode(screenshot).decode("utf-8")

            elif version == 2:
                # 找到圖片位置再截圖，跟直接截圖差不多；不穩定，但有時可用
                screenshot_element = page.query_selector(target_element)
                bounding_box = screenshot_element.bounding_box()
                screenshot = page.screenshot(clip=bounding_box)
                base64_screenshot = base64.b64encode(screenshot).decode("utf-8")

            elif version == 3:
                # 直接找圖片的src
                captcha_element = page.wait_for_selector(target_element)
                screenshot = captcha_element.get_attribute('src')
                if screenshot.startswith('data:image'):
                    base64_screenshot = screenshot.split(',')[1]
                else:
                    base_url = page.url
                    full_url = urllib.parse.urljoin(base_url, screenshot)
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}
                    response = requests.get(url = full_url, headers=headers)
                    base64_screenshot = base64.b64encode(response.content).decode("utf-8")

            browser.close()

    # 調用解析驗證碼的函數
    captcha_code = CaptchaResolver().get_captcha_code(base64_screenshot)

    # base64 -> bytes
    screenshot = base64.b64decode(base64_screenshot)

    # bytes -> image
    save_image(output_path, captcha_code, screenshot)

    return captcha_code

def git_push(website_name):
    cmd = ["git", "add", "data"]
    subprocess.run(cmd)
    commit_message = f"update datasets for {website_name}"
    cmd = ["git", "commit", "-m", commit_message]
    subprocess.run(cmd)
    cmd = ["git", "push"]
    subprocess.run(cmd)

if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%Y%m%d")
    cfg = OmegaConf.load("setting.yaml")

    # Global setting
    image_count = cfg.image_count
    push_frequency = cfg.push_frequency

    # Select the Website
    target_website = cfg.thsrc

    website_name = target_website.website_name
    website_url = target_website.website_url
    target_element = target_website.target_element
    version = target_website.version
    length = target_website.length
    dtype = target_website.dtype
    

    output_path = f"data/{website_name}_{today}"
    os.makedirs(f"{output_path}", exist_ok=True)

    pbar = tqdm.tqdm(range(image_count), desc="Processing captchas")
    n = 0
    for i in pbar:
        captcha_code = get_captcha_to_database(website_url, target_element, output_path, version)
        pbar.set_description(f"Processing captchas (current code: {captcha_code})")
        if n != 0 and n % push_frequency == 0:
            print(f"{push_frequency} images saved, push to github first")
            git_push(website_name)
        n+=1
