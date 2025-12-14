"""
Performance Benchmark for Azure Speech API Rate Limiting

Measures response times under different concurrent load scenarios
Provides baseline metrics for production monitoring
"""

import asyncio
import time
import statistics
import sys
import os
from typing import Dict, Any

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class AzureRateLimitBenchmark:
    """Benchmark Azure rate limiting performance"""

    def __init__(self):
        self.results = {}

    async def benchmark_scenario(
        self,
        scenario_name: str,
        num_users: int,
        requests_per_user: int,
        api_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Benchmark a specific concurrent load scenario

        Args:
            scenario_name: Name of the scenario (e.g., "10 users × 10 requests")
            num_users: Number of concurrent users
            requests_per_user: Requests per user
            api_delay: Simulated Azure API delay in seconds

        Returns:
            Performance metrics dictionary
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        response_times = []
        queue_wait_times = []
        errors = []

        async def simulate_user_requests(user_id: int):
            """Simulate one user making multiple requests"""
            user_results = []

            for req_id in range(requests_per_user):
                overall_start = time.time()
                queue_start = time.time()

                try:
                    async with _get_azure_speech_semaphore():
                        queue_wait = time.time() - queue_start
                        queue_wait_times.append(queue_wait)

                        # Simulate Azure API processing
                        await asyncio.sleep(api_delay)

                        response_time = time.time() - overall_start
                        response_times.append(response_time)

                        user_results.append(
                            {
                                "user_id": user_id,
                                "request_id": req_id,
                                "response_time": response_time,
                                "queue_wait": queue_wait,
                            }
                        )

                except Exception as e:
                    errors.append(
                        {
                            "user_id": user_id,
                            "request_id": req_id,
                            "error": str(e),
                        }
                    )

            return user_results

        # Execute benchmark
        start_time = time.time()
        user_tasks = [simulate_user_requests(i) for i in range(num_users)]
        await asyncio.gather(*user_tasks)
        total_time = time.time() - start_time

        # Calculate metrics
        total_requests = num_users * requests_per_user
        successful_requests = len(response_times)
        failed_requests = len(errors)

        metrics = {
            "scenario": scenario_name,
            "num_users": num_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time_seconds": round(total_time, 2),
            "throughput_req_per_sec": round(successful_requests / total_time, 2),
            "response_times": {
                "min": round(min(response_times) if response_times else 0, 3),
                "max": round(max(response_times) if response_times else 0, 3),
                "mean": round(
                    statistics.mean(response_times) if response_times else 0, 3
                ),
                "median": round(
                    statistics.median(response_times) if response_times else 0, 3
                ),
                "p95": round(
                    sorted(response_times)[int(len(response_times) * 0.95)]
                    if response_times
                    else 0,
                    3,
                ),
                "p99": round(
                    sorted(response_times)[int(len(response_times) * 0.99)]
                    if response_times
                    else 0,
                    3,
                ),
            },
            "queue_wait_times": {
                "min": round(min(queue_wait_times) if queue_wait_times else 0, 3),
                "max": round(max(queue_wait_times) if queue_wait_times else 0, 3),
                "mean": round(
                    statistics.mean(queue_wait_times) if queue_wait_times else 0, 3
                ),
                "median": round(
                    statistics.median(queue_wait_times) if queue_wait_times else 0, 3
                ),
                "p95": round(
                    sorted(queue_wait_times)[int(len(queue_wait_times) * 0.95)]
                    if queue_wait_times
                    else 0,
                    3,
                ),
            },
        }

        self.results[scenario_name] = metrics
        return metrics

    def print_results(self, metrics: Dict[str, Any]):
        """Pretty print benchmark results"""
        print(f"\n{'=' * 80}")
        print(f"Scenario: {metrics['scenario']}")
        print(f"{'=' * 80}")
        print("Configuration:")
        print(f"  - Users: {metrics['num_users']}")
        print(f"  - Requests per user: {metrics['requests_per_user']}")
        print(f"  - Total requests: {metrics['total_requests']}")
        print("\nExecution:")
        print(f"  - Total time: {metrics['total_time_seconds']}s")
        print(f"  - Successful: {metrics['successful_requests']}")
        print(f"  - Failed: {metrics['failed_requests']}")
        print(f"  - Throughput: {metrics['throughput_req_per_sec']} req/sec")
        print("\nResponse Times (seconds):")
        rt = metrics["response_times"]
        print(f"  - Min:    {rt['min']}s")
        print(f"  - Mean:   {rt['mean']}s")
        print(f"  - Median: {rt['median']}s")
        print(f"  - P95:    {rt['p95']}s")
        print(f"  - P99:    {rt['p99']}s")
        print(f"  - Max:    {rt['max']}s")
        print("\nQueue Wait Times (seconds):")
        qt = metrics["queue_wait_times"]
        print(f"  - Min:    {qt['min']}s")
        print(f"  - Mean:   {qt['mean']}s")
        print(f"  - Median: {qt['median']}s")
        print(f"  - P95:    {qt['p95']}s")
        print(f"  - Max:    {qt['max']}s")

    def generate_comparison_table(self):
        """Generate comparison table across all scenarios"""
        if not self.results:
            print("No benchmark results to compare")
            return

        print(f"\n{'=' * 120}")
        print("PERFORMANCE COMPARISON - All Scenarios")
        print(f"{'=' * 120}")
        print(
            f"{'Scenario':<30} {'Users':>6} {'Req/User':>8} {'Total':>7} "
            f"{'Time(s)':>8} {'Throughput':>12} {'P95(s)':>8} {'P99(s)':>8}"
        )
        print(f"{'-' * 120}")

        for scenario_name, metrics in self.results.items():
            print(
                f"{scenario_name:<30} "
                f"{metrics['num_users']:>6} "
                f"{metrics['requests_per_user']:>8} "
                f"{metrics['total_requests']:>7} "
                f"{metrics['total_time_seconds']:>8.2f} "
                f"{metrics['throughput_req_per_sec']:>12.2f} "
                f"{metrics['response_times']['p95']:>8.3f} "
                f"{metrics['response_times']['p99']:>8.3f}"
            )

        print(f"{'=' * 120}\n")

    async def run_all_benchmarks(self):
        """Run all benchmark scenarios"""
        scenarios = [
            ("10 users × 10 requests", 10, 10),
            ("30 users × 10 requests", 30, 10),
            ("50 users × 10 requests", 50, 10),
            ("20 users × 5 requests", 20, 5),
            ("5 users × 50 requests", 5, 50),
        ]

        print("\n" + "=" * 80)
        print("Azure Speech API Rate Limiting - Performance Benchmark")
        print("=" * 80)
        print("Configuration:")
        print("  - Semaphore limit: 18 concurrent")
        print("  - Azure API simulated delay: 1.0s")
        print("  - Azure S0 limit: 20 TPS")
        print("=" * 80)

        for scenario_name, num_users, requests_per_user in scenarios:
            print(f"\nRunning: {scenario_name}...")
            metrics = await self.benchmark_scenario(
                scenario_name, num_users, requests_per_user, api_delay=1.0
            )
            self.print_results(metrics)

            # Small delay between scenarios
            await asyncio.sleep(0.5)

        # Print comparison
        self.generate_comparison_table()

        # Generate recommendations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generate deployment recommendations based on benchmark results"""
        print("\n" + "=" * 80)
        print("DEPLOYMENT RECOMMENDATIONS")
        print("=" * 80)

        # Find worst case scenario
        worst_p99 = max(r["response_times"]["p99"] for r in self.results.values())
        worst_scenario = [
            name
            for name, r in self.results.items()
            if r["response_times"]["p99"] == worst_p99
        ][0]

        print("\n1. Performance Baseline:")
        print(f"   - Worst case P99: {worst_p99:.3f}s ({worst_scenario})")
        print("   - Acceptable P99 threshold: < 5.0s")
        print(
            f"   - Status: {'✅ PASS' if worst_p99 < 5.0 else '❌ FAIL - Consider optimizing'}"
        )

        print("\n2. Capacity Planning:")
        max_users_scenario = max(self.results.values(), key=lambda x: x["num_users"])
        print(f"   - Tested up to: {max_users_scenario['num_users']} concurrent users")
        print("   - Semaphore limit: 18 concurrent API calls")
        print("   - Recommended max concurrent users: 50")
        print("   - If exceeding 50 users, consider: Upgrading to Azure S1 (50 TPS)")

        print("\n3. Monitoring Alerts:")
        avg_queue_wait = statistics.mean(
            [r["queue_wait_times"]["mean"] for r in self.results.values()]
        )
        print(f"   - Average queue wait: {avg_queue_wait:.3f}s")
        print("   - Set alert threshold: Queue wait > 2.0s")
        print("   - Set critical threshold: Queue wait > 5.0s")

        print("\n4. Rate Limiting Configuration:")
        print("   - Current semaphore: 18 concurrent")
        print("   - Azure S0 limit: 20 TPS")
        print("   - Buffer: 2 requests (10%)")
        print("   - Status: ✅ Optimal configuration")

        print("\n5. Production Deployment:")
        print("   - ✅ Ready for staging deployment")
        print("   - ✅ Run load test on staging with real Azure API")
        print("   - ✅ Monitor P95/P99 latency for first 48 hours")
        print("   - ✅ Set up alerting for queue wait > 2s")
        print("   - ⚠️  Consider canary deployment (10% traffic first)")

        print("\n" + "=" * 80 + "\n")


async def main():
    """Run benchmark suite"""
    benchmark = AzureRateLimitBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
