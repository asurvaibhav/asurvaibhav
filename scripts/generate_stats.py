import os
import json
import urllib.request
from datetime import datetime, timedelta, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GH_LOGIN = os.environ.get("GH_LOGIN", "asurvaibhav")

now = datetime.now(timezone.utc)
to_date = now.strftime("%Y-%m-%dT23:59:59Z")
from_date = (now - timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z")

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": GH_LOGIN, "from": from_date, "to": to_date}}).encode("utf-8"),
    headers={"Authorization": f"bearer {GITHUB_TOKEN}", "User-Agent": "Python"}
)

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        stats = res["data"]["user"]["contributionsCollection"]
        total = sum(stats.values())
except Exception as e:
    total = 0

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="80" viewBox="0 0 400 80">
  <rect width="100%" height="100%" fill="#0d1117" rx="6" stroke="#30363d" stroke-width="1" />
  <text x="20" y="35" fill="#58a6ff" font-family="monospace" font-size="14" font-weight="bold">Total Contributions (Past Year)</text>
  <text x="20" y="60" fill="#c9d1d9" font-family="monospace" font-size="20">{total:,}</text>
</svg>"""

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("Generated stats.svg successfully.")
