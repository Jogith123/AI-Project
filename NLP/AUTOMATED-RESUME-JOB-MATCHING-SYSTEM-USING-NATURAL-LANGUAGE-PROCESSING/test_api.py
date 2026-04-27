import requests

url = "http://localhost:8000/match"

print("Reading files...")
with open("sample_job.txt", "r") as f:
    job_desc = f.read()

files = [
    ("files", ("sample_resume_good.txt", open("sample_resume_good.txt", "rb"), "text/plain")),
    ("files", ("sample_resume_bad.txt", open("sample_resume_bad.txt", "rb"), "text/plain"))
]
data = {"job_description": job_desc}

print("Sending request to backend...")
try:
    response = requests.post(url, data=data, files=files)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
