#!/usr/bin/env python3
"""Generate the named SVG jewel-icon collection used by SteamDeck Jewels."""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "jewels"

GEMS = {
    "agate": ("#ffcf9f", "#a94f42"),
    "alexandrite": ("#7de0be", "#75409b"),
    "amber": ("#ffd45e", "#c66a08"),
    "aquamarine": ("#a8f3f1", "#2b9eb3"),
    "beryl": ("#c5f2b8", "#569d72"),
    "bloodstone": ("#376f58", "#7e1525"),
    "carnelian": ("#ff9b65", "#a83c24"),
    "citrine": ("#fff176", "#d39b19"),
    "coral": ("#ff9a91", "#d94d57"),
    "diamond": ("#f7ffff", "#91cfe8"),
    "emerald": ("#55e89b", "#087b4f"),
    "garnet": ("#d94b63", "#72172d"),
    "jade": ("#8ee2a0", "#267b55"),
    "jasper": ("#df8e69", "#7b4635"),
    "kunzite": ("#f2b4ee", "#a55aa2"),
    "labradorite": ("#79b7b1", "#384d73"),
    "lapis-lazuli": ("#527cff", "#192c91"),
    "malachite": ("#67d681", "#126140"),
    "moonstone": ("#e8eaff", "#8e9bc8"),
    "obsidian": ("#55566a", "#11121b"),
    "onyx": ("#77798a", "#20212c"),
    "pearl": ("#fff8ef", "#cbbbc8"),
    "peridot": ("#c9f56b", "#6ca62d"),
    "quartz": ("#f3eaff", "#b6a1cb"),
    "rose-quartz": ("#ffc8da", "#d983a3"),
    "spinel": ("#ff719c", "#a52d62"),
    "sunstone": ("#ffc36c", "#d46537"),
    "tanzanite": ("#7d8cff", "#4036aa"),
    "tiger-eye": ("#e9a94f", "#63391d"),
    "topaz": ("#75dfff", "#287dc2"),
    "tourmaline": ("#f47fb5", "#397f69"),
    "turquoise": ("#62e4d4", "#168b91"),
    "zircon": ("#b5eeff", "#4e9ac1"),
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
<title>{title}</title>
<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient></defs>
<path d="M64 8 104 34 94 91 64 120 34 91 24 34Z" fill="url(#g)" stroke="#ffffff" stroke-opacity=".65" stroke-width="4"/>
<path d="M24 34h80L64 120ZM64 8 45 34l19 86 19-86Z" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="3"/>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (light, dark) in GEMS.items():
        title = name.replace("-", " ").title()
        (OUT / f"{name}.svg").write_text(
            TEMPLATE.format(title=title, light=light, dark=dark), encoding="utf-8"
        )
    print(f"Generated {len(GEMS)} jewel icons in {OUT}")


if __name__ == "__main__":
    main()
