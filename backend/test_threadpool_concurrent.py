#!/usr/bin/env python3
"""
測試 Thread Pool 並發處理能力
模擬語音評分的阻塞 I/O 操作
"""
import asyncio
import time
import aiohttp
import statistics

# Production URL
BASE_URL = "https://duotopia-production-backend-316409492201.asia-east1.run.app"


async def simulate_blocking_request(session, user_id, request_id):
    """模擬需要 thread pool 處理的阻塞請求"""
    url = f"{BASE_URL}/api/speech-assessment/test-concurrent"

    start = time.time()
    try:
        async with session.get(url, timeout=30) as response:
            elapsed = time.time() - start
            data = await response.json()
            return {
                "user_id": user_id,
                "request_id": request_id,
                "elapsed": elapsed,
                "success": True,
                "api_elapsed": data.get("elapsed_seconds", 0),
            }
    except Exception as e:
        return {
            "user_id": user_id,
            "request_id": request_id,
            "elapsed": time.time() - start,
            "success": False,
            "error": str(e),
        }


async def test_concurrent_users(num_users):
    """測試 N 個用戶並發"""
    print(f"\n{'='*60}")
    print(f"🧪 測試 {num_users} 個並發用戶")
    print(f"{'='*60}")

    async with aiohttp.ClientSession() as session:
        # 每個用戶發送 1 個請求
        tasks = []
        for user_id in range(num_users):
            task = simulate_blocking_request(session, user_id, 1)
            tasks.append(task)

        # 並發執行
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 分析結果
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            latencies = [r["elapsed"] for r in successful]
            avg_latency = statistics.mean(latencies)
            median = statistics.median(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)

            # 檢查是否是並發處理
            latency_spread = max_latency - min_latency

            print(f"\n✅ 成功: {len(successful)}/{len(results)}")
            print(f"❌ 失敗: {len(failed)}")
            print(f"\n⏱️  總執行時間: {total_time:.2f}s")
            print("\n📊 延遲分析:")
            print(f"   平均: {avg_latency*1000:.0f}ms")
            print(f"   中位數: {median*1000:.0f}ms")
            print(f"   最小: {min_latency*1000:.0f}ms")
            print(f"   最大: {max_latency*1000:.0f}ms")
            print(f"   延遲差距: {latency_spread*1000:.0f}ms")

            # 判斷是並發還是序列
            print("\n🔍 並發處理判斷:")
            if latency_spread < 1.0:  # 差距小於 1 秒
                print("   ✅ 並發處理（延遲差距 < 1s）")
                print("   所有請求幾乎同時完成")
            elif latency_spread > num_users * 0.2:  # 差距大於人數*200ms
                print("   ❌ 序列處理（延遲呈階梯式）")
                print("   每個請求等待前一個完成")
            else:
                print("   ⚠️  部分並發（有些排隊）")

            # 顯示延遲分布
            print("\n📈 延遲分布:")
            sorted_latencies = sorted(latencies)
            for i, lat in enumerate(sorted_latencies[:5], 1):
                print(f"   第 {i:2d} 快: {lat*1000:6.0f}ms")
            if len(sorted_latencies) > 10:
                print("   ...")
            for i, lat in enumerate(sorted_latencies[-5:], len(sorted_latencies) - 4):
                print(f"   第 {i:2d} 慢: {lat*1000:6.0f}ms")

        return {
            "num_users": num_users,
            "total_time": total_time,
            "successful": len(successful),
            "failed": len(failed),
        }


async def main():
    print("🚀 Thread Pool 並發測試")
    print(f"🎯 {BASE_URL}")

    # 先測試連線
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            data = await response.json()
            print("\n✅ 服務健康")
            thread_pools = data.get("thread_pools", {})
            print("🧵 Thread Pool 狀態:")
            speech_workers = thread_pools.get("speech_pool", {}).get(
                "max_workers", "N/A"
            )
            audio_workers = thread_pools.get("audio_pool", {}).get("max_workers", "N/A")
            print(f"   Speech Pool: {speech_workers} workers")
            print(f"   Audio Pool: {audio_workers} workers")

    # 測試不同並發數
    test_cases = [5, 10, 20]

    all_results = []
    for num_users in test_cases:
        result = await test_concurrent_users(num_users)
        all_results.append(result)
        await asyncio.sleep(2)  # 休息 2 秒

    # 總結
    print(f"\n\n{'='*60}")
    print("📊 測試總結")
    print(f"{'='*60}\n")

    print(f"{'並發數':<10} {'總時間':<10} {'成功率':<10}")
    print(f"{'-'*30}")
    for r in all_results:
        success_rate = r["successful"] / (r["successful"] + r["failed"]) * 100
        print(
            f"{r['num_users']:<10} {r['total_time']:<10.2f} " f"{success_rate:<10.1f}%"
        )

    print("\n💡 結論:")
    print("   如果 20 人的總時間接近 5 人 → Thread Pool 並發正常")
    print("   如果 20 人的總時間是 5 人的 4 倍 → 有序列化問題")


if __name__ == "__main__":
    asyncio.run(main())
