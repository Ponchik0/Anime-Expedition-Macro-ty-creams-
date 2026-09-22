"""Интерактивный дашборд аналитики Anime Expeditions Macro.

Объединяет:
1. Статистику загрузок и релизов из GitHub Releases API.
2. Трафик репозитория (просмотры и клоны за 14 дней).
3. Живую телеметрию онлайна и активности из Supabase (защищено секретным ключом разработчика).

Запуск:
    python tools/dashboard.py         # Выведет сводку в консоль и откроет HTML-дашборд
    python tools/dashboard.py --cli   # Только консольный вывод
"""
import json
import os
import subprocess
import sys
import urllib.request
import webbrowser

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_FILE = os.path.join(ROOT_DIR, "tools", "admin_secret.json")

SUPABASE_URL = "https://ifpnicjcpyissiqhwotq.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmcG5pY2pjcHlpc3NpcWh3b3RxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwODA3NjgsImV4cCI6MjEwNTY1Njc2OH0."
    "mX0YyBEoew5FmfjzYpnN7EWVL4NJG343lar6m_VycjI"
)
GITHUB_REPO = "Ponchik0/Anime-Expedition-Macro-ty-creams-"


def get_admin_secret() -> str:
    if os.path.isfile(SECRET_FILE):
        try:
            with open(SECRET_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("secret_key", "")
        except Exception:
            pass
    return ""


def get_git_token() -> str:
    try:
        p = subprocess.Popen(["git", "credential", "fill"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate("protocol=https\nhost=github.com\n\n")
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def fetch_github_releases():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    headers = {"User-Agent": "AEMacro-Analytics", "Accept": "application/vnd.github+json"}
    token = get_git_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        print(f"[!] GitHub API error: {exc}")
        return []


def fetch_github_traffic():
    token = get_git_token()
    if not token:
        return {"views": {"count": 0, "uniques": 0}, "clones": {"count": 0, "uniques": 0}}

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "AEMacro-Analytics",
        "Accept": "application/vnd.github+json"
    }
    traffic = {}
    for kind in ("views", "clones"):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/traffic/{kind}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                traffic[kind] = json.loads(resp.read().decode())
        except Exception:
            traffic[kind] = {"count": 0, "uniques": 0}
    return traffic


def fetch_live_telemetry():
    secret = get_admin_secret()
    if not secret:
        return {"error": "No admin secret configured in tools/admin_secret.json"}

    url = f"{SUPABASE_URL}/rest/v1/rpc/get_macro_analytics"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"p_secret_key": secret}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        return {"error": str(exc)}


def render_html_dashboard(telemetry, releases, traffic) -> str:
    total_downloads = 0
    release_rows = []
    for r in releases:
        tag = r.get("tag_name", "")
        assets = r.get("assets", [])
        rel_dl = sum(a.get("download_count", 0) for a in assets)
        total_downloads += rel_dl
        release_rows.append({
            "tag": tag,
            "published_at": r.get("published_at", "")[:10],
            "downloads": rel_dl,
            "assets": [{"name": a["name"], "count": a["download_count"], "size_mb": round(a["size"] / 1048576, 1)} for a in assets]
        })

    views_cnt = traffic.get("views", {}).get("count", 0)
    views_uniq = traffic.get("views", {}).get("uniques", 0)
    clones_cnt = traffic.get("clones", {}).get("count", 0)
    clones_uniq = traffic.get("clones", {}).get("uniques", 0)

    online_now = telemetry.get("online_now", 0)
    farming_now = telemetry.get("currently_farming", 0)
    active_today = telemetry.get("active_today", 0)
    total_clients = telemetry.get("total_clients", 0)
    avg_hours = telemetry.get("avg_total_hours", 0)
    max_hours = telemetry.get("max_total_hours", 0)
    total_runs = telemetry.get("total_runs", 0)
    versions = telemetry.get("versions", []) or []
    os_stats = telemetry.get("os_stats", []) or []
    recent_activity = telemetry.get("recent_activity", []) or []

    data_json = json.dumps({
        "telemetry": telemetry,
        "releases": release_rows,
        "total_downloads": total_downloads,
        "traffic": {"views": views_cnt, "views_uniq": views_uniq, "clones": clones_cnt, "clones_uniq": clones_uniq}
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Anime Expeditions Macro — Analytics Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="60">
  <style>
    :root {{
      --bg: #131417;
      --card-bg: #1c1d22;
      --card-border: #2b2d35;
      --header-bg: #18191e;
      --accent: #dcae6e;
      --accent-hover: #ebd494;
      --accent-dim: rgba(220, 174, 110, 0.12);
      --text: #c5c7d0;
      --text-head: #ffffff;
      --text-muted: #7e8294;
      --green: #6bc987;
      --green-dim: rgba(107, 201, 135, 0.12);
      --red: #e25c5c;
      --font: "Segoe UI Variable Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      font-size: 14px;
      line-height: 1.5;
      padding: 32px 24px;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 20px;
    }}
    .brand {{
      display: flex;
      flex-direction: column;
    }}
    .brand-eyebrow {{
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
    }}
    .brand-title {{
      font-size: 24px;
      font-weight: 700;
      color: var(--text-head);
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 8px var(--green);
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(1.15); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}
    .grid-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      position: relative;
    }}
    .card-label {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 6px;
    }}
    .card-value {{
      font-size: 28px;
      font-weight: 700;
      color: var(--text-head);
    }}
    .card-sub {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .card-accent {{
      color: var(--accent);
    }}
    .card-green {{
      color: var(--green);
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text-head);
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .section-title::before {{
      content: "";
      width: 4px;
      height: 16px;
      background: var(--accent);
      border-radius: 2px;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 28px;
    }}
    @media (max-width: 800px) {{
      .two-col {{ grid-template-columns: 1fr; }}
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th {{
      text-align: left;
      padding: 10px 14px;
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--card-border);
      background: rgba(0,0,0,0.15);
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .tag-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
      background: var(--accent-dim);
      color: var(--accent);
      border: 1px solid rgba(220,174,110,0.25);
    }}
    .online-tag {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 11px;
      background: var(--green-dim);
      color: var(--green);
    }}
    .farming-tag {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 11px;
      background: rgba(220,174,110,0.15);
      color: var(--accent);
    }}
    .bar-container {{
      width: 100%;
      height: 6px;
      background: rgba(255,255,255,0.06);
      border-radius: 3px;
      overflow: hidden;
      margin-top: 4px;
    }}
    .bar-fill {{
      height: 100%;
      background: var(--accent);
      border-radius: 3px;
    }}
    footer {{
      margin-top: 36px;
      text-align: center;
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px solid var(--card-border);
      padding-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <span class="brand-eyebrow">ANIME EXPEDITIONS MACRO</span>
        <h1 class="brand-title">Analytics & Telemetry Dashboard</h1>
      </div>
      <div class="status-badge">
        <div class="dot"></div>
        <span>Live System Status: <strong>Normal</strong></span>
      </div>
    </header>

    <!-- TOP CARDS -->
    <div class="grid-cards">
      <div class="card">
        <div class="card-label">Online Right Now</div>
        <div class="card-value card-green">{online_now}</div>
        <div class="card-sub">{farming_now} actively farming in Roblox</div>
      </div>
      <div class="card">
        <div class="card-label">Active Users (24h)</div>
        <div class="card-value">{active_today}</div>
        <div class="card-sub">Total unique clients: {total_clients}</div>
      </div>
      <div class="card">
        <div class="card-label">Avg Runtime Per User</div>
        <div class="card-value card-accent">{avg_hours} h</div>
        <div class="card-sub">Top farmer: {max_hours} hours</div>
      </div>
      <div class="card">
        <div class="card-label">Total Matches Played</div>
        <div class="card-value">{total_runs}</div>
        <div class="card-sub">Recorded across all users</div>
      </div>
      <div class="card">
        <div class="card-label">Total Downloads</div>
        <div class="card-value card-accent">{total_downloads}</div>
        <div class="card-sub">Across all {len(releases)} GitHub releases</div>
      </div>
      <div class="card">
        <div class="card-label">Repo Clones (14d)</div>
        <div class="card-value">{clones_cnt}</div>
        <div class="card-sub">{clones_uniq} unique developers / users</div>
      </div>
    </div>

    <!-- TWO COLUMN: VERSIONS & OS -->
    <div class="two-col">
      <div class="card">
        <div class="section-title">Active Versions</div>
        <table>
          <thead>
            <tr>
              <th>Version</th>
              <th>Total Users</th>
              <th>Active (24h)</th>
            </tr>
          </thead>
          <tbody>
            {"".join(f"<tr><td><span class='tag-badge'>{v.get('version')}</span></td><td>{v.get('count')}</td><td>{v.get('active_today')}</td></tr>" for v in versions) if versions else "<tr><td colspan='3' style='text-align:center; color:var(--text-muted);'>Telemetry data will appear as users launch v2.0.1+</td></tr>"}
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="section-title">Operating Systems</div>
        <table>
          <thead>
            <tr>
              <th>Platform</th>
              <th>Count</th>
              <th>Share</th>
            </tr>
          </thead>
          <tbody>
            {"".join(f"<tr><td>{o.get('os')}</td><td>{o.get('count')}</td><td>{round(o.get('count', 0) / max(1, total_clients) * 100)}%</td></tr>" for o in os_stats) if os_stats else "<tr><td colspan='3' style='text-align:center; color:var(--text-muted);'>No OS data yet</td></tr>"}
          </tbody>
        </table>
      </div>
    </div>

    <!-- GITHUB RELEASES BREAKDOWN -->
    <div class="card" style="margin-bottom: 28px;">
      <div class="section-title">GitHub Release Downloads</div>
      <table>
        <thead>
          <tr>
            <th>Release</th>
            <th>Date</th>
            <th>Total Downloads</th>
            <th>Asset Breakdown</th>
          </tr>
        </thead>
        <tbody>
          {"".join(f"<tr><td><span class='tag-badge'>{r['tag']}</span></td><td>{r['published_at']}</td><td><strong>{r['downloads']}</strong></td><td>" + " &bull; ".join(f"{a['name']}: {a['count']} dl" for a in r['assets']) + "</td></tr>" for r in release_rows)}
        </tbody>
      </table>
    </div>

    <!-- RECENT ACTIVITY TABLE -->
    <div class="card">
      <div class="section-title">Recent Anonymous Activity (Live Sessions)</div>
      <table>
        <thead>
          <tr>
            <th>Client ID</th>
            <th>Status</th>
            <th>Version</th>
            <th>OS</th>
            <th>Uptime</th>
            <th>Total Hours</th>
            <th>Matches</th>
            <th>Last Ping</th>
          </tr>
        </thead>
        <tbody>
          {"".join(f"<tr><td><code>{a.get('client_masked')}</code></td><td>" + ("<span class='farming-tag'>Farming</span>" if a.get('is_active') else ("<span class='online-tag'>Online</span>" if a.get('is_online') else "<span style='color:var(--text-muted);'>Idle</span>")) + f"</td><td><span class='tag-badge'>{a.get('version')}</span></td><td>{a.get('os')}</td><td>{a.get('uptime_minutes')}m</td><td><strong>{a.get('total_hours')}h</strong></td><td>{a.get('total_runs')}</td><td style='color:var(--text-muted);'>{a.get('last_ping')[:19].replace('T', ' ')}</td></tr>" for a in recent_activity) if recent_activity else "<tr><td colspan='8' style='text-align:center; color:var(--text-muted);'>No live sessions yet. Pings will display here automatically once v2.0.1 clients start up.</td></tr>"}
        </tbody>
      </table>
    </div>

    <footer>
      Anime Expeditions Macro &bull; Private Analytics Dashboard &bull; Access restricted to Ponchik0
    </footer>
  </div>
</body>
</html>"""
    return html


def print_cli_summary(telemetry, releases, traffic):
    print("\n" + "=" * 60)
    print("      ANIME EXPEDITIONS MACRO - ANALYTICS DASHBOARD")
    print("=" * 60)

    total_downloads = sum(sum(a.get("download_count", 0) for a in r.get("assets", [])) for r in releases)
    clones = traffic.get("clones", {}).get("count", 0)
    clones_u = traffic.get("clones", {}).get("uniques", 0)
    views = traffic.get("views", {}).get("count", 0)
    views_u = traffic.get("views", {}).get("uniques", 0)

    print("\n[GITHUB DOWNLOADS & TRAFFIC]")
    print(f"  * Total Release Downloads: {total_downloads}")
    print(f"  * Repo Clones (14d):        {clones} ({clones_u} unique users)")
    print(f"  * Repo Views (14d):         {views} ({views_u} unique visitors)")

    print("\n  Top Releases by Downloads:")
    for r in releases[:5]:
        tag = r.get("tag_name")
        c = sum(a.get("download_count", 0) for a in r.get("assets", []))
        print(f"    - {tag:<10}: {c:>4} downloads")

    if "error" in telemetry:
        print(f"\n[LIVE TELEMETRY]: {telemetry['error']}")
    else:
        print("\n[LIVE TELEMETRY]")
        print(f"  * Online Right Now:   {telemetry.get('online_now', 0)} (Farming: {telemetry.get('currently_farming', 0)})")
        print(f"  * Active Today (24h): {telemetry.get('active_today', 0)}")
        print(f"  * Total Clients:      {telemetry.get('total_clients', 0)}")
        print(f"  * Avg Hours Per User: {telemetry.get('avg_total_hours', 0)} hours")
        print(f"  * Max Hours Player:   {telemetry.get('max_total_hours', 0)} hours")
        print(f"  * Total Matches Run:  {telemetry.get('total_runs', 0)}")

    print("\n" + "=" * 60)


def main():
    print("[*] Fetching GitHub releases & traffic...")
    releases = fetch_github_releases()
    traffic = fetch_github_traffic()

    print("[*] Fetching live Supabase telemetry...")
    telemetry = fetch_live_telemetry()

    print_cli_summary(telemetry, releases, traffic)

    if "--cli" not in sys.argv:
        out_path = os.path.join(ROOT_DIR, "tools", "dashboard.html")
        html = render_html_dashboard(telemetry, releases, traffic)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n[+] Generated HTML Dashboard: {out_path}")
        print("[*] Opening in browser...")
        webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
