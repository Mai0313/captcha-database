from captcha_resolver import CaptchaResolver

image = "test.png"

# read png to base64
image = CaptchaResolver().get_image_in_base64(image)

captcha_code = CaptchaResolver().get_detection_captcha_code(image, "data/result.jpg")
print(captcha_code)
