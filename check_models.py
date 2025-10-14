import requests

API_KEY = "AIzaSyAL5VOSWMNDToxvpzxeNIMfrXLDwQTUOBo"  # your real key

url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

response = requests.get(url)
print(response.text)
