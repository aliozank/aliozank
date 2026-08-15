#!/usr/bin/env python3
"""Generate every SVG used by the aliozank GitHub profile README.

The renderer intentionally uses only the Python standard library and SVG
features that work when the file is loaded as an image by GitHub.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CONFIG_PATH = ROOT / "profile.config.json"

FALLBACK_ACTIVE = {
    "2026-05-18": 1,
    "2026-05-19": 1,
    "2026-05-20": 1,
    "2026-05-24": 1,
    "2026-07-23": 4,
    "2026-07-24": 3,
    "2026-07-26": 4,
    "2026-07-27": 1,
    "2026-07-29": 1,
    "2026-08-04": 1,
    "2026-08-05": 1,
    "2026-08-11": 1,
}


@dataclass
class ProfileStats:
    contributions: int = 39
    public_repos: int = 3
    followers: int = 4
    active: dict[str, int] | None = None
    updated: str = "2026-08-15"

    def __post_init__(self) -> None:
        if self.active is None:
            self.active = dict(FALLBACK_ACTIVE)


def load_config() -> dict[str, str]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def request_text(url: str, token: str | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aliozank-profile-art/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def fetch_stats(username: str, offline: bool) -> ProfileStats:
    stats = ProfileStats(updated=date.today().isoformat())
    if offline:
        return stats

    token = os.environ.get("GITHUB_TOKEN")
    try:
        contribution_html = request_text(
            f"https://github.com/users/{username}/contributions"
        )
        active: dict[str, int] = {}
        for tag in re.findall(r"<td\b[^>]*ContributionCalendar-day[^>]*>", contribution_html):
            day_match = re.search(r'data-date="([0-9-]+)"', tag)
            level_match = re.search(r'data-level="([0-4])"', tag)
            if day_match and level_match and int(level_match.group(1)):
                active[day_match.group(1)] = int(level_match.group(1))

        total_match = re.search(
            r"([0-9][0-9,]*)\s+contributions?\s+in\s+the\s+last\s+year",
            contribution_html,
            re.IGNORECASE,
        )
        if total_match:
            stats.contributions = int(total_match.group(1).replace(",", ""))
        if active:
            stats.active = active
    except Exception as exc:  # A stale-but-valid panel is better than a broken workflow.
        print(f"warning: contribution refresh failed: {exc}")

    try:
        payload = json.loads(
            request_text(f"https://api.github.com/users/{username}", token=token)
        )
        stats.public_repos = int(payload.get("public_repos", stats.public_repos))
        stats.followers = int(payload.get("followers", stats.followers))
    except Exception as exc:
        print(f"warning: profile stats refresh failed: {exc}")

    return stats


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


COMMON_CSS = r"""
    text { font-family: 'Segoe UI', Inter, Arial, sans-serif; }
    .mono { font-family: 'Cascadia Code', 'SFMono-Regular', Consolas, monospace; }
    .kicker { fill: #d2bdff; font-size: 13px; font-weight: 700; letter-spacing: 3px; }
    .display { fill: #f8f4ff; font-weight: 800; letter-spacing: -1px; }
    .copy { fill: #b8a9cc; font-size: 16px; }
    .muted { fill: #7c6d92; }
    .fine { fill: #9281aa; font-size: 11px; letter-spacing: 1.6px; }
    .label { fill: #c8b9db; font-size: 12px; font-weight: 700; letter-spacing: 1.3px; }
    .value { fill: #faf6ff; font-size: 22px; font-weight: 800; }
    .hairline { stroke: #342744; stroke-width: 1; }
    .cyan-line { stroke: #d2bdff; stroke-width: 1.5; fill: none; }
    .green-line { stroke: #efa9ff; stroke-width: 1.5; fill: none; }
    .violet-line { stroke: #9f7aea; stroke-width: 1.5; fill: none; }
    [fill="#2dd4ff"] { fill: #d2bdff; }
    [stroke="#2dd4ff"] { stroke: #d2bdff; }
    [fill="#55e6a5"] { fill: #efa9ff; }
    [stroke="#55e6a5"] { stroke: #efa9ff; }
    [fill="#9b7cff"] { fill: #9f7aea; }
    [stroke="#9b7cff"] { stroke: #9f7aea; }
    [fill="#ffb454"] { fill: #e4c7ff; }
    [stroke="#ffb454"] { stroke: #e4c7ff; }
    [fill="#0b1420"], [fill="#08111c"], [fill="#09151e"], [fill="#09131e"],
    [fill="#08131d"], [fill="#0a1a25"], [fill="#08141b"], [fill="#08131f"],
    [fill="#0a1420"], [fill="#09161b"] { fill: #130c1d; }
    [stroke="#1d3048"], [stroke="#1c2b40"], [stroke="#1b3348"],
    [stroke="#21445e"], [stroke="#24364e"] { stroke: #49355f; }
    .route { stroke-dasharray: 7 10; animation: route 4s linear infinite; }
    .route-fast { stroke-dasharray: 5 8; animation: route 2.4s linear infinite; }
    .pulse { animation: pulse 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
    .pulse2 { animation: pulse 2.6s ease-in-out 1.3s infinite; transform-box: fill-box; transform-origin: center; }
    .twinkle { animation: twinkle 3.4s ease-in-out infinite; }
    .spin { animation: spin 22s linear infinite; transform-box: fill-box; transform-origin: center; }
    .spin-reverse { animation: spin-reverse 30s linear infinite; transform-box: fill-box; transform-origin: center; }
    .scan { animation: scan 8s linear infinite; }
    .bar { animation: breathe 3s ease-in-out infinite; transform-origin: left; }
    @keyframes route { to { stroke-dashoffset: -68; } }
    @keyframes pulse { 0%,100% { opacity:.45; transform:scale(.86); } 50% { opacity:1; transform:scale(1.12); } }
    @keyframes twinkle { 0%,100% { opacity:.15; } 50% { opacity:.85; } }
    @keyframes spin { to { transform:rotate(360deg); } }
    @keyframes spin-reverse { to { transform:rotate(-360deg); } }
    @keyframes scan { 0% { transform:translateY(-120px); opacity:0; } 15%,85% { opacity:.32; } 100% { transform:translateY(650px); opacity:0; } }
    @keyframes breathe { 0%,100% { opacity:.62; } 50% { opacity:1; } }
    @media (prefers-reduced-motion: reduce) {
      .route,.route-fast,.pulse,.pulse2,.twinkle,.spin,.spin-reverse,.scan,.bar { animation:none !important; }
    }
"""


def svg_document(height: int, title: str, description: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">
  <title id="title">{esc(title)}</title>
  <desc id="desc">{esc(description)}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#08060d"/><stop offset="0.52" stop-color="#100a18"/><stop offset="1" stop-color="#07050c"/>
    </linearGradient>
    <linearGradient id="cyanViolet" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#d7c3ff"/><stop offset="1" stop-color="#9f7aea"/>
    </linearGradient>
    <linearGradient id="cyanGreen" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#d7c3ff"/><stop offset="1" stop-color="#f0a6ff"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#d7c3ff" stop-opacity=".8"/><stop offset="1" stop-color="#d7c3ff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="orb" cx="45%" cy="38%" r="62%">
      <stop offset="0" stop-color="#35224f"/><stop offset=".48" stop-color="#1b1129"/><stop offset="1" stop-color="#08060d"/>
    </radialGradient>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="#4a3563" stroke-width="1" opacity=".24"/>
    </pattern>
    <pattern id="microgrid" width="8" height="8" patternUnits="userSpaceOnUse">
      <path d="M8 0H0V8" fill="none" stroke="#d2bdff" stroke-width=".35" opacity=".14"/>
    </pattern>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="11" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="shadow" x="-20%" y="-30%" width="140%" height="160%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000" flood-opacity=".6"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0 0L10 5L0 10Z" fill="#d2bdff"/>
    </marker>
    <clipPath id="frameClip"><rect x="1" y="1" width="998" height="{height - 2}" rx="24"/></clipPath>
    <style>{COMMON_CSS}</style>
  </defs>
  <g clip-path="url(#frameClip)">
    <rect width="1000" height="{height}" fill="url(#bg)"/>
    <rect width="1000" height="{height}" fill="url(#grid)"/>
    <path d="M0 0H430L260 {height}H0Z" fill="#140c1f" opacity=".62"/>
    <rect class="scan" x="0" y="0" width="1000" height="2" fill="url(#fade)"/>
    {body}
  </g>
  <rect x="1" y="1" width="998" height="{height - 2}" rx="24" fill="none" stroke="#342744" stroke-width="2"/>
  <path d="M24 1H180" stroke="#d2bdff" stroke-width="2"/>
  <path d="M820 {height - 1}H976" stroke="#9f7aea" stroke-width="2"/>
</svg>
'''


def pill(x: int, y: int, width: int, label: str, accent: str = "#d2bdff") -> str:
    return f'''<g>
      <rect x="{x}" y="{y}" width="{width}" height="34" rx="17" fill="#0b1420" stroke="{accent}" stroke-opacity=".42"/>
      <circle cx="{x + 17}" cy="{y + 17}" r="3.5" fill="{accent}" filter="url(#glow)"/>
      <text class="mono label" x="{x + 29}" y="{y + 22}">{esc(label)}</text>
    </g>'''


def render_hero(config: dict[str, str], stats: ProfileStats) -> str:
    stars = []
    coords = [(704, 65), (737, 96), (914, 69), (847, 118), (958, 179), (679, 205),
              (891, 263), (730, 318), (945, 344), (805, 375), (664, 407), (922, 440)]
    for index, (x, y) in enumerate(coords):
        delay = (index % 5) * 0.55
        stars.append(
            f'<circle class="twinkle" style="animation-delay:{delay}s" cx="{x}" cy="{y}" r="1.8" fill="#bfefff"/>'
        )

    body = f'''
    <circle cx="815" cy="214" r="248" fill="#2b183e" opacity=".22" filter="url(#softGlow)"/>
    <g opacity=".62">{''.join(stars)}</g>
    <path class="cyan-line route" d="M590 410C690 346 682 143 806 100S960 105 991 46" opacity=".25"/>
    <path class="violet-line route-fast" d="M648 456C720 378 835 397 916 300S945 137 1008 119" opacity=".22"/>

    <text class="mono kicker" x="58" y="56">AOK // ENGINEERING PROFILE</text>
    <g transform="translate(58 78)">
      <circle class="pulse" cx="6" cy="6" r="5" fill="#efa9ff" filter="url(#glow)"/>
      <text class="mono fine" x="19" y="10" fill="#efa9ff">SYSTEM ONLINE</text>
      <text class="mono fine" x="168" y="10">TR / UTC+3</text>
      <text class="mono fine" x="292" y="10">BUILD 2026</text>
    </g>

    <text class="display" x="54" y="176" font-size="59">{esc(config['name']).upper()}</text>
    <rect x="57" y="198" width="492" height="3" rx="2" fill="url(#cyanViolet)" filter="url(#glow)"/>
    <text class="mono" x="58" y="242" fill="#dbe9fb" font-size="22" font-weight="700" letter-spacing="2.2">{esc(config['role'])}</text>
    <text class="copy" x="58" y="281">{esc(config['tagline'])}</text>

    {pill(58, 312, 170, 'SYSTEM DESIGN')}
    {pill(242, 312, 178, 'EVENT-DRIVEN', '#9f7aea')}
    {pill(434, 312, 174, 'OBSERVABILITY', '#efa9ff')}

    <g transform="translate(814 214)">
      <circle r="134" fill="url(#orb)" stroke="#21445e" stroke-width="1.5" filter="url(#shadow)"/>
      <circle r="110" fill="url(#microgrid)" opacity=".7"/>
      <circle class="spin" r="151" fill="none" stroke="#2dd4ff" stroke-opacity=".38" stroke-width="1.5" stroke-dasharray="2 11"/>
      <circle class="spin-reverse" r="168" fill="none" stroke="#9b7cff" stroke-opacity=".28" stroke-width="1" stroke-dasharray="23 14 4 14"/>
      <path d="M-87 48C-36-62 48-90 96-20" fill="none" stroke="#2dd4ff" stroke-opacity=".46" stroke-width="1.5"/>
      <path d="M-104-23C-24 29 31 65 102 42" fill="none" stroke="#9b7cff" stroke-opacity=".38"/>
      <circle class="pulse" cx="-87" cy="48" r="6" fill="#2dd4ff"/>
      <circle class="pulse2" cx="96" cy="-20" r="6" fill="#55e6a5"/>
      <circle cx="102" cy="42" r="4" fill="#9b7cff"/>
      <text class="mono" text-anchor="middle" y="14" fill="#f4f8ff" font-size="52" font-weight="800" letter-spacing="3">AOK</text>
      <text class="mono fine" text-anchor="middle" y="43">BACKEND CONTROL</text>
    </g>

    <line x1="58" y1="390" x2="942" y2="390" class="hairline"/>
    <text class="mono fine" x="58" y="418">CURRENT VECTOR</text>
    <g transform="translate(58 439)">
      <text class="value" x="0" y="0">{stats.public_repos:02d}</text><text class="mono fine" x="39" y="-2">PUBLIC REPOS</text>
      <line x1="182" y1="-21" x2="182" y2="17" class="hairline"/>
      <text class="value" x="214" y="0">{stats.contributions}</text><text class="mono fine" x="269" y="-2">YEARLY SIGNALS</text>
      <line x1="438" y1="-21" x2="438" y2="17" class="hairline"/>
      <text class="value" x="470" y="0">15</text><text class="mono fine" x="506" y="-2">ENGINEERING LABS</text>
      <line x1="668" y1="-21" x2="668" y2="17" class="hairline"/>
      <text class="value" x="700" y="0">{stats.followers:02d}</text><text class="mono fine" x="740" y="-2">PEOPLE TUNED IN</text>
    </g>
    <text class="mono fine" x="58" y="494">github.com/{esc(config['username'])}</text>
    <text class="mono fine" x="942" y="494" text-anchor="end">SCROLL TO ENTER THE SYSTEM ↓</text>
    '''
    return svg_document(520, f"{config['name']} — engineering profile", config["tagline"], body)


def render_manifesto(config: dict[str, str]) -> str:
    body = f'''
    <text class="mono kicker" x="58" y="55">01 // OPERATING PRINCIPLES</text>
    <text class="display" x="55" y="114" font-size="42">I BUILD THE BACKEND</text>
    <text class="display" x="55" y="160" font-size="42" fill="url(#cyanGreen)">BENEATH THE INTERFACE.</text>
    <text class="copy" x="58" y="207">From domain rules to event streams, I turn complex operations</text>
    <text class="copy" x="58" y="233">into systems that can be understood, tested and observed.</text>

    <g transform="translate(575 58)">
      <rect width="367" height="245" rx="18" fill="#08111c" stroke="#1d3048" filter="url(#shadow)"/>
      <text class="mono fine" x="24" y="32">REQUEST LIFECYCLE // LIVE TRACE</text>
      <line x1="52" y1="66" x2="52" y2="205" stroke="#24364e" stroke-width="2"/>
      <path class="cyan-line route-fast" d="M52 66V205"/>
      <g>
        <circle class="pulse" cx="52" cy="70" r="6" fill="#2dd4ff"/>
        <text class="mono label" x="76" y="75">01 / VALIDATE THE DOMAIN</text>
        <circle class="pulse2" cx="52" cy="114" r="6" fill="#9b7cff"/>
        <text class="mono label" x="76" y="119">02 / PERSIST THE TRUTH</text>
        <circle class="pulse" cx="52" cy="158" r="6" fill="#55e6a5"/>
        <text class="mono label" x="76" y="163">03 / PUBLISH THE EVENT</text>
        <circle class="pulse2" cx="52" cy="202" r="6" fill="#ffb454"/>
        <text class="mono label" x="76" y="207">04 / OBSERVE THE OUTCOME</text>
      </g>
    </g>

    <g transform="translate(58 273)">
      <text class="mono fine" x="0" y="0">DESIGN FOR</text>
      <text class="mono label" x="0" y="28" fill="#eef6ff">FAILURE</text>
      <line x1="120" y1="-11" x2="120" y2="38" class="hairline"/>
      <text class="mono fine" x="153" y="0">OPTIMIZE FOR</text>
      <text class="mono label" x="153" y="28" fill="#eef6ff">CLARITY</text>
      <line x1="298" y1="-11" x2="298" y2="38" class="hairline"/>
      <text class="mono fine" x="331" y="0">SHIP WITH</text>
      <text class="mono label" x="331" y="28" fill="#eef6ff">EVIDENCE</text>
    </g>
    <text class="mono fine" x="942" y="337" text-anchor="end">ALI OZAN KARAÇOR // {esc(config['location']).upper()}</text>
    '''
    return svg_document(360, "Engineering operating principles", "A concise engineering manifesto and request lifecycle", body)


def render_projects(config: dict[str, str]) -> str:
    body = f'''
    <text class="mono kicker" x="58" y="53">02 // SELECTED WORK</text>
    <text class="display" x="55" y="103" font-size="42">A FEW SYSTEMS. ZERO FILLER.</text>
    <text class="copy" x="58" y="137">Enough context to choose a door. The repositories hold the details.</text>

    <g transform="translate(55 169)">
      <rect width="555" height="218" rx="20" fill="#130c1d" stroke="#d2bdff" stroke-opacity=".46" filter="url(#shadow)"/>
      <rect x="0" y="0" width="5" height="218" rx="3" fill="url(#cyanViolet)"/>
      <text class="mono kicker" x="28" y="35">FLAGSHIP // ACTIVE</text>
      <text class="display" x="28" y="78" font-size="28">FLIGHT MANAGEMENT SYSTEM</text>
      <text class="copy" x="28" y="111" font-size="14">Event-driven airline operations platform built as</text>
      <text class="copy" x="28" y="134" font-size="14">a full-stack microservice system.</text>
      <g transform="translate(28 158)">
        <rect width="99" height="34" rx="17" fill="#1b1228" stroke="#d2bdff" stroke-opacity=".34"/>
        <text class="mono fine" x="49" y="22" text-anchor="middle">JAVA 17</text>
        <rect x="111" width="116" height="34" rx="17" fill="#1b1228" stroke="#b590ff" stroke-opacity=".34"/>
        <text class="mono fine" x="169" y="22" text-anchor="middle">SPRING BOOT</text>
        <rect x="239" width="91" height="34" rx="17" fill="#1b1228" stroke="#efa9ff" stroke-opacity=".34"/>
        <text class="mono fine" x="284" y="22" text-anchor="middle">KAFKA</text>
        <path class="violet-line route-fast" d="M355 17H490"/>
        <text class="mono fine" x="490" y="22" text-anchor="end">OPEN REPO ↗</text>
      </g>
      <circle class="pulse" cx="521" cy="34" r="6" fill="#efa9ff"/>
    </g>

    <g transform="translate(632 169)">
      <rect width="310" height="101" rx="18" fill="#130c1d" stroke="#9f7aea" stroke-opacity=".42"/>
      <text class="mono kicker" x="22" y="30">UYS LABS // 15 TRACKS</text>
      <text class="mono label" x="22" y="56" fill="#f4efff">FOCUSED ENGINEERING LABS</text>
      <text class="mono fine" x="22" y="79">FROM REST AND JPA TO KAFKA AND CI/CD</text>
    </g>

    <g transform="translate(632 286)">
      <rect width="310" height="101" rx="18" fill="#130c1d" stroke="#efa9ff" stroke-opacity=".38"/>
      <text class="mono kicker" x="22" y="30">JAVA NOTES // FOUNDATION</text>
      <text class="mono label" x="22" y="56" fill="#f4efff">BACKEND PRACTICE</text>
      <text class="mono fine" x="22" y="79">CORE JAVA · OOP · COLLECTIONS</text>
    </g>

    <line x1="58" y1="419" x2="942" y2="419" class="hairline"/>
    <text class="mono fine" x="58" y="441">BUILD → LEARN → COMPOSE</text>
    <text class="mono fine" x="942" y="441" text-anchor="end">github.com/{esc(config['username'])}?tab=repositories</text>
    '''
    return svg_document(
        455,
        "Selected work",
        "Three concise project cards for Flight Management System, UYS Labs and Java Notes",
        body,
    )


def render_architecture(config: dict[str, str]) -> str:
    body = f'''
    <text class="mono kicker" x="58" y="53">02 // FLAGSHIP SYSTEM</text>
    <text class="display" x="55" y="101" font-size="37">FLIGHT OPERATIONS // EVENT-DRIVEN</text>
    <text class="mono fine" x="942" y="51" text-anchor="end">ACTIVE DEVELOPMENT</text>
    <circle class="pulse" cx="924" cy="77" r="5" fill="#55e6a5"/>
    <text class="mono fine" x="912" y="81" text-anchor="end" fill="#55e6a5">3 SERVICES / 4 DATA PATHS</text>

    <rect x="38" y="121" width="924" height="392" rx="22" fill="#060b12" stroke="#1c2b40"/>
    <text class="mono fine" x="62" y="147">SYSTEM TOPOLOGY / LIVE EVENT TRACE</text>
    <text class="mono fine" x="938" y="147" text-anchor="end">CLICK PANEL → OPEN REPOSITORY</text>

    <!-- moving routes live behind the system nodes -->
    <path class="cyan-line route-fast" d="M265 216H338" marker-end="url(#arrow)"/>
    <path class="cyan-line route" d="M568 205H638" marker-end="url(#arrow)"/>
    <path class="violet-line route" d="M455 262V297" marker-end="url(#arrow)"/>
    <path class="green-line route-fast" d="M568 226C606 226 607 297 645 297" marker-end="url(#arrow)"/>
    <path class="cyan-line route" d="M568 347C610 347 607 312 645 312" marker-end="url(#arrow)"/>
    <path class="violet-line route-fast" d="M776 213V363" marker-end="url(#arrow)"/>
    <path class="cyan-line route" d="M825 402H842" marker-end="url(#arrow)"/>
    <path class="green-line route" d="M458 407V454H645" marker-end="url(#arrow)"/>
    <path class="green-line route" d="M776 421V454" marker-end="url(#arrow)"/>

    <!-- operations interface -->
    <g transform="translate(62 174)">
      <rect width="203" height="84" rx="14" fill="#091724" stroke="#2dd4ff" stroke-opacity=".5" filter="url(#shadow)"/>
      <rect x="16" y="17" width="42" height="42" rx="9" fill="#102b36" stroke="#2dd4ff" stroke-opacity=".4"/>
      <path d="M27 46L37 27L47 46Z" fill="none" stroke="#55e6a5" stroke-width="2"/>
      <text class="mono label" x="72" y="33">VUE 3 CONTROL DECK</text>
      <text class="mono fine" x="72" y="55">PINIA / WEBSOCKET / MAPS</text>
      <text class="mono fine" x="16" y="73" fill="#55e6a5">OPERATOR CHANNEL ONLINE</text>
    </g>

    <!-- primary services -->
    <g transform="translate(338 165)">
      <rect width="230" height="97" rx="14" fill="#0a1521" stroke="#2dd4ff" stroke-opacity=".55" filter="url(#shadow)"/>
      <text class="mono fine" x="18" y="25">CORE SERVICE / JAVA 17</text>
      <text class="mono" x="18" y="53" fill="#f3f8ff" font-size="18" font-weight="800">FLIGHT SERVICE</text>
      <text class="mono fine" x="18" y="78">JWT · VERSIONING · ACTIVITY LOG</text>
      <circle class="pulse" cx="207" cy="23" r="5" fill="#55e6a5"/>
    </g>
    <g transform="translate(338 297)">
      <rect width="230" height="110" rx="14" fill="#0a1521" stroke="#9b7cff" stroke-opacity=".55" filter="url(#shadow)"/>
      <text class="mono fine" x="18" y="25">DOMAIN CATALOG / JAVA 17</text>
      <text class="mono" x="18" y="53" fill="#f3f8ff" font-size="17" font-weight="800">REFERENCE MANAGER</text>
      <text class="mono fine" x="18" y="78">AIRPORT · AIRCRAFT · ROUTE</text>
      <text class="mono fine" x="18" y="96">AIRLINE · FLIGHT TYPE</text>
      <circle class="pulse2" cx="207" cy="23" r="5" fill="#9b7cff"/>
    </g>

    <!-- event fabric and stores -->
    <g transform="translate(645 173)">
      <rect width="289" height="80" rx="14" fill="#0b151f" stroke="#ffb454" stroke-opacity=".58" filter="url(#shadow)"/>
      <text class="mono fine" x="18" y="24">EVENT FABRIC</text>
      <text class="mono" x="18" y="52" fill="#f5f8ff" font-size="19" font-weight="800">APACHE KAFKA</text>
      <path class="route-fast" d="M183 27H258" fill="none" stroke="#ffb454" stroke-width="2"/>
      <circle class="pulse" cx="199" cy="50" r="4" fill="#ffb454"/>
      <circle class="pulse2" cx="230" cy="50" r="4" fill="#ffb454"/>
      <circle class="pulse" cx="261" cy="50" r="4" fill="#ffb454"/>
    </g>
    <g transform="translate(645 276)">
      <rect width="137" height="64" rx="12" fill="#08141b" stroke="#55e6a5" stroke-opacity=".45"/>
      <text class="mono fine" x="16" y="23">HOT PATH</text>
      <text class="mono label" x="16" y="46" fill="#eafbf4">REDIS CACHE</text>
    </g>
    <g transform="translate(797 276)">
      <rect width="137" height="64" rx="12" fill="#08131f" stroke="#2dd4ff" stroke-opacity=".45"/>
      <text class="mono fine" x="16" y="23">PRIMARY DATA</text>
      <text class="mono label" x="16" y="46" fill="#eef8ff">MYSQL</text>
    </g>
    <g transform="translate(645 363)">
      <rect width="180" height="68" rx="12" fill="#0a1420" stroke="#9b7cff" stroke-opacity=".48"/>
      <text class="mono fine" x="16" y="23">EVENT CONSUMER</text>
      <text class="mono label" x="16" y="47" fill="#f1ecff">ARCHIVE SERVICE</text>
    </g>
    <g transform="translate(842 363)">
      <rect width="92" height="68" rx="12" fill="#08131f" stroke="#2dd4ff" stroke-opacity=".45"/>
      <text class="mono fine" x="12" y="23">COLD DATA</text>
      <text class="mono label" x="12" y="47">POSTGRES</text>
    </g>
    <g transform="translate(645 452)">
      <rect width="289" height="42" rx="12" fill="#09161b" stroke="#55e6a5" stroke-opacity=".38"/>
      <circle class="pulse" cx="20" cy="21" r="4" fill="#55e6a5"/>
      <text class="mono label" x="34" y="26">PROMETHEUS → GRAFANA / OBSERVE</text>
    </g>

    <g transform="translate(58 548)">
      <text class="mono fine" x="0" y="0">CAPABILITIES</text>
      <text class="mono label" x="0" y="25">CSV BULK IMPORT</text>
      <text class="mono label" x="189" y="25">ROLE-BASED ACCESS</text>
      <text class="mono label" x="405" y="25">REAL-TIME UPDATES</text>
      <text class="mono label" x="611" y="25">TESTCONTAINERS</text>
      <text class="mono label" x="798" y="25">DOCKER COMPOSE</text>
    </g>
    '''
    return svg_document(
        600,
        "Flight Management System architecture",
        "Animated system topology for the Java, Spring Boot, Kafka, Redis and Vue flagship project",
        body,
    )


def lab_chip(x: int, y: int, width: int, number: int, name: str, color: str) -> str:
    return f'''<g transform="translate({x} {y})">
      <rect width="{width}" height="48" rx="12" fill="#09131e" stroke="{color}" stroke-opacity=".34"/>
      <circle cx="20" cy="24" r="10" fill="{color}" fill-opacity=".13" stroke="{color}" stroke-opacity=".7"/>
      <path d="M15 24l3 3 7-8" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <text class="mono fine" x="39" y="19">{number:02d}</text>
      <text class="mono" x="39" y="35" fill="#cdd9e8" font-size="10.5" font-weight="700">{esc(name)}</text>
    </g>'''


def render_labs(config: dict[str, str]) -> str:
    rows = [
        ("FOUNDATIONS", "#2dd4ff", ["MOCK DATA", "REST", "JPA", "LIQUIBASE", "MAPSTRUCT"]),
        ("DISTRIBUTED", "#9b7cff", ["JWT", "REDIS", "KAFKA", "MICROSERVICES", "ARCHIVE"]),
        ("DELIVERY", "#55e6a5", ["VUE 3", "WEBSOCKET", "TESTING", "CONTAINERS", "OBSERVE / CI"]),
    ]
    chips: list[str] = []
    number = 1
    for row_index, (row_name, color, names) in enumerate(rows):
        y = 186 + row_index * 72
        chips.append(f'<text class="mono fine" x="58" y="{y + 29}" fill="{color}">{row_name}</text>')
        chips.append(f'<line x1="147" y1="{y + 24}" x2="172" y2="{y + 24}" stroke="{color}" stroke-opacity=".45"/>')
        for index, name in enumerate(names):
            chips.append(lab_chip(183 + index * 153, y, 140, number, name, color))
            if index < len(names) - 1:
                chips.append(
                    f'<path class="route" d="M{323 + index * 153} {y + 24}H{336 + index * 153}" stroke="{color}" stroke-width="1"/>'
                )
            number += 1

    body = f'''
    <text class="mono kicker" x="58" y="53">03 // ENGINEERING LABS</text>
    <text class="display" x="55" y="103" font-size="40">15 LABS. ONE PRODUCTION SYSTEM.</text>
    <text class="copy" x="58" y="137">Small, isolated experiments — composed into the flagship architecture above.</text>
    <g transform="translate(789 39)">
      <rect width="153" height="102" rx="16" fill="#09151e" stroke="#55e6a5" stroke-opacity=".38"/>
      <text class="mono fine" x="18" y="25">LEARNING VECTOR</text>
      <text class="mono" x="18" y="64" fill="#f4f8ff" font-size="31" font-weight="800">15 / 15</text>
      <text class="mono fine" x="18" y="86" fill="#55e6a5">TRACKS COMPLETE</text>
    </g>
    {''.join(chips)}
    <line x1="58" y1="410" x2="942" y2="410" class="hairline"/>
    <text class="mono fine" x="58" y="431">LAB → VERIFY → COMPOSE → SHIP</text>
    <text class="mono fine" x="942" y="431" text-anchor="end">github.com/{esc(config['username'])}/{esc(config['labs_repo'])}</text>
    '''
    return svg_document(455, "UYS engineering labs", "Fifteen completed backend learning tracks", body)


def stack_card(x: int, y: int, title: str, color: str, lines: list[str]) -> str:
    line_text = []
    for index, line in enumerate(lines):
        line_text.append(
            f'<text class="mono" x="20" y="{58 + index * 23}" fill="#c7d3e3" font-size="12.5">{esc(line)}</text>'
        )
    return f'''<g transform="translate({x} {y})">
      <rect width="278" height="128" rx="16" fill="#09131e" stroke="{color}" stroke-opacity=".34"/>
      <rect x="0" y="0" width="4" height="128" rx="2" fill="{color}"/>
      <text class="mono kicker" x="20" y="28" fill="{color}">{esc(title)}</text>
      {''.join(line_text)}
    </g>'''


def render_arsenal() -> str:
    body = f'''
    <text class="mono kicker" x="58" y="53">03 // SYSTEM ARSENAL</text>
    <text class="display" x="55" y="101" font-size="34">TOOLS ARE SECONDARY. SYSTEMS THINKING IS CORE.</text>
    <text class="copy" x="58" y="136">A production-oriented stack spanning domain logic, data flow, delivery and proof.</text>

    <g transform="translate(225 298)">
      <circle r="135" fill="#08131d" stroke="#1b3348" filter="url(#shadow)"/>
      <circle class="spin" r="113" fill="none" stroke="#2dd4ff" stroke-opacity=".32" stroke-width="1.5" stroke-dasharray="4 10"/>
      <circle class="spin-reverse" r="88" fill="none" stroke="#9b7cff" stroke-opacity=".38" stroke-width="1.2" stroke-dasharray="18 12"/>
      <circle r="57" fill="url(#orb)" stroke="#55e6a5" stroke-opacity=".45"/>
      <text class="mono" text-anchor="middle" y="-4" fill="#f5f8ff" font-size="22" font-weight="800">JAVA 17</text>
      <text class="mono fine" text-anchor="middle" y="20">SPRING BOOT</text>
      <g class="pulse"><circle cx="0" cy="-113" r="7" fill="#2dd4ff"/><text class="mono fine" text-anchor="middle" y="-127">REST</text></g>
      <g class="pulse2"><circle cx="104" cy="44" r="7" fill="#9b7cff"/><text class="mono fine" x="119" y="48">KAFKA</text></g>
      <g class="pulse"><circle cx="-92" cy="65" r="7" fill="#55e6a5"/><text class="mono fine" x="-142" y="86">REDIS</text></g>
      <path class="cyan-line route" d="M0-55C92-38 87 51 45 72" opacity=".45"/>
      <path class="violet-line route-fast" d="M-49 22C-4 75 65 32 75-30" opacity=".38"/>
    </g>

    {stack_card(427, 174, 'DOMAIN / CORE', '#2dd4ff', ['Spring Security · JPA', 'MapStruct · Liquibase', 'REST · WebSocket'])}
    {stack_card(713, 174, 'DATA / FLOW', '#9b7cff', ['Kafka · Redis', 'PostgreSQL · MySQL', 'Event-driven contracts'])}
    {stack_card(427, 315, 'PLATFORM / SIGNAL', '#55e6a5', ['Docker · Kubernetes', 'Prometheus · Grafana', 'CI/CD pipelines'])}
    {stack_card(713, 315, 'PROOF / QUALITY', '#ffb454', ['JUnit 5 · Mockito', 'Spring Boot Test', 'Testcontainers'])}

    <text class="mono fine" x="58" y="465">THE STACK CHANGES. THE DISCIPLINE SURVIVES.</text>
    <rect class="bar" x="427" y="469" width="564" height="3" fill="url(#cyanGreen)"/>
    '''
    return svg_document(495, "System arsenal", "Java backend technologies grouped by engineering responsibility", body)


def render_activity(config: dict[str, str], stats: ProfileStats) -> str:
    end = date.fromisoformat(stats.updated)
    sunday_offset = (end.weekday() + 1) % 7
    current_week = end - timedelta(days=sunday_offset)
    start = current_week - timedelta(weeks=52)
    cell = 11
    step = 15
    x0 = 130
    y0 = 193
    colors = ["#130c1d", "#2b1b40", "#513574", "#8255b4", "#ceb8ff"]
    cells: list[str] = []
    month_labels: list[str] = []
    previous_month = -1

    for week in range(53):
        week_date = start + timedelta(weeks=week)
        if week_date.month != previous_month:
            month_labels.append(
                f'<text class="mono fine" x="{x0 + week * step}" y="174">{week_date.strftime("%b").upper()}</text>'
            )
            previous_month = week_date.month
        for weekday in range(7):
            day = week_date + timedelta(days=weekday)
            level = int((stats.active or {}).get(day.isoformat(), 0))
            future = day > end
            opacity = ".28" if future else "1"
            css_class = "pulse" if level >= 4 else ""
            delay = ((week + weekday) % 9) * 0.17
            cells.append(
                f'<rect class="{css_class}" style="animation-delay:{delay:.2f}s" x="{x0 + week * step}" y="{y0 + weekday * step}" width="{cell}" height="{cell}" rx="2.5" fill="{colors[level]}" stroke="#274057" stroke-opacity=".42" opacity="{opacity}"/>'
            )

    active_days = len(stats.active or {})
    body = f'''
    <text class="mono kicker" x="58" y="53">04 // YEARLY SIGNAL</text>
    <text class="display" x="55" y="103" font-size="40">CONSISTENCY, RENDERED AS DATA.</text>
    <text class="copy" x="58" y="136">A live public contribution trace — refreshed automatically every day.</text>

    <g transform="translate(695 36)">
      <rect width="247" height="105" rx="17" fill="#09151f" stroke="#2dd4ff" stroke-opacity=".35"/>
      <text class="mono fine" x="18" y="27">TOTAL CONTRIBUTIONS</text>
      <text class="mono" x="18" y="70" fill="#f4f8ff" font-size="38" font-weight="800">{stats.contributions}</text>
      <circle class="pulse" cx="213" cy="28" r="5" fill="#55e6a5"/>
      <text class="mono fine" x="213" y="89" text-anchor="end" fill="#55e6a5">LIVE</text>
    </g>

    {''.join(month_labels)}
    <text class="mono fine" x="58" y="217">SUN</text>
    <text class="mono fine" x="58" y="247">TUE</text>
    <text class="mono fine" x="58" y="277">THU</text>
    <text class="mono fine" x="58" y="307">SAT</text>
    {''.join(cells)}

    <g transform="translate(58 337)">
      <text class="mono fine" x="0" y="0">{active_days:02d} ACTIVE DAYS</text>
      <text class="mono fine" x="180" y="0">{stats.public_repos:02d} PUBLIC REPOS</text>
      <text class="mono fine" x="368" y="0">{stats.followers:02d} PEOPLE TUNED IN</text>
      <text class="mono fine" x="884" y="0" text-anchor="end">SYNC {esc(stats.updated)} / UTC</text>
    </g>
    <rect x="58" y="354" width="884" height="2" fill="#122235"/>
    <rect class="bar" x="58" y="354" width="{max(32, min(884, stats.contributions * 5))}" height="2" fill="url(#cyanViolet)"/>
    '''
    return svg_document(
        380,
        f"{config['name']} contribution signal",
        f"{stats.contributions} public contributions in the last year, refreshed {stats.updated}",
        body,
    )


def render_footer(config: dict[str, str]) -> str:
    body = f'''
    <circle cx="858" cy="107" r="118" fill="#2b183e" opacity=".34" filter="url(#softGlow)"/>
    <path class="cyan-line route" d="M688 170C757 82 833 50 992 66" opacity=".28"/>
    <path class="violet-line route-fast" d="M740 215C808 134 898 140 1016 101" opacity=".25"/>
    <text class="mono kicker" x="58" y="52">05 // OPEN CHANNEL</text>
    <text class="display" x="55" y="111" font-size="44">LET'S BUILD SYSTEMS THAT STAY UP.</text>
    <text class="copy" x="58" y="145">Explore the code, follow the signal, or start a conversation.</text>
    <g transform="translate(58 173)">
      <rect width="286" height="46" rx="23" fill="#0a1a25" stroke="#2dd4ff" stroke-opacity=".55"/>
      <circle class="pulse" cx="24" cy="23" r="5" fill="#2dd4ff"/>
      <text class="mono label" x="42" y="28">github.com/{esc(config['username'])}</text>
    </g>
    <text class="mono fine" x="942" y="216" text-anchor="end">CLICK TO CONNECT ↗</text>
    <g transform="translate(858 107)">
      <circle class="spin" r="78" fill="none" stroke="#2dd4ff" stroke-opacity=".31" stroke-dasharray="3 10"/>
      <circle class="spin-reverse" r="60" fill="none" stroke="#9b7cff" stroke-opacity=".29" stroke-dasharray="17 11"/>
      <path d="M-23-7h46v14h-46zM-13-22v44M13-22v44" fill="none" stroke="#ccefff" stroke-width="2" opacity=".8"/>
    </g>
    '''
    return svg_document(245, "Open channel", "Connect with Ali Ozan Karaçor on GitHub", body)


def write_panel(filename: str, content: str) -> None:
    path = ASSETS / filename
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"rendered {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="render with the bundled public-data snapshot instead of calling GitHub",
    )
    args = parser.parse_args()

    config = load_config()
    stats = fetch_stats(config["username"], offline=args.offline)
    ASSETS.mkdir(parents=True, exist_ok=True)

    write_panel("hero.svg", render_hero(config, stats))
    write_panel("manifesto.svg", render_manifesto(config))
    write_panel("projects.svg", render_projects(config))
    write_panel("arsenal.svg", render_arsenal())
    write_panel("activity.svg", render_activity(config, stats))
    write_panel("footer.svg", render_footer(config))


if __name__ == "__main__":
    main()
