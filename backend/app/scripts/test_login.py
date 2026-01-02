import requests

# Test the login API
url = "http://localhost:8000/api/v1/auth/login"
data = {
    "email": "admin@example.com",
    "password": "Admin123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n✓ Login successful!")
        token = response.json().get("access_token")
        print(f"Access Token: {token[:50]}...")
    else:
        print("\n✗ Login failed!")
except Exception as e:
    print(f"Error: {e}")
