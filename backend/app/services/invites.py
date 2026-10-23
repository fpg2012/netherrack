"""邀请码的生成与校验。"""
import hashlib
import secrets

# Crockford base32：去掉 I/L/O/U，避免和 1/0 混淆
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CODE_LEN = 20
# 输入时允许的混淆字符 → 实际字符
CONFUSABLES = str.maketrans({"O": "0", "I": "1", "L": "1", "U": "V"})


def generate_code() -> str:
    """20 个字符 = 100 bit 熵，按 5 位分组方便抄写。"""
    raw = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))
    return "-".join(raw[i:i + 5] for i in range(0, CODE_LEN, 5))


def normalize(code: str) -> str:
    """统一大小写、去掉分隔符，并纠正易混字符。"""
    return "".join(ch for ch in code.upper() if ch.isalnum()).translate(CONFUSABLES)


def hash_code(code: str) -> str:
    return hashlib.sha256(normalize(code).encode()).hexdigest()


def hint(code: str) -> str:
    return normalize(code)[-4:]
