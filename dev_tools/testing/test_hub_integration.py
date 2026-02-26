import httpx

# Constants
HUB_URL = "https://logichive-hub-344411298688.asia-northeast1.run.app"
TEST_QUERY = "Implementation of a 2D vector rotation around the origin"
TEST_CANDIDATES = [
    {
        "name": "vector_norm",
        "description": "Calculates the magnitude of a 2D vector",
        "tags": ["math", "linear-algebra"],
    },
    {
        "name": "rotate_point_2d",
        "description": "Rotates a point (x, y) by a given angle in radians around (0, 0)",
        "tags": ["math", "geometry", "2d"],
    },
    {
        "name": "color_to_grayscale",
        "description": "Converts an RGB color vector to grayscale",
        "tags": ["image", "color"],
    },
]


def test_hub_rerank():
    print(f"Testing Hub Rerank at: {HUB_URL}")

    with httpx.Client(timeout=30.0) as client:
        # Health Check
        print("Checking Hub Health...")
        health_resp = client.get(f"{HUB_URL.rstrip('/')}/health")
        print(f"Health Status: {health_resp.status_code}, Body: {health_resp.text}")

        url = f"{HUB_URL.rstrip('/')}/api/v1/intelligence/rerank/direct"

    payload = {"query": TEST_QUERY, "candidates": TEST_CANDIDATES}

    try:
        with httpx.Client(timeout=30.0) as client:
            print(f"Sending request for query: '{TEST_QUERY}'")
            resp = client.post(url, json=payload)

            if resp.status_code == 200:
                result = resp.json()
                selected = result.get("selected_name")
                print(f"SUCCESS: Hub selected '{selected}'")

                if selected == "rotate_point_2d":
                    print(
                        "VERIFICATION PASSED: Gemma 3 correctly identified the rotation function."
                    )
                else:
                    print(
                        f"VERIFICATION FAILED: Expected 'rotate_point_2d', but got '{selected}'"
                    )
            elif resp.status_code == 429:
                print("FAILED: Rate limit exceeded (429). Hub Gemini API is busy.")
            else:
                print(f"FAILED: Status {resp.status_code}")
                print(f"Response: {resp.text}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    test_hub_rerank()
