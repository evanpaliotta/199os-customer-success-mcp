"""
Load Testing with Locust

This script uses Locust to perform load testing on the Customer Success MCP.

Installation:
    pip install locust

Usage:
    # Run with web UI (http://localhost:8089)
    locust -f tests/load_test.py --host=http://localhost:8080

    # Run headless with 100 users
    locust -f tests/load_test.py --host=http://localhost:8080 --users 100 --spawn-rate 10 --run-time 5m --headless

    # Generate HTML report
    locust -f tests/load_test.py --host=http://localhost:8080 --users 100 --spawn-rate 10 --run-time 5m --headless --html=load_test_report.html

Test Scenarios:
    - Baseline: 10 concurrent users
    - Target: 50 concurrent users
    - Peak: 100 concurrent users

Performance Targets:
    - P95 latency <1s
    - Error rate <1%
    - Throughput >100 requests/second
"""

from locust import HttpUser, task, between, events
import random
import string
import json
from datetime import datetime, date, timedelta


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_client_id() -> str:
    """Generate a unique client ID for load testing."""
    timestamp = int(datetime.now().timestamp())
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"cs_{timestamp}_{random_suffix}"


def generate_customer_data() -> dict:
    """Generate random customer data for load testing."""
    industries = ["SaaS", "Technology", "Healthcare", "Finance", "E-commerce", "Manufacturing"]
    tiers = ["starter", "standard", "professional", "enterprise"]

    return {
        "client_name": f"Load Test Company {random.randint(1000, 9999)}",
        "company_name": f"Load Test Company {random.randint(1000, 9999)} Inc.",
        "industry": random.choice(industries),
        "tier": random.choice(tiers),
        "contract_value": float(random.randint(10000, 500000)),
        "contract_start_date": date.today().isoformat(),
        "contract_end_date": (date.today() + timedelta(days=365)).isoformat(),
        "renewal_date": (date.today() + timedelta(days=365)).isoformat(),
        "primary_contact_email": f"test{random.randint(1000, 9999)}@loadtest.com",
        "primary_contact_name": f"Load Test User {random.randint(1000, 9999)}",
        "csm_assigned": f"CSM {random.randint(1, 10)}"
    }


def generate_health_score_data() -> dict:
    """Generate random health score data."""
    return {
        "usage_score": random.uniform(20, 100),
        "engagement_score": random.uniform(20, 100),
        "support_score": random.uniform(20, 100),
        "satisfaction_score": random.uniform(20, 100),
        "payment_score": random.uniform(70, 100)
    }


# ============================================================================
# Locust User Classes
# ============================================================================

