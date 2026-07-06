import requests

SECRET = "sk_test_6e44980deb90556ba54e61222d2628513cd8dc2d"

headers = {
    "Authorization": f"Bearer {SECRET}"
}

response = requests.get(
    "https://api.paystack.co/bank",
    headers=headers,
    timeout=20
)

print("Status Code:", response.status_code)
print("Response:")
print(response.text)