#!/usr/bin/env python3
"""
測試 API Rate Limiting 功能
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = "http://localhost:8000"

def test_rate_limit(endpoint: str, max_requests: int, window: int):
    """測試特定端點的速率限制"""
    print(f"\n🧪 Testing {endpoint} - Limit: {max_requests}/{window}s")

    results = []
    for i in range(max_requests + 5):  # 故意超過限制
        response = requests.get(f"{BASE_URL}{endpoint}")

        # 取得 rate limit headers
        headers = {
            "status": response.status_code,
            "limit": response.headers.get("X-RateLimit-Limit"),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset": response.headers.get("X-RateLimit-Reset"),
        }

        results.append(headers)

        if response.status_code == 429:
            print(f"  ❌ Request {i+1}: Rate limited! Retry after: {response.headers.get('Retry-After')}s")
        else:
            print(f"  ✅ Request {i+1}: OK (Remaining: {headers['remaining']})")

        time.sleep(0.1)  # 小延遲避免太快

    # 統計結果
    success = sum(1 for r in results if r["status"] == 200)
    limited = sum(1 for r in results if r["status"] == 429)

    print(f"\n📊 Results: {success} successful, {limited} rate limited")
    return results

def test_concurrent_requests(endpoint: str, num_threads: int = 10):
    """測試並發請求"""
    print(f"\n🔥 Testing concurrent requests to {endpoint} with {num_threads} threads")

    def make_request(i):
        response = requests.get(f"{BASE_URL}{endpoint}")
        return {
            "thread": i,
            "status": response.status_code,
            "remaining": response.headers.get("X-RateLimit-Remaining"),
        }

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(make_request, range(num_threads)))

    success = sum(1 for r in results if r["status"] == 200)
    limited = sum(1 for r in results if r["status"] == 429)

    print(f"📊 Concurrent Results: {success} successful, {limited} rate limited")
    return results

def test_different_ips():
    """測試不同 IP 的獨立限制"""
    print("\n🌐 Testing different IPs have separate limits")

    headers1 = {"X-Forwarded-For": "192.168.1.100"}
    headers2 = {"X-Forwarded-For": "192.168.1.200"}

    # IP 1 的請求
    print("  IP 192.168.1.100:")
    for i in range(3):
        response = requests.get(f"{BASE_URL}/health", headers=headers1)
        print(f"    Request {i+1}: {response.status_code}, Remaining: {response.headers.get('X-RateLimit-Remaining')}")

    # IP 2 的請求（應該有獨立的限制）
    print("  IP 192.168.1.200:")
    for i in range(3):
        response = requests.get(f"{BASE_URL}/health", headers=headers2)
        print(f"    Request {i+1}: {response.status_code}, Remaining: {response.headers.get('X-RateLimit-Remaining')}")

def test_auth_endpoint_strict_limit():
    """測試認證端點的嚴格限制"""
    print("\n🔐 Testing strict auth endpoint limits")

    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }

    for i in range(7):  # 登入限制是 5 次/分鐘
        response = requests.post(
            f"{BASE_URL}/api/auth/teacher/login",
            json=login_data
        )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            print(f"  ❌ Attempt {i+1}: Blocked! Wait {retry_after}s")
            print(f"     This prevents brute force attacks!")
        else:
            print(f"  🔑 Attempt {i+1}: {response.status_code}")

def main():
    print("=" * 60)
    print("🚀 API Rate Limiting Test Suite")
    print("=" * 60)

    # 測試健康檢查端點（寬鬆限制）
    test_rate_limit("/health", 1000, 60)

    # 測試一般 API 端點（中等限制）
    test_rate_limit("/api/teachers/classrooms", 30, 60)

    # 測試並發請求
    test_concurrent_requests("/health", 20)

    # 測試不同 IP
    test_different_ips()

    # 測試認證端點（嚴格限制）
    test_auth_endpoint_strict_limit()

    print("\n" + "=" * 60)
    print("✅ Rate Limiting Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
