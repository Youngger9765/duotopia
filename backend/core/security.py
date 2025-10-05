"""
安全性配置和加密功能
"""

import os
import ssl
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import secrets
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# 密碼雜湊設定
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12
)  # 提高 rounds 數增加安全性


class SecurityConfig:
    """安全性配置管理"""

    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
        self.encryption_key = self._get_or_create_encryption_key()

    def _get_or_create_encryption_key(self) -> bytes:
        """取得或建立加密金鑰"""
        key_str = os.getenv("ENCRYPTION_KEY")
        if not key_str:
            # 如果沒有設定，生成新的金鑰
            key = Fernet.generate_key()
            print("⚠️ No ENCRYPTION_KEY found, generated new one (save it!)")
            print(f"ENCRYPTION_KEY={key.decode()}")
            return key
        return key_str.encode()

    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """取得 SSL 上下文用於加密連線"""
        if os.getenv("ENVIRONMENT") == "production":
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            return context
        return None

    def get_database_ssl_params(self) -> Dict[str, Any]:
        """取得資料庫 SSL 連線參數"""
        if os.getenv("DATABASE_SSL_MODE", "prefer") == "require":
            return {
                "sslmode": "require",
                "sslcert": os.getenv("DATABASE_SSL_CERT"),
                "sslkey": os.getenv("DATABASE_SSL_KEY"),
                "sslrootcert": os.getenv("DATABASE_SSL_ROOT_CERT"),
            }
        return {"sslmode": "prefer"}


class DataEncryption:
    """資料加密服務"""

    def __init__(self, key: Optional[bytes] = None):
        if key:
            self.cipher = Fernet(key)
        else:
            # 使用環境變數的金鑰
            key_str = os.getenv("ENCRYPTION_KEY")
            if not key_str:
                raise ValueError("ENCRYPTION_KEY not set in environment")
            self.cipher = Fernet(key_str.encode())

    def encrypt(self, data: str) -> str:
        """加密字串"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密字串"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: dict) -> str:
        """加密字典"""
        import json

        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """解密字典"""
        import json

        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class PasswordPolicy:
    """密碼政策檢查"""

    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate(cls, password: str) -> tuple[bool, str]:
        """驗證密碼是否符合政策"""
        if len(password) < cls.MIN_LENGTH:
            return False, f"密碼長度至少需要 {cls.MIN_LENGTH} 個字元"

        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "密碼需要包含至少一個大寫字母"

        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "密碼需要包含至少一個小寫字母"

        if cls.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "密碼需要包含至少一個數字"

        if cls.REQUIRE_SPECIAL and not any(c in cls.SPECIAL_CHARS for c in password):
            return False, "密碼需要包含至少一個特殊字元"

        return True, "密碼符合安全政策"

    @classmethod
    def generate_strong_password(cls, length: int = 16) -> str:
        """生成強密碼"""
        import random
        import string

        # 確保包含所有必需的字元類型
        password_chars = []

        if cls.REQUIRE_UPPERCASE:
            password_chars.append(random.choice(string.ascii_uppercase))
        if cls.REQUIRE_LOWERCASE:
            password_chars.append(random.choice(string.ascii_lowercase))
        if cls.REQUIRE_DIGIT:
            password_chars.append(random.choice(string.digits))
        if cls.REQUIRE_SPECIAL:
            password_chars.append(random.choice(cls.SPECIAL_CHARS))

        # 填充剩餘長度
        all_chars = ""
        if cls.REQUIRE_UPPERCASE:
            all_chars += string.ascii_uppercase
        if cls.REQUIRE_LOWERCASE:
            all_chars += string.ascii_lowercase
        if cls.REQUIRE_DIGIT:
            all_chars += string.digits
        if cls.REQUIRE_SPECIAL:
            all_chars += cls.SPECIAL_CHARS

        for _ in range(length - len(password_chars)):
            password_chars.append(random.choice(all_chars))

        # 打亂順序
        random.shuffle(password_chars)

        return "".join(password_chars)


class TokenManager:
    """JWT Token 管理"""

    def __init__(self, secret: str = None, algorithm: str = "HS256"):
        self.secret = secret or os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.algorithm = algorithm

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """建立存取 token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
            }
        )

        encoded_jwt = jwt.encode(to_encode, self.secret, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """驗證 token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def create_refresh_token(self, user_id: str) -> str:
        """建立更新 token"""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return jwt.encode(data, self.secret, algorithm=self.algorithm)


class SecureSession:
    """安全 Session 管理"""

    def __init__(self):
        self.sessions = {}  # 實際應該用 Redis

    def create_session(self, user_id: str, ip_address: str) -> str:
        """建立 session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "user_id": user_id,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }
        return session_id

    def validate_session(self, session_id: str, ip_address: str) -> bool:
        """驗證 session"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # 檢查 IP 是否一致
        if session["ip_address"] != ip_address:
            return False

        # 檢查是否過期（30 分鐘無活動）
        if datetime.utcnow() - session["last_activity"] > timedelta(minutes=30):
            del self.sessions[session_id]
            return False

        # 更新最後活動時間
        session["last_activity"] = datetime.utcnow()
        return True

    def destroy_session(self, session_id: str):
        """銷毀 session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# 全域實例
security_config = SecurityConfig()
data_encryption = DataEncryption()
token_manager = TokenManager()
secure_session = SecureSession()


# 密碼雜湊函數
def hash_password(password: str) -> str:
    """雜湊密碼"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)


# 敏感資料遮罩
def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """遮罩敏感資料"""
    if len(data) <= visible_chars * 2:
        return "*" * len(data)
    return (
        data[:visible_chars]
        + "*" * (len(data) - visible_chars * 2)
        + data[-visible_chars:]
    )


# IP 地址驗證
def is_valid_ip(ip: str) -> bool:
    """驗證 IP 地址"""
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# 防止 SQL Injection
def sanitize_input(input_str: str) -> str:
    """清理輸入防止 SQL Injection"""
    # 移除危險字元
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_", "0x"]
    cleaned = input_str
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, "")
    return cleaned.strip()
