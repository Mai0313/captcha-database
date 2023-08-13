import autorootcwd  # noqa: F401

from captcha_resolver import CaptchaResolver

def test_get_image_in_base64():
    resolver = CaptchaResolver()
    image_path = 'tests/test_datasets/classification_image.png'
    result = resolver.get_image_in_base64(image_path)
    assert isinstance(result, str)

def test_get_captcha_code():
    resolver = CaptchaResolver()
    image_path = 'tests/test_datasets/classification_image.png'
    captcha_base64 = resolver.get_image_in_base64(image_path)
    result = resolver.get_captcha_code(captcha_base64, upper=True, enable_gpu=False)
    assert isinstance(result, str)

def test_get_detection_captcha_code():
    resolver = CaptchaResolver()
    image_path = 'tests/test_datasets/detection_image.png'
    captcha_base64 = resolver.get_image_in_base64(image_path)
    result = resolver.get_detection_captcha_code(captcha_base64, output_path="tests/test_datasets/detection_result.png", enable_gpu=False)
    assert isinstance(result, list)
