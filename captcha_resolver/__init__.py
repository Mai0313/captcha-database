# coding=utf-8
import warnings

warnings.filterwarnings('ignore')
from captcha_resolver.models.core import Resolver
import base64
import cv2
import numpy as np

class CaptchaResolver:
    def __init__(self):
        pass

    def get_image_in_base64(self, image_path: str) -> str:
        """This function is used to read the image and convert it to base64.

        Args:
            image_path (str): The path of the image.

        Returns:
            str: The image in base64.
        """
        with open(image_path, 'rb') as f:
            image = f.read()
            image = base64.b64encode(image).decode("utf-8")
        return image

    def get_captcha_code(self, captcha_base64: str, upper: bool = True, enable_gpu: bool = False) -> str:
        """This function is used to recognize the captcha code in the image.

        Args:
            captcha_base64 (str): The captcha image in base64.
            upper (bool, optional): Whether to convert the result to uppercase. Defaults to True.
            enable_gpu (bool, optional): Whether to use GPU. Defaults to False.

        Returns:
            str: The captcha code.
        """
        capt = Resolver(use_gpu = enable_gpu)
        result = capt.classification(captcha_base64)
        if upper:
            result = result.upper()
        return result

    def get_detection_captcha_code(self, captcha_base64: str, output_path: str = "result.jpg", enable_gpu: bool = False) -> str:
        """This function is used to detect the captcha code in the image.

        Args:
            captcha_base64 (str): The captcha image in base64.
            output_path (str, optional): The output path of the image. Defaults to "result.jpg".
            enable_gpu (bool, optional): Whether to use GPU. Defaults to False.

        Returns:
            str: The detected captcha "words" position.
        """
        img_bytes = base64.b64decode(captcha_base64)

        det = Resolver(det=True, use_gpu = enable_gpu)
        poses = det.detection(img_bytes=img_bytes)

        nparr = np.frombuffer(img_bytes, np.uint8)
        im = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        for box in poses:
            x1, y1, x2, y2 = box
            im = cv2.rectangle(im, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=1)
        cv2.imwrite(output_path, im)
        return poses
