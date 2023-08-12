import base64
import datetime
import os
import time
from tqdm import tqdm

import requests

from captcha_resolver import CaptchaResolver


def get_captcha_to_database_from_req() -> str:
    today = datetime.datetime.now().strftime("%Y%m%d")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"}
    img_src = "https://www.newebpay.com/main/main/captcha_img"
    response = requests.get(url = img_src, headers=headers)
    captcha_base64 = base64.b64encode(response.content).decode("utf-8")
    captcha_code = CaptchaResolver().get_captcha_code(captcha_base64)
    captcha_code = captcha_code.upper()
    os.makedirs(f"data/captchas_{today}", exist_ok=True)
    if len(captcha_code) == 5:
        with open(f"data/captchas_{today}/{captcha_code}.png", "wb") as file:
            file.write(response.content)
        return captcha_code

def get_captcha_detection(image_path) -> list:
    """如果抓取的圖片本來就是base64，可以直接使用get_detection_captcha_code()，不用再轉換一次。."""
    image = CaptchaResolver().get_image_in_base64(image_path)
    captcha_code = CaptchaResolver().get_detection_captcha_code(image, "data/result.jpg")
    return captcha_code

if __name__ == "__main__":
    pbar = tqdm(range(1000), desc="Processing captchas")
    for i in pbar:
        captcha_code = get_captcha_to_database_from_req()
        pbar.set_description(f"Processing captchas (current code: {captcha_code})")
        time.sleep(1)
