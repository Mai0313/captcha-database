# coding=utf-8
import warnings

warnings.filterwarnings('ignore')
from captcha_resolver.models.core import Resolver

class CaptchaResolver:
    def __init__(self):
        pass

    def get_captcha_code(self, captcha_base64: str, upper: bool = True) -> str:
        capt = Resolver()
        result = capt.classification(captcha_base64)
        if upper:
            result = result.upper()
        return result
