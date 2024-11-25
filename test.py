import requests

req = requests.post("http://127.0.0.1:8080/api/v1/semester", json={
    "start_month": "2024-09",
    "end_month": "2025-01",
    "semester_name":  "2024-2025学年第一学期"
})
print(req.json())

# req = requests.post("http://127.0.0.1:8080/api/v1/template", json={
#     "building": "4",
#     "room": "111",
#     "classname": "191981"
# })
# print(req.json())
#
# req = requests.delete("http://127.0.0.1:8080/api/v1/template/4")
# print(req.json())

# req = requests.delete("http://127.0.0.1:8080/api/v1/template")
# print(req.json())

# 打开文件并发送 POST 请求
# with open("./template.csv", 'rb') as file:
#     files = {'file': ("./template.csv", file, 'text/csv')}
#     req = requests.post("http://127.0.0.1:8080/api/v1/template/upload", files=files)
# print(req.json())

req = requests.get("http://127.0.0.1:8080/api/v1/template")
print(req.json())