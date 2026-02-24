# cython: language_level=3
# auth_core.pyx - Cython 컴파일용 핵심 인증 로직
# 비밀번호 해싱/검증을 C 확장으로 분리 → 리버스 엔지니어링 어려움

import hashlib
import secrets


def _hash_password(password: str) -> str:
    """비밀번호를 salt + SHA256으로 해싱"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    """저장된 해시와 비밀번호 검증"""
    if not stored or ":" not in stored:
        return False
    salt, h = stored.split(":", 1)
    computed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(computed, h)
