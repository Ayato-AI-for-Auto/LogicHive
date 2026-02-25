import json
import requests
import sys

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Update hardcoded URLs to use base_url
    def test_hybrid_flow(base_url):
        print(f"Testing Backend Endpoints at {base_url}...")
        
        # 1. Health Check
        health_url = f"{base_url}/health"
        try:
            resp = requests.get(health_url)
            print(f"Health Check: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"Health Check failed: {e}")

        # 2. Execute Check
        execute_url = f"{base_url}/execute"
        execute_data = {
            "code": "def hello(name='world'): return f'hello {name}'",
            "test_cases": [
                {"input": {"name": "LogicHive"}, "expected": "hello LogicHive"},
                {"input": {}, "expected": "hello world"}
            ]
        }
        headers = {"X-API-Key": "PRO-MOCK-KEY-123"}
        
        try:
            resp = requests.post(execute_url, json=execute_data, headers=headers)
            print(f"\nExecute Response: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
        except Exception as e:
            print(f"Execute Request failed: {e}")

    test_hybrid_flow(base_url)
