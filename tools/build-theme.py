#!/usr/bin/env python3
"""Build the Marvin Red Circles KDE icon-theme overlay."""

from __future__ import annotations

import base64
import html
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUT_APPS = ROOT / "scalable" / "apps"
OUT_PLACES = ROOT / "scalable" / "places"
HOME = Path.home()
BASE = HOME / ".local/share/icons/Simply-Red-Circles"
RED = "#a02c2c"

DESKTOP_ROOTS = [
    Path("/usr/share/applications"),
    HOME / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    HOME / ".local/share/flatpak/exports/share/applications",
]

SEARCH_ROOTS = [
    HOME / ".local/share/icons/Colorful-Dark-Icons",
    HOME / ".local/share/icons/hicolor",
    Path("/usr/share/icons/hicolor"),
    Path("/usr/share/icons/breeze"),
    Path("/usr/share/icons/breeze-dark"),
    Path("/usr/share/pixmaps"),
]
SEARCH_ROOTS.extend(Path("/var/lib/flatpak/appstream").glob("*/*/active/icons"))
SEARCH_ROOTS.extend(
    (HOME / ".local/share/flatpak/appstream").glob("*/*/active/icons")
)

CUSTOM_DIR = Path(os.environ.get("MARVIN_ICON_ASSETS", ROOT / "assets"))
AVATAR = CUSTOM_DIR / "marvin-avatar.png"

CUSTOM = {
    "8tracks": CUSTOM_DIR / "8tracks.svg",
    "bitwarden": CUSTOM_DIR / "bitwarden.png",
    "chatgpt": CUSTOM_DIR / "chatGPT.svg",
    "gitkraken": CUSTOM_DIR / "gitkraken.svg",
    "gitlab": CUSTOM_DIR / "gitlab.svg",
    "rustdesk": CUSTOM_DIR / "rustdesk.png",
    "com.rustdesk.RustDesk": CUSTOM_DIR / "rustdesk.png",
    "slack": CUSTOM_DIR / "slack.svg",
    "spideroak": CUSTOM_DIR / "spideroak.svg",
}

FALLBACK_NAMES = {
    "emblem-music-symbolic": "audio-x-generic",
    "get-hot-new-stuff": "system-software-install",
    "hwloc": "utilities-system-monitor",
    "mark-location-symbolic": "mark-location",
    "network-wired-symbolic": "network-wired",
    "network-wireless-symbolic": "network-wireless",
    "office-chart-line-symbolic": "x-office-spreadsheet",
    "preferences-system-network-connection": "preferences-system-network",
    "speedometer-symbolic": "utilities-system-monitor",
    "view-process-system-symbolic": "utilities-system-monitor",
}

MENU_ALIASES = [
    "application-menu",
    "distributor-logo",
    "kde",
    "marvin-avatar",
    "start-here",
    "start-here-kde",
    "supertux",
]


def desktop_icon_names() -> set[str]:
    names: set[str] = set()
    for root in DESKTOP_ROOTS:
        if not root.exists():
            continue
        for desktop in root.rglob("*.desktop"):
            try:
                for raw in desktop.read_text(errors="ignore").splitlines():
                    if raw.startswith("Icon="):
                        name = raw.partition("=")[2].strip()
                        if name and not name.startswith("/"):
                            names.add(name)
            except OSError:
                continue
    return names


def theme_has(name: str) -> bool:
    for subdir in ("scalable/apps", "scalable/places", "scalable/actions"):
        for ext in ("svg", "svgz", "png", "xpm"):
            if (BASE / subdir / f"{name}.{ext}").exists():
                return True
    return False


def source_candidates(name: str) -> list[Path]:
    found: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for ext in ("svg", "svgz", "png", "xpm"):
            found.extend(root.rglob(f"{name}.{ext}"))
            found.extend(root.rglob(f"{name.lower()}.{ext}"))
    flatpak_app = Path("/var/lib/flatpak/app") / name
    if flatpak_app.exists():
        for ext in ("svg", "svgz", "png", "xpm"):
            found.extend(flatpak_app.rglob(f"{name}.{ext}"))
    return list(dict.fromkeys(found))


