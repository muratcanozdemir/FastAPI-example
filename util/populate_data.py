import requests
import json

data = json.loads("knowledge_source.json")

response = requests.post("http://localhost:8001/populate_data/", json=data)
print(response.json())
