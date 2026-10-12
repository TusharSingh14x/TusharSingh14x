"""Generate a self-contained animated SVG from public GitHub repository data."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = "TusharSingh14x"
ROOT = Path(__file__).resolve().parent

def fetch_repos():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-card"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=100&page={page}"
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1

def text(value, limit):
    value = str(value or "")
    return escape(value if len(value) <= limit else value[:limit-1] + "…")

def render(repos, refreshed):
    projects = sorted(
        (r for r in repos if not r.get("fork") and not r.get("private")
         and r["name"].lower() != USER.lower() and r.get("pushed_at")),
        key=lambda r: r["pushed_at"], reverse=True
    )[:3]
    rows = []
    for i, repo in enumerate(projects):
        y = 182 + i * 69
        date = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).strftime("%d %b %Y")
        rows.append(f"""
        <g>
          <text x="36" y="{y}" class="index">0{i+1}</text>
          <text x="84" y="{y}" class="repo">{text(repo["name"], 38)}</text>
          <text x="84" y="{y+22}" class="meta">{text(repo.get("language") or "No language reported", 26)}</text>
          <text x="784" y="{y}" text-anchor="end" class="meta">{date}</text>
          <path d="M84 {y+37} H784" class="rule"/>
        </g>""")
    if not rows:
        rows.append('<text x="36" y="200" class="meta">No public project pushes to display yet.</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="820" height="430" viewBox="0 0 820 430" role="img" aria-labelledby="title desc">
    <title id="title">Recent public projects by Tushar Singh</title>
    <desc id="desc">Latest pushes to public repositories, excluding forks and the profile repository. Refreshed {refreshed} UTC.</desc>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }}
      .label {{font-family: monospace; font-size:12px; letter-spacing:2px; fill:#93a4b7}}
      .heading {{font-size:31px; font-weight:600; fill:#edf2f7}}
      .repo {{font-size:19px; font-weight:500; fill:#edf2f7}}
      .meta {{font-size:13px; fill:#a7b6c8}}
      .index {{font-family:monospace; font-size:13px; fill:#7ca9e8}}
      .rule {{stroke:#253245; stroke-width:1}}
      .scan {{animation:scan 7s ease-in-out infinite}}
      @keyframes scan {{0%,100% {{transform:translateX(0); opacity:.35}} 50% {{transform:translateX(568px);opacity:1}}}}
      @media (prefers-reduced-motion: reduce) {{.scan {{animation:none}}}}
    </style>
    <rect x="1" y="1" width="818" height="428" rx="16" fill="#0d131c" stroke="#253245"/>
    <text x="36" y="42" class="label">TUSHAR / DEVELOPMENT NOTES</text>
    <text x="36" y="89" class="heading">Recent work.</text>
    <text x="36" y="115" class="meta">Latest pushes to public repositories</text>
    <path d="M36 139 H784" class="rule"/>
    <rect x="36" y="138" width="180" height="2" rx="1" fill="#7ca9e8" class="scan"/>
    {''.join(rows)}
    <text x="36" y="396" class="label">GITHUB / PUBLIC DATA</text>
    <text x="784" y="396" text-anchor="end" class="meta">Refreshed {refreshed} UTC</text>
    </svg>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, help="Use a saved public API response for local preview.")
    args = parser.parse_args()
    repos = json.loads(args.data.read_text()) if args.data else fetch_repos()
    if not isinstance(repos, list):
        raise ValueError("Expected a GitHub repository list; keeping the previous card.")
    now = datetime.now(timezone.utc).strftime("%d %b %Y")
    svg = render(repos, now)
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)
    temporary = ROOT / "activity.svg.tmp"
    temporary.write_text(svg, encoding="utf-8")
    temporary.replace(ROOT / "activity.svg")

if __name__ == "__main__":
    main()
