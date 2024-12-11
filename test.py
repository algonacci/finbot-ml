import requests

url = "https://api.sectors.app/v1/company/report/BBCA/"

headers = {
    "Authorization": "3b4395eacac95bc27ba7e231421fd93ec9e15efd566b6f1f2b8e504a124338ed"
}

response = requests.request("GET", url, headers=headers)

print(response.text)
