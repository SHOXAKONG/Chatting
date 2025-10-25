import random
import string


def code_generate():
    letters = random.choices(string.ascii_uppercase, k=3)
    numbers = random.choices(string.digits, k=3)
    code_list = letters + numbers
    random.shuffle(code_list)
    code = ''.join(code_list)
    return code