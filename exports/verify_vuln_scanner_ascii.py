import json
import urllib.request
import urllib.error

def check_package_vulnerability(package_name: str, version: str) -> dict:
    """
    Queries Google's OSV (Open Source Vulnerability) API to check for vulnerabilities
    in a specific package name and version.
    """
    url = "https://api.osv.dev/v1/query"
    
    # Request Payload
    payload = {
        "package": {
            "name": package_name,
            "ecosystem": "PyPI"
        },
        "version": version
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            # If the OSV API returns 'vulns' key, there are active CVEs
            vulns = res_data.get("vulns", [])
            return {
                "package": package_name,
                "version": version,
                "has_vulnerabilities": len(vulns) > 0,
                "count": len(vulns),
                "details": [
                    {
                        "id": v.get("id"),
                        "summary": v.get("summary", "No summary provided"),
                        "details": v.get("details", "")[:120] + "...",
                        "aliases": v.get("aliases", [])
                    }
                    for v in vulns
                ]
            }
    except urllib.error.URLError as e:
        return {
            "package": package_name,
            "version": version,
            "error": f"API Request failed: {e}"
        }

if __name__ == "__main__":
    # Test cases:
    # 1. urllib3==1.26.15 (Known CVE-2023-37895, etc.)
    # 2. requests==2.31.0 (Known GHSA-j8r2-6x86-q33q / CVE-2024-3651, etc.)
    # 3. requests==2.32.3 (Current secure version)
    
    test_packages = [
        ("urllib3", "1.26.15"),
        ("requests", "2.31.0"),
        ("requests", "2.32.3")
    ]
    
    print("=== LogicHive Dependency Vulnerability Scanner Simulation ===")
    for pkg, ver in test_packages:
        print(f"\nScanning: {pkg}=={ver}...")
        result = check_package_vulnerability(pkg, ver)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        elif result["has_vulnerabilities"]:
            print(f"[!] VULNERABILITIES DETECTED ({result['count']} found)!")
            for idx, vuln in enumerate(result["details"][:2], 1):
                print(f"  {idx}. {vuln['id']} ({', '.join(vuln['aliases'])}): {vuln['summary']}")
                print(f"     Details: {vuln['details']}")
        else:
            print("[OK] Clear! No known vulnerabilities.")