class CSMCPUser(HttpUser):
    """
    Simulates a typical Customer Success Manager using CS MCP.

    Performs common operations:
    - Register customers
    - View customer overviews
    - Calculate health scores
    - Create onboarding plans
    - Track usage
    - Create support tickets
    - Send emails
    """

    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts. Initialize user-specific data."""
        self.client_ids = []

        # Register 1-3 customers for this user
        num_customers = random.randint(1, 3)
        for _ in range(num_customers):
            client_id = generate_client_id()
            self.client_ids.append(client_id)

            # Register customer (don't track this in tasks, as it's setup)
            customer_data = generate_customer_data()
            customer_data["client_id"] = client_id

            try:
                with self.client.post(
                    "/v1/tools/register_client",
                    json=customer_data,
                    catch_response=True,
                    name="/tools/register_client [setup]"
                ) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Failed to register customer: {response.status_code}")
            except Exception as e:
                pass  # Ignore setup failures

    @task(10)
    def get_customer_overview(self):
        """Retrieve customer overview (most common operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        with self.client.get(
            f"/v1/tools/get_client_overview",
            params={"client_id": client_id},
            name="/tools/get_client_overview",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Customer not found")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(8)
    def calculate_health_score(self):
        """Calculate customer health score (frequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)
        health_data = generate_health_score_data()
        health_data["client_id"] = client_id

        with self.client.post(
            "/v1/tools/calculate_health_score",
            json=health_data,
            name="/tools/calculate_health_score",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "health_score" in data:
                        response.success()
                    else:
                        response.failure("Missing health_score in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(5)
    def list_customers(self):
        """List customers with filters (common operation)."""
        filters = [
            {"tier": "professional"},
            {"lifecycle_stage": "active"},
            {"health_score_min": 70},
            {}  # No filter
        ]

        filter_params = random.choice(filters)

        with self.client.get(
            "/v1/tools/list_clients",
            params=filter_params,
            name="/tools/list_clients",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(6)
    def track_usage(self):
        """Track customer usage events (frequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        event_names = ["login", "feature_used", "report_generated", "export", "api_call"]
        event_name = random.choice(event_names)

        event_data = {
            "client_id": client_id,
            "event_name": event_name,
            "properties": {
                "source": random.choice(["web", "mobile", "api"]),
                "timestamp": datetime.now().isoformat()
            }
        }

        with self.client.post(
            "/v1/tools/track_usage_engagement",
            json=event_data,
            name="/tools/track_usage_engagement",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def create_onboarding_plan(self):
        """Create onboarding plan (less frequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        plan_data = {
            "client_id": client_id,
            "plan_name": f"Onboarding Plan {random.randint(1000, 9999)}",
            "duration_days": random.choice([30, 60, 90]),
            "milestones": [
                {
                    "milestone_name": "Initial Setup",
                    "target_date": (date.today() + timedelta(days=7)).isoformat(),
                    "completion_criteria": ["Setup complete", "Training scheduled"]
                }
            ]
        }

        with self.client.post(
            "/v1/tools/create_onboarding_plan",
            json=plan_data,
            name="/tools/create_onboarding_plan",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(4)
    def identify_churn_risk(self):
        """Identify churn risk (regular operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        risk_data = {
            "client_id": client_id,
            "health_score": random.uniform(20, 80)
        }

        with self.client.post(
            "/v1/tools/identify_churn_risk",
            json=risk_data,
            name="/tools/identify_churn_risk",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def create_support_ticket(self):
        """Create support ticket (less frequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        ticket_data = {
            "client_id": client_id,
            "subject": f"Support Request {random.randint(1000, 9999)}",
            "description": "This is a load test support ticket",
            "priority": random.choice(["low", "medium", "high"]),
            "category": random.choice(["technical", "billing", "training", "general"])
        }

        with self.client.post(
            "/v1/tools/handle_support_ticket",
            json=ticket_data,
            name="/tools/handle_support_ticket",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def send_email(self):
        """Send personalized email (less frequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        email_data = {
            "client_id": client_id,
            "template": random.choice(["welcome", "monthly_report", "renewal_reminder"]),
            "recipient_email": f"test{random.randint(1000, 9999)}@loadtest.com",
            "subject": f"Test Email {random.randint(1000, 9999)}",
            "variables": {"name": "Load Test User"}
        }

        with self.client.post(
            "/v1/tools/send_personalized_email",
            json=email_data,
            name="/tools/send_personalized_email",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def update_customer(self):
        """Update customer information (infrequent operation)."""
        if not self.client_ids:
            return

        client_id = random.choice(self.client_ids)

        update_data = {
            "client_id": client_id,
            "updates": {
                "csm_assigned": f"CSM {random.randint(1, 10)}",
                "notes": f"Updated at {datetime.now().isoformat()}"
            }
        }

        with self.client.patch(
            "/v1/tools/update_client_info",
            json=update_data,
            name="/tools/update_client_info",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class AnalyticsUser(HttpUser):
    """
    Simulates analytics/reporting workload.

    Performs read-heavy operations:
    - Query customer segments
    - Generate reports
    - Analyze trends
    """

    wait_time = between(2, 5)

    @task(5)
    def segment_customers(self):
        """Segment customers (analytics operation)."""
        segment_types = ["value_based", "industry", "lifecycle", "health_based"]

        segment_data = {
            "segment_type": random.choice(segment_types),
            "criteria": {
                "min_arr": random.choice([10000, 50000, 100000]),
                "tier": [random.choice(["starter", "standard", "professional", "enterprise"])]
            }
        }

        with self.client.post(
            "/v1/tools/segment_customers",
            json=segment_data,
            name="/tools/segment_customers",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def analyze_product_usage(self):
        """Analyze product usage patterns (analytics operation)."""
        analysis_data = {
            "time_period": random.choice(["7d", "30d", "90d"]),
            "metrics": ["active_users", "feature_adoption", "session_duration"]
        }

        with self.client.post(
            "/v1/tools/analyze_product_usage",
            json=analysis_data,
            name="/tools/analyze_product_usage",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def generate_retention_report(self):
        """Generate retention report (analytics operation)."""
        report_data = {
            "report_type": "retention",
            "time_period": random.choice(["30d", "90d", "1y"])
        }

        with self.client.post(
            "/v1/tools/generate_report",
            json=report_data,
            name="/tools/generate_report",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# ============================================================================
# Event Handlers for Reporting
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    print("\n" + "=" * 80)
    print("CUSTOMER SUCCESS MCP - LOAD TEST STARTING")
    print("=" * 80)
    print(f"Target: {environment.host}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops. Print summary."""
    print("\n" + "=" * 80)
    print("CUSTOMER SUCCESS MCP - LOAD TEST COMPLETED")
    print("=" * 80)
    print(f"Test ended at: {datetime.now().isoformat()}")

    # Get statistics
    stats = environment.stats

    # Print summary
    print("\n📊 SUMMARY STATISTICS:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Total Failures: {stats.total.num_failures}")
    print(f"  Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"  Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"  Median Response Time: {stats.total.median_response_time:.2f}ms")
    print(f"  P95 Response Time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  P99 Response Time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  RPS: {stats.total.total_rps:.2f}")

    # Performance targets
    print("\n🎯 PERFORMANCE TARGETS:")
    p95 = stats.total.get_response_time_percentile(0.95)
    fail_rate = stats.total.fail_ratio * 100

    p95_pass = p95 < 1000
    error_rate_pass = fail_rate < 1

    print(f"  P95 Latency < 1s: {'✅ PASS' if p95_pass else '❌ FAIL'} ({p95:.2f}ms)")
    print(f"  Error Rate < 1%: {'✅ PASS' if error_rate_pass else '❌ FAIL'} ({fail_rate:.2f}%)")

    overall_pass = p95_pass and error_rate_pass
    print(f"\n  Overall: {'✅ PASS' if overall_pass else '❌ FAIL'}")

    print("=" * 80 + "\n")


# ============================================================================
# Custom Load Test Shapes
# ============================================================================

from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Load test with step increases.

    Steps:
    1. Baseline: 10 users for 2 minutes
    2. Target: 50 users for 3 minutes
    3. Peak: 100 users for 3 minutes
    4. Cool down: 10 users for 2 minutes
    """

    step_time = 60  # Each step lasts 60 seconds
    step_load = 10  # Increase by 10 users per step
    spawn_rate = 5  # Spawn 5 users per second
    time_limit = 600  # Total test time: 10 minutes

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 120:
            # Baseline: 10 users
            return (10, self.spawn_rate)
        elif run_time < 300:
            # Target: 50 users
            return (50, self.spawn_rate)
        elif run_time < 480:
            # Peak: 100 users
            return (100, self.spawn_rate)
        elif run_time < 600:
            # Cool down: 10 users
            return (10, self.spawn_rate)
        else:
            return None


# ============================================================================
# Run Load Test
# ============================================================================

if __name__ == "__main__":
    """
    Run load test from command line.

    Example:
        python tests/load_test.py
    """

    import subprocess
    import sys

    print("\nStarting Locust load test...")
    print("Web UI will be available at: http://localhost:8089")
    print("\nPress Ctrl+C to stop the test\n")

    # Run Locust with web UI
    subprocess.run([
        "locust",
        "-f", __file__,
        "--host", "http://localhost:8080"
    ])