def score(path: Path) -> tuple[int, int, int]:
    ext_score = {".svg": 4, ".svgz": 3, ".png": 2, ".xpm": 1}.get(
        path.suffix.lower(), 0
    )
    scalable = 1 if "scalable" in path.parts else 0
    size = path.stat().st_size if path.exists() else 0
    return (ext_score, scalable, size)


def find_source(name: str) -> Path | None:
    candidates = source_candidates(name)
    if not candidates and name in FALLBACK_NAMES:
        candidates = source_candidates(FALLBACK_NAMES[name])
        base_name = FALLBACK_NAMES[name]
        if not candidates:
            for subdir in BASE.glob("*/*"):
                for ext in ("svg", "svgz", "png", "xpm"):
                    path = subdir / f"{base_name}.{ext}"
                    if path.exists():
                        candidates.append(path)
    return max(candidates, key=score) if candidates else None


def normalized_png(source: Path, size: int = 512) -> bytes:
    with tempfile.TemporaryDirectory(prefix="marvin-icon-") as tmp:
        render_source = source
        if source.suffix.lower() in {".svg", ".svgz"}:
            render_source = Path(tmp) / "rendered.png"
            subprocess.run(
                [
                    "rsvg-convert",
                    "-w",
                    str(size),
                    "-h",
                    str(size),
                    str(source),
                    "-o",
                    str(render_source),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        output = Path(tmp) / "icon.png"
        command = [
            "magick",
            str(render_source),
            "-background",
            "none",
            "-alpha",
            "on",
            "-resize",
            f"{size}x{size}",
            "-gravity",
            "center",
            "-extent",
            f"{size}x{size}",
            "-strip",
            str(output),
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        return output.read_bytes()


def badge_svg(source: Path, label: str) -> str:
    image = base64.b64encode(normalized_png(source)).decode("ascii")
    safe_label = html.escape(label)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <title>{safe_label} - Marvin Red Circles</title>
  <defs>
    <clipPath id="inside"><circle cx="32" cy="32" r="24"/></clipPath>
  </defs>
  <circle cx="32" cy="32" r="28" fill="none" stroke="{RED}" stroke-width="4"/>
  <image x="10" y="10" width="44" height="44" preserveAspectRatio="xMidYMid meet"
         clip-path="url(#inside)" href="data:image/png;base64,{image}"/>
</svg>
'''


def avatar_svg() -> str:
    image = base64.b64encode(normalized_png(AVATAR, 768)).decode("ascii")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <title>Marvin avatar menu icon</title>
  <defs><clipPath id="portrait"><circle cx="32" cy="32" r="27"/></clipPath></defs>
  <circle cx="32" cy="32" r="29" fill="#1f1f1f" stroke="{RED}" stroke-width="4"/>
  <image x="5" y="5" width="54" height="54" preserveAspectRatio="xMidYMid slice"
         clip-path="url(#portrait)" href="data:image/png;base64,{image}"/>
</svg>
'''


def write_icon(name: str, source: Path) -> None:
    (OUT_APPS / f"{name}.svg").write_text(badge_svg(source, name))


def main() -> int:
    OUT_APPS.mkdir(parents=True, exist_ok=True)
    OUT_PLACES.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    unresolved: list[str] = []
    names = sorted(name for name in desktop_icon_names() if not theme_has(name))

    for name in names:
        custom_source = CUSTOM.get(name)
        existing_custom = OUT_APPS / f"{name}.svg"
        if custom_source is not None and not custom_source.exists() and existing_custom.exists():
            generated.append(name)
            continue
        source = find_source(name)
        if source is None:
            unresolved.append(name)
            continue
        write_icon(name, source)
        generated.append(name)

    for name, source in CUSTOM.items():
        if source.exists():
            write_icon(name, source)
            if name not in generated:
                generated.append(name)

    avatar_path = OUT_APPS / "marvin-avatar.svg"
    avatar = ""
    if AVATAR.exists():
        avatar = avatar_svg()
    elif avatar_path.exists():
        avatar = avatar_path.read_text()
    if avatar:
        for name in MENU_ALIASES:
            (OUT_APPS / f"{name}.svg").write_text(avatar)
        (OUT_PLACES / "user-home.svg").write_text(avatar)

    print(f"Generated or refreshed: {len(generated)} application icons")
    print(f"Menu/avatar aliases: {len(MENU_ALIASES)}")
    if unresolved:
        print("Unresolved (covered by inherited themes):")
        for name in unresolved:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
