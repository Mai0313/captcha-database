import base64
import datetime
import os
import subprocess
import urllib

import requests
from omegaconf import OmegaConf
from playwright.sync_api import sync_playwright
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from captcha_resolver import CaptchaResolver


def save_image(output_path, captcha_code, screenshot: bytes):
    with open(f'{output_path}/{captcha_code}.png', 'wb') as f:
        f.write(screenshot)

def git_push(website_name):
    cmd_sequence = [
        ["git", "add", "data"],
        ["git", "commit", "-m", f"update datasets for {website_name}"],
        ["git", "push"]
    ]

    for cmd in cmd_sequence:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_captcha_to_database(website: str, target_element: str, output_path: str, version: int, length: int, dtype: list) -> str:
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

    min_length, max_length = length
    if not min_length <= len(captcha_code) <= max_length:
        """基本確認，先確認驗證碼長度是否正確，因為很多網站的驗證碼長度都是固定的"""
        return "Length Error, skipping..."
    else:
        if "english" in dtype and not captcha_code.isascii():
            """表示驗證碼除了數字還有英文字母"""
            return "Classified Error, skipping..."

        elif "english" not in dtype and not captcha_code.isdigit():
            """表示驗證碼只有數字"""
            return "Classified Error, skipping..."
        else:
            # bytes -> image
            save_image(output_path, captcha_code, screenshot)
            return captcha_code

def get_config_details():
    """Get the config details from setting.yaml.

    Args:
        targets (list): The target website e.g. ["newebpay"]


    Returns:
        image_count (int): The number of images to be generated
        push_frequency (int): The frequency of pushing to github
        website_name (str): The name of the website
        website_url (str): The url of the website
        target_element (str): The target element of the captcha
        version (int): The version of the script
        length (list): The length of the captcha
        dtype (list): The type of the captcha
        output_path (str): The output path of the captcha
    """
    today = datetime.datetime.now().strftime("%Y%m%d")
    cfg = OmegaConf.load("setting.yaml")

    image_count = cfg.image_count + 1  # Python range() starts from 0, so it needs to add 1
    push_frequency = cfg.push_frequency
    targets = cfg.target_websites

    for target in targets:
        target_website = getattr(cfg, target)

        website_name = target_website.website_name
        website_url = target_website.website_url
        target_element = target_website.target_element
        version = target_website.version
        min_length = target_website.min_length
        max_length = target_website.max_length
        length = [min_length, max_length]
        dtype = target_website.dtype
        output_path = f"data/{website_name}_{today}"
        os.makedirs(f"{output_path}", exist_ok=True)
        return target, image_count, push_frequency, website_name, website_url, target_element, version, length, dtype, output_path

def get_progress_layout():
    job_progress = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    return job_progress

# def main():
#     target = ["newebpay"]
#     image_count, push_frequency, website_name, website_url, target_element, version, length, dtype, output_path = get_config_details()

#     # 定義兩個進度條，注意 job_push 的 total 設置
#     with Progress() as progress:
#         job_captcha = progress.add_task("[green]Processing Captcha Code", total=image_count)
#         job_push = progress.add_task("[magenta]How Many Left before Push", total=image_count // push_frequency)

#         n = 0
#         for i in range(image_count):
#             captcha_code = get_captcha_to_database(website_url, target_element, output_path, version, length, dtype)
#             progress.update(job_captcha, advance=1)
#             if n != 0 and n % push_frequency == 0:
#                 git_push(website_name)
#                 progress.update(job_push, advance=1)  # 每次推送後更新 job_push 進度條
#             n += 1

def main():
    target, image_count, push_frequency, website_name, website_url, target_element, version, length, dtype, output_path = get_config_details()
    job_progress = get_progress_layout()
    job_captcha = job_progress.add_task("[green]Processing Captcha Code", total=image_count)
    job_push = job_progress.add_task("[magenta]How Many Left before Push", total=push_frequency)
    total = sum(task.total for task in job_progress.tasks)
    overall_progress = Progress()
    overall_task = overall_progress.add_task("Jobs Overall", total=int(total))
    progress_table = Table.grid()
    progress_table.add_row(
        Panel.fit(overall_progress, title=f"[b]Processing {target} for {image_count} images", border_style="green", padding=(2, 2)),
        Panel.fit(job_progress, title="[b]Jobs", border_style="red", padding=(1, 2))
    )
    with Live(progress_table, refresh_per_second=10):
        n = 0
        for i in range(image_count):
            captcha_code = get_captcha_to_database(website_url, target_element, output_path, version, length, dtype)
            job_progress.update(job_captcha, advance=1)
            job_progress.update(job_push, advance=1)
            if n != 0 and n % push_frequency == 0:
                git_push(website_name)
                job_progress.reset(job_push)
            n += 1

            completed = sum(task.completed for task in job_progress.tasks)
            overall_progress.update(overall_task, completed=completed)

if __name__ == "__main__":
    main()
