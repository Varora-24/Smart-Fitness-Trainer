import urllib.request
import json

url = "https://api.github.com/repos/Varora-24/Smart-Fitness-Trainer/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        run = data.get("workflow_runs", [])[0]
        jobs_url = run["jobs_url"]
        
        req2 = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2) as r2:
            jobs = json.loads(r2.read().decode())['jobs']
            for j in jobs:
                print(f"Job: {j['name']}, Conclusion: {j['conclusion']}")
                if j['conclusion'] == 'failure':
                    for s in j['steps']:
                        if s['conclusion'] == 'failure':
                            print("  Failed step:", s['name'])
except Exception as e:
    print("Error:", e)
