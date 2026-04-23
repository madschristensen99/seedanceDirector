#!/usr/bin/env python3
"""
Snow Crash scene template expander.

Scene schema (registry-style):
{
  "scene_number": 7,
  "scene_name": "The Deliverator Suits Up",
  "duration": 5,
  "setting": "cosanostra_3569",
  "characters": ["hiro:deliverator"],     # id or id:variant
  "artifacts_visible": ["katana_hiro"],   # optional
  "style": "default",
  "action": "Low-angle tracking shot of {character:hiro}. He zips up..."
}

Placeholders in `action`:
  {character:id}         - short descriptor (name + one-line summary)
  {character:id:variant} - full descriptor (name + physical + variant wardrobe)
  {character:id:+}       - deep descriptor (adds species, affiliations, carried artifacts)
  {setting}              - description of the scene's single `setting` field
  {setting:id}           - description of a specific setting (with parent chain)
  {artifact:id}          - artifact description
  {faction:id}           - faction description

Commands:
  expand <registry> <scenes> [--out <path>] [--depth short|full|deep]
  validate <registry> <scenes>
  render <registry> <scenes> [--out <path>]   # full template-based rendering
"""
import json
import re
import sys
import argparse
from pathlib import Path


# Regex for placeholders: {type:id} or {type:id:variant_or_flag}
PLACEHOLDER_RE = re.compile(r"\{(character|setting|artifact|faction)(?::([a-z0-9_]+))?(?::([a-z0-9_+~]+))?\}")


# ---------- Loading ----------

def load_json(path):
    with open(path) as f:
        return json.load(f)


# ---------- Resolution ----------

def _inline_desc_clause(description):
    """
    Take a description string and format it as an inline parenthetical clause
    so that prose flows around it. Strips trailing periods, wraps in parens.
    """
    d = description.strip()
    # Collapse internal whitespace/newlines
    d = re.sub(r"\s+", " ", d)
    # Strip trailing period — we'll supply punctuation from the template
    d = d.rstrip(".").rstrip()
    return f"({d})"


def resolve_character(reg, cid, modifier=None, depth="full"):
    """
    Resolve a character reference for INLINE use in an action sentence.

    Produces output like: **Hiro Protagonist** (cappuccino skin, spiky dreads, wearing black arachnofiber uniform)

    depth/modifier:
      modifier='~'           -> name + short summary
      modifier='+'           -> name + deep (physical + species + affiliations + carries)
      modifier=<variant_id>  -> name + physical + variant wardrobe
      modifier=None          -> name + physical + default_variant wardrobe
    """
    if cid not in reg["characters"]:
        raise KeyError(f"Unknown character: {cid!r}")
    char = reg["characters"][cid]
    name = char.get("name", cid)

    # Decide mode
    variant_id = None
    if modifier == "~":
        mode = "short"
    elif modifier == "+":
        mode = "deep"
    elif modifier:
        mode = "full"
        variant_id = modifier
    else:
        mode = "full"
        variant_id = char.get("default_variant")

    if mode == "short":
        summary = char.get("short", "").strip()
        return f"**{name}** {_inline_desc_clause(summary)}" if summary else f"**{name}**"

    # Build a single inline clause from physical + variant wardrobe (+ optional deep extras)
    chunks = [char.get("physical_base", "").strip()]
    if variant_id:
        variants = char.get("variants", {})
        if variant_id not in variants:
            raise KeyError(f"Character {cid!r} has no variant {variant_id!r}. Available: {list(variants)}")
        chunks.append(variants[variant_id].strip())

    if mode == "deep":
        species_id = char.get("species")
        if species_id and species_id in reg.get("species", {}) and species_id != "human":
            chunks.append(f"a {reg['species'][species_id]['name']}")
        aff_ids = char.get("affiliations", []) or []
        aff_names = [reg["factions"][a]["name"] for a in aff_ids if a in reg.get("factions", {})]
        if aff_names:
            chunks.append("affiliated with " + ", ".join(aff_names))
        carry_ids = char.get("carries", []) or []
        carry_names = [reg["artifacts"][a]["name"] for a in carry_ids if a in reg.get("artifacts", {})]
        if carry_names:
            chunks.append("carrying " + ", ".join(carry_names))

    # Join the chunks into a single sentence, strip trailing periods on each piece
    cleaned = [re.sub(r"\s+", " ", c).rstrip(".").strip() for c in chunks if c.strip()]
    # For character inline clauses, join with " — " between physical and wardrobe
    # and ", " before deep extras. Keeps it reading like natural prose.
    if mode == "full":
        clause = " — ".join(cleaned)
    else:  # deep
        # First two pieces are physical+variant joined with ' — ', extras with ', '
        if len(cleaned) >= 2:
            head = " — ".join(cleaned[:2])
            tail = ", ".join(cleaned[2:]) if len(cleaned) > 2 else ""
            clause = head + (", " + tail if tail else "")
        else:
            clause = cleaned[0] if cleaned else ""
    return f"**{name}** ({clause})"


def resolve_setting(reg, sid, mode="inline"):
    """
    'inline' mode returns just the bold name — assumes the full description
    is provided once at the top of the prompt as the location anchor.
    """
    if sid not in reg["settings"]:
        raise KeyError(f"Unknown setting: {sid!r}")
    setting = reg["settings"][sid]
    name = setting.get("name", sid)
    if mode == "inline":
        return f"**{name}**"
    desc = re.sub(r"\s+", " ", setting.get("description", "").strip()).rstrip(".")
    return f"**{name}** — {desc}."


def resolve_artifact(reg, aid, mode="inline"):
    """
    'inline' mode returns bold name + short inline clause for prose flow.
    """
    if aid not in reg["artifacts"]:
        raise KeyError(f"Unknown artifact: {aid!r}")
    art = reg["artifacts"][aid]
    name = art["name"]
    if mode == "inline":
        # Short inline form — just the bold name, description goes to the artifact list
        return f"**{name}**"
    desc = re.sub(r"\s+", " ", art.get("description", "").strip()).rstrip(".")
    return f"**{name}** — {desc}."


def resolve_faction(reg, fid, mode="inline"):
    if fid not in reg["factions"]:
        raise KeyError(f"Unknown faction: {fid!r}")
    fac = reg["factions"][fid]
    name = fac["name"]
    if mode == "inline":
        return f"**{name}**"
    desc = re.sub(r"\s+", " ", fac.get("description", "").strip()).rstrip(".")
    return f"**{name}** — {desc}."


# ---------- Expansion ----------

def build_prompt(reg, scene, depth="full"):
    """
    Compose the final rendering prompt.

    Structure:
      [Universe: ...] Location: <setting name + description>.
      Characters present: <bold-name list with full descriptions>.
      <action text with inline references>.
      Additional visible artifacts: <list>.
      <style suffix>

    Characters and artifacts that appear inline in the action get their full
    description from the inline resolver. Anything in the `characters` /
    `artifacts_visible` lists that DIDN'T appear inline gets rolled into a
    'Also present / Also visible' clause to keep the model aware.
    """
    universe_name = reg["universe"]["name"]
    action = scene.get("action", "")
    default_setting = scene.get("setting")

    # Track which ids appear inline via placeholders so we don't duplicate them.
    inline_char_ids = set()
    inline_artifact_ids = set()
    for m in PLACEHOLDER_RE.finditer(action):
        kind, first, second = m.group(1), m.group(2), m.group(3)
        if kind == "character" and first:
            inline_char_ids.add(first)
        elif kind == "artifact" and first:
            inline_artifact_ids.add(first)

    # Inline expansion of the action text
    def replace(match):
        kind, first, second = match.group(1), match.group(2), match.group(3)
        if kind == "character":
            if not first:
                raise ValueError(f"Scene {scene.get('scene_number')}: {{character}} requires an id.")
            return resolve_character(reg, first, second, depth)
        if kind == "setting":
            sid = first if first else default_setting
            if not sid:
                raise ValueError(f"Scene {scene.get('scene_number')}: {{setting}} used with no setting field.")
            return resolve_setting(reg, sid, mode="inline")
        if kind == "artifact":
            return resolve_artifact(reg, first, mode="inline")
        if kind == "faction":
            return resolve_faction(reg, first, mode="inline")
        return match.group(0)

    expanded_action = PLACEHOLDER_RE.sub(replace, action)

    # Build the top location anchor (full description of the primary setting)
    location_line = ""
    if default_setting:
        s = reg["settings"].get(default_setting)
        if s:
            desc = re.sub(r"\s+", " ", s.get("description", "").strip()).rstrip(".")
            location_line = f"Location — **{s['name']}**: {desc}."

    # Character roster: any characters listed in the scene's `characters` field
    # that didn't get expanded inline still deserve a description.
    also_present = []
    for cref in scene.get("characters", []) or []:
        parts = cref.split(":")
        cid = parts[0]
        variant = parts[1] if len(parts) > 1 else None
        if cid in inline_char_ids:
            continue  # already described inline
        also_present.append(resolve_character(reg, cid, variant, depth))
    present_line = ""
    if also_present:
        present_line = "Also present: " + "; ".join(also_present) + "."

    # Artifacts visible but not referenced inline
    also_visible = []
    for aid in scene.get("artifacts_visible", []) or []:
        if aid in inline_artifact_ids:
            continue
        if aid in reg["artifacts"]:
            art = reg["artifacts"][aid]
            desc = re.sub(r"\s+", " ", art.get("description", "").strip()).rstrip(".")
            also_visible.append(f"**{art['name']}** ({desc})")
    visible_line = ""
    if also_visible:
        visible_line = "Also visible: " + "; ".join(also_visible) + "."

    # Style
    styles = reg.get("styles", {})
    style_id = scene.get("style", "default")
    style_suffix = styles.get(style_id, {}).get("suffix", "")

    pieces = [
        f"[Universe: {universe_name}]",
        location_line,
        present_line,
        expanded_action.strip(),
        visible_line,
        style_suffix,
    ]
    return " ".join(p for p in pieces if p).strip()


def expand_scenes(reg, scenes, depth="full"):
    out = []
    for scene in scenes:
        prompt = build_prompt(reg, scene, depth)
        out.append({
            "scene_number": scene["scene_number"],
            "scene_name": scene["scene_name"],
            "duration": scene["duration"],
            "original_prompt": prompt,
        })
    return out


# ---------- Validation ----------

def validate_scenes(reg, scenes):
    errors = []
    known = {
        "characters": set(reg.get("characters", {}).keys()),
        "settings": set(reg.get("settings", {}).keys()),
        "artifacts": set(reg.get("artifacts", {}).keys()),
        "factions": set(reg.get("factions", {}).keys()),
        "styles": set(reg.get("styles", {}).keys()),
        "species": set(reg.get("species", {}).keys()),
    }

    # Cross-check registry internal references
    for cid, char in reg.get("characters", {}).items():
        if char.get("species") and char["species"] not in known["species"]:
            errors.append(f"Registry: character {cid!r} references unknown species {char['species']!r}")
        for aff in char.get("affiliations", []) or []:
            if aff not in known["factions"]:
                errors.append(f"Registry: character {cid!r} references unknown faction {aff!r}")
        for art in char.get("carries", []) or []:
            if art not in known["artifacts"]:
                errors.append(f"Registry: character {cid!r} references unknown artifact {art!r}")
    for sid, setting in reg.get("settings", {}).items():
        if setting.get("parent") and setting["parent"] not in known["settings"]:
            errors.append(f"Registry: setting {sid!r} references unknown parent {setting['parent']!r}")
        if setting.get("operated_by") and setting["operated_by"] not in known["factions"]:
            errors.append(f"Registry: setting {sid!r} references unknown operator {setting['operated_by']!r}")

    # Check each scene
    for scene in scenes:
        sn = scene.get("scene_number", "?")
        # Setting field
        if scene.get("setting") and scene["setting"] not in known["settings"]:
            errors.append(f"Scene {sn}: unknown setting id {scene['setting']!r}")
        # Characters list (format: id or id:variant)
        for cref in scene.get("characters", []) or []:
            parts = cref.split(":")
            cid = parts[0]
            variant = parts[1] if len(parts) > 1 else None
            if cid not in known["characters"]:
                errors.append(f"Scene {sn}: unknown character id {cid!r}")
                continue
            if variant and variant not in ("+", "~"):
                variants = reg["characters"][cid].get("variants", {})
                if variant not in variants:
                    errors.append(f"Scene {sn}: character {cid!r} has no variant {variant!r}")
        # Artifacts visible
        for aid in scene.get("artifacts_visible", []) or []:
            if aid not in known["artifacts"]:
                errors.append(f"Scene {sn}: unknown artifact {aid!r}")
        # Placeholders inside action text
        for m in PLACEHOLDER_RE.finditer(scene.get("action", "")):
            kind, first, second = m.group(1), m.group(2), m.group(3)
            if kind == "character" and first and first not in known["characters"]:
                errors.append(f"Scene {sn}: action references unknown character {first!r}")
            elif kind == "setting" and first and first not in known["settings"]:
                errors.append(f"Scene {sn}: action references unknown setting {first!r}")
            elif kind == "artifact" and first and first not in known["artifacts"]:
                errors.append(f"Scene {sn}: action references unknown artifact {first!r}")
            elif kind == "faction" and first and first not in known["factions"]:
                errors.append(f"Scene {sn}: action references unknown faction {first!r}")
        # Style
        if scene.get("style") and scene["style"] not in known["styles"]:
            errors.append(f"Scene {sn}: unknown style {scene['style']!r}")

    return errors


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_exp = sub.add_parser("expand", help="Expand scenes to full rendering prompts.")
    p_exp.add_argument("registry")
    p_exp.add_argument("scenes")
    p_exp.add_argument("--out")
    p_exp.add_argument("--depth", choices=["short", "full", "deep"], default="full")

    p_val = sub.add_parser("validate", help="Validate registry and scene references.")
    p_val.add_argument("registry")
    p_val.add_argument("scenes")

    args = parser.parse_args()
    reg = load_json(args.registry)
    scenes = load_json(args.scenes)

    if args.cmd == "validate":
        errs = validate_scenes(reg, scenes)
        if errs:
            print(f"Found {len(errs)} validation errors:")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)
        print(f"OK: registry valid, all {len(scenes)} scenes validate.")
        return

    if args.cmd == "expand":
        out = expand_scenes(reg, scenes, depth=args.depth)
        j = json.dumps(out, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(j)
            print(f"Wrote {len(out)} expanded scenes to {args.out}")
        else:
            print(j)


if __name__ == "__main__":
    main()
