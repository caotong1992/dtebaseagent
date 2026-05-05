import requests

url = "http://localhost:8080/api/v1/diagnose"

payload='{"description": "服务响应缓慢", "environment": {"cluster_name": "prod-01"}}'
# payload = "{\"query\": \"请给出一个标书文件的常见提纲\"}"
headers = {
  'Authorization': 'Bearer test-api-key-123',
  'Content-Type': 'application/json; charset=utf-8',
  'Cookie': 'locale=en-us'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)