#!/usr/bin/env python3
"""Apply a profile theme to README widgets and generated Breakout SVG files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / ".github" / "profile-themes"
ACTIVE_THEME_PATH = ROOT / ".github" / "profile-theme.json"
README_PATH = ROOT / "README.md"

LIGHT_SOURCE = ["EBEDF0", "9BE9A8", "40C463", "30A14E", "216E39"]
DARK_SOURCE = ["161B22", "0E4429", "006D32", "26A641", "39D353"]


def load_theme(theme_id: str) -> dict:
    if not re.fullmatch(r"[a-z0-9-]+", theme_id):
        raise ValueError(f"Invalid theme id: {theme_id}")

    path = THEMES_DIR / f"{theme_id}.json"
    if not path.is_file():
        available = ", ".join(sorted(item.stem for item in THEMES_DIR.glob("*.json")))
        raise ValueError(f"Unknown theme '{theme_id}'. Available themes: {available}")

    theme = json.loads(path.read_text(encoding="utf-8"))
    if theme.get("id") != theme_id:
        raise ValueError(f"Theme id mismatch in {path}")
    return theme


def active_theme_id() -> str:
    state = json.loads(ACTIVE_THEME_PATH.read_text(encoding="utf-8"))
    return state["active"]


def replace_parameter(url: str, name: str, value: str) -> str:
    pattern = rf"([?&]{re.escape(name)}=)[^&\"\s]+"
    updated, count = re.subn(pattern, rf"\g<1>{value}", url)
    if count == 0:
        raise ValueError(f"Parameter '{name}' was not found in {url}")
    return updated


def update_widget_url(url: str, colors: dict) -> str:
    mappings: dict[str, str] = {}

    if "readme-typing-svg.demolab.com" in url:
        mappings = {"color": colors["primary"]}
    elif "github-profile-summary-cards.vercel.app" in url:
        mappings = {
            "title_color": colors["primary"],
            "text_color": colors["text"],
            "border_color": colors["soft"],
            "icon_color": colors["strong"],
            "chart_color": colors["primary"],
        }
    elif "github-readme-streak-stats-eight.vercel.app" in url:
        mappings = {
            "border": colors["soft"],
            "stroke": colors["soft"],
            "ring": colors["primary"],
            "fire": colors["primary"],
            "currStreakNum": colors["text"],
            "sideNums": colors["text"],
            "currStreakLabel": colors["primary"],
            "sideLabels": colors["primary"],
            "dates": colors["text"],
        }
    elif "komarev.com/ghpvc" in url or "capsule-render.vercel.app" in url:
        mappings = {"color": colors["primary"]}

    for name, value in mappings.items():
        url = replace_parameter(url, name, value)
    return url


def apply_theme(theme_id: str) -> None:
    theme = load_theme(theme_id)
    colors = theme["colors"]
    readme = README_PATH.read_text(encoding="utf-8")

    readme, marker_count = re.subn(
        r"<!-- profile-theme: [a-z0-9-]+ -->",
        f"<!-- profile-theme: {theme_id} -->",
        readme,
        count=1,
    )
    if marker_count != 1:
        raise ValueError("README profile-theme marker is missing or duplicated")

    readme = re.sub(r"https://[^\"\s>]+", lambda match: update_widget_url(match.group(0), colors), readme)
    README_PATH.write_text(readme, encoding="utf-8", newline="\n")
    ACTIVE_THEME_PATH.write_text(
        json.dumps({"active": theme_id}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def recolor_svg(path: Path, source: list[str], target: list[str]) -> None:
    if len(source) != len(target):
        raise ValueError("Source and target palettes have different lengths")
    content = path.read_text(encoding="utf-8")
    for old, new in zip(source, target, strict=True):
        content = re.sub(rf"#{old}", f"#{new}", content, flags=re.IGNORECASE)
    path.write_text(content, encoding="utf-8", newline="\n")


def recolor_breakout(paths: list[Path], theme_id: str | None = None) -> None:
    theme = load_theme(theme_id or active_theme_id())
    colors = theme["colors"]
    for path in paths:
        palette = colors["breakout_dark"] if "-dark" in path.stem else colors["breakout_light"]
        source = DARK_SOURCE if "-dark" in path.stem else LIGHT_SOURCE
        recolor_svg(path, source, palette)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("theme_id")

    recolor_parser = subparsers.add_parser("recolor-breakout")
    recolor_parser.add_argument("--theme-id")
    recolor_parser.add_argument("paths", nargs="+", type=Path)

    args = parser.parse_args()
    if args.command == "apply":
        apply_theme(args.theme_id)
    else:
        recolor_breakout(args.paths, args.theme_id)


if __name__ == "__main__":
    main()
