#kdfix/utils/enc_code.py

def give_me_char(c):
    return str(hex(ord(c)))[2:4]

def form_key(key):
    f_key:str = "0x"
    for v in key:
        f_key += give_me_char(v)
    # Keep '0x' and the next 16 characters
    return f_key[:18]