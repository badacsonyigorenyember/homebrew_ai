"""Tags for hops, fermentables and yeasts (s3-style-fit Task 3).

The hand-made part is loaders/style_fit_vocab.toml: the sensory dimensions, the tag tree and the
descriptor dictionary (a Hungarian or English word -> a character tag). This module

  1. loads that file into ref.sensory_dimension, ref.tag and ref.tag_synonym (load_vocab), and
  2. derives ref.ingredient_tag (reviewed = false) for every hop, fermentable and yeast from the
     ingredient's own ref data (derive_tags).

Nothing is guessed. A word that is in neither the dictionary nor the no-character list is not
tagged; the ingredient gets a row in ref.ingredient_review naming it. So does an ingredient with
no descriptor text at all. A person adds the word to the vocabulary file and runs this again.

Where the words come from:
  hop         the shop's short "Aroma :" line, and only when that line is empty or "???" the
              "Komló aroma" list (the list carries Citrusos on 55 of 90 hops, so using both
              would make nearly every hop match a citrus style); origin from ref.hop.origins
  fermentable its role as a family tag; characters from a keyword scan of its name and
              description (prose, so a word that is not in the dictionary is not flagged)
  yeast       family from the shop's Stílus (else ref.yeast.type); characters from the shop's
              Aroma field, else a keyword scan of the product text after "Aroma"
  intake row  (raw has an "intake" key, written by loaders/extra_ingredients.py) the
              "descriptors" list of its file, each word a synonym or a character tag name; a word
              that is neither goes to ingredient_review. Hop origin and fermentable family come
              as above; a yeast's family comes from its type (INTAKE_YEAST_FAMILY)

Re-runnable, one transaction. Rows of ref.ingredient_tag with reviewed = true are kept.

Usage:  python -m loaders.tags
"""

import re
import tomllib
from collections import Counter
from pathlib import Path

from loaders.common import name_key
from loaders.db import connect

VOCAB_PATH = Path(__file__).with_name("style_fit_vocab.toml")
YEAST_TYPE_FAMILIES = {"ale", "lager", "kveik", "brett"}  # ref.yeast.type values that are family tags

# ref.yeast.type -> family tag, for intake yeasts (they have no shop Stílus); souring cultures are "sour"
INTAKE_YEAST_FAMILY = {"ale": "ale", "lager": "lager", "kveik": "kveik", "brett": "brett", "lacto": "sour", "pedio": "sour"}


def read_vocab(path: Path = VOCAB_PATH) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------- reading the words


def split_words(text: str | None, filler: frozenset | set = frozenset()) -> list[str]:
    """A descriptor text as a list of lower-case phrases.

    Splits on commas, " és " and " and "; drops empty pieces and "???"; drops filler words
    (e.g. "jegyekkel", "erősen") at either end of a phrase.
    """
    if not text:
        return []
    words = []
    for piece in re.split(r"\s*,\s*|\s+és\s+|\s+and\s+", text.strip()):
        tokens = piece.strip().strip(".").lower().split()
        while tokens and tokens[0] in filler:
            tokens.pop(0)
        while tokens and tokens[-1] in filler:
            tokens.pop()
        phrase = " ".join(tokens)
        if phrase and not set(phrase) <= {"?"}:
            words.append(phrase)
    return words


def _unique(words: list[str]) -> list[str]:
    return list(dict.fromkeys(words))


def hop_words(raw: dict, filler: frozenset | set = frozenset()) -> list[str]:
    """A hop's character words: the "Aroma :" line of the shop page, else its "Komló aroma" list."""
    skus = raw.get("hopline-hops", {}).values()
    line = []
    for sku in skus:
        match = re.search(r"Aroma\s*:(.*)$", sku.get("spec") or "")
        if match:
            line += split_words(match.group(1), filler)
    if line:
        return _unique(line)
    listed = []
    for sku in skus:
        listed += split_words((sku.get("params") or {}).get("Komló aroma"), filler)
    return _unique(listed)


def yeast_words(raw: dict, filler: frozenset | set = frozenset()) -> list[str]:
    """A yeast's character words from the shop's Aroma field (parameters, then the spec table)."""
    words = []
    for sku in raw.get("hopline-yeasts", {}).values():
        field = (
            (sku.get("params") or {}).get("Aroma")
            or (sku.get("table") or {}).get("Aroma")
            or ((sku.get("details") or {}).get("table") or {}).get("Aroma")
        )
        words += split_words(field, filler)
    return _unique(words)


def yeast_spec_text(raw: dict) -> str:
    """The product text after "Aroma" (free text, style words and prose included), or ""."""
    for sku in raw.get("hopline-yeasts", {}).values():
        match = re.search(r"Aroma\s*:?\s*(.*)$", sku.get("spec") or "")
        if match:
            return match.group(1)
    return ""


def yeast_style(raw: dict) -> str | None:
    """The shop's Stílus value (e.g. "English Ale", "kveik"), or None."""
    for sku in raw.get("hopline-yeasts", {}).values():
        style = (sku.get("params") or {}).get("Stílus") or (sku.get("table") or {}).get("Stílus")
        if style:
            return style
    return None


def intake_words(raw: dict) -> list[str] | None:
    """The descriptor words of an intake row, or None when the row is not an intake row."""
    if "intake" not in raw:
        return None
    return list(raw["intake"]["fields"].get("descriptors") or [])


def descriptor_tag(word: str, synonyms: dict, character_tags: set) -> str | None:
    """The character tag a descriptor word of an intake file means, or None when it is unknown.

    The word is a key of the synonym dictionary (compared as name_key) or a character tag name.
    """
    tag = synonyms.get(name_key(word))
    if tag:
        return tag
    return word if word in character_tags else None


def scan_text(text: str, synonyms: dict, no_character: set) -> tuple[list[str], bool]:
    """Known descriptor words found in free text: (tag names, whether any known word was seen).

    Looks at runs of one to three words. Words that are not known are ignored; this is a scan
    of prose, not a list of descriptors.
    """
    tokens = re.findall(r"[^\W\d_]+", (text or "").lower())
    found, seen = [], False
    for start in range(len(tokens)):
        for length in (3, 2, 1):
            if start + length > len(tokens):
                continue
            key = name_key(" ".join(tokens[start : start + length]))
            if key in synonyms:
                found.append(synonyms[key])
                seen = True
                break
            if key in no_character:
                seen = True
                break
    return _unique(found), seen


# ---------------------------------------------------------------- loading the vocabulary


def load_vocab(conn, vocab: dict) -> dict:
    """Upsert dimensions, tags and synonyms from the vocabulary; synonyms not in it are deleted."""
    for d in vocab["dimension"]:
        conn.execute(
            "insert into ref.sensory_dimension (name, class) values (%s, %s) "
            "on conflict (name) do update set class = excluded.class",
            (d["name"], d["class"]),
        )

    ids = {}  # (facet, name) -> id; a parent must be listed before its children
    for t in vocab["tag"]:
        parent_id = None
        if t.get("parent"):
            if (t["facet"], t["parent"]) not in ids:
                raise ValueError(f"tag {t['facet']}/{t['name']}: parent {t['parent']!r} is not listed before it")
            parent_id = ids[(t["facet"], t["parent"])]
        ids[(t["facet"], t["name"])] = conn.execute(
            "insert into ref.tag (facet, name, parent_id) values (%s, %s, %s) "
            "on conflict (facet, name) do update set parent_id = excluded.parent_id returning id",
            (t["facet"], t["name"], parent_id),
        ).fetchone()[0]

    no_character = {name_key(w) for w in vocab["no_character"]["words"]}
    for word, tag in vocab["synonyms"].items():
        if ("character", tag) not in ids:
            raise ValueError(f"synonym {word!r}: {tag!r} is not a character tag")
        if word != name_key(word):
            raise ValueError(f"synonym {word!r}: write the key as {name_key(word)!r} (name_key)")
        if word in no_character:
            raise ValueError(f"synonym {word!r} is also in the no-character list")
    for table in ("yeast_family", "yeast_family_override"):
        for word, tag in vocab[table].items():
            if ("family", tag) not in ids:
                raise ValueError(f"{table} {word!r}: {tag!r} is not a family tag")

    keys = list(vocab["synonyms"])
    conn.execute("delete from ref.tag_synonym where word <> all(%s)", (keys,))
    for word, tag in vocab["synonyms"].items():
        conn.execute(
            "insert into ref.tag_synonym (word, tag_id) values (%s, %s) "
            "on conflict (word) do update set tag_id = excluded.tag_id",
            (word, ids[("character", tag)]),
        )
    return {"dimensions": len(vocab["dimension"]), "tags": len(ids), "synonyms": len(keys)}


# ---------------------------------------------------------------- deriving ingredient tags


def derive_tags(conn, vocab: dict) -> dict:
    """Rebuild ref.ingredient_tag (reviewed = false) and ref.ingredient_review from ref data.

    Reads the dictionary from ref.tag_synonym, so a synonym added there (or in the vocabulary
    file, after load_vocab) takes effect on the next call. The caller commits.
    """
    filler = set(vocab["filler"]["words"])
    no_character = {name_key(w) for w in vocab["no_character"]["words"]}
    tag_ids = {(facet, name): tag_id for tag_id, facet, name in conn.execute("select id, facet, name from ref.tag")}
    synonyms = {
        word: name
        for word, name in conn.execute(
            "select s.word, t.name from ref.tag_synonym s join ref.tag t on t.id = s.tag_id"
        )
    }

    conn.execute("delete from ref.ingredient_tag where not reviewed")
    conn.execute("delete from ref.ingredient_review")

    def resolve(words: list[str]) -> tuple[list[str], list[str]]:
        """(character tag names, unknown words) for descriptor phrases."""
        known, unknown = [], []
        for word in words:
            key = name_key(word)
            if key in synonyms:
                known.append(synonyms[key])
            elif key not in no_character:
                unknown.append(word)
        return _unique(known), unknown

    character_tags = {name for facet, name in tag_ids if facet == "character"}

    def resolve_intake(words: list[str]) -> tuple[list[str], list[str]]:
        """(character tag names, unknown words) for the descriptors of an intake file."""
        known, unknown = [], []
        for word in words:
            tag = descriptor_tag(word, synonyms, character_tags)
            if tag:
                known.append(tag)
            else:
                unknown.append(word)
        return _unique(known), unknown

    def save(ingredient_id: int, origin=(), family=(), character=(), reasons=()):
        wanted = [("origin", n) for n in origin] + [("family", n) for n in family] + [("character", n) for n in character]
        for facet, name in wanted:
            conn.execute(
                "insert into ref.ingredient_tag (ingredient_id, tag_id) values (%s, %s) on conflict do nothing",
                (ingredient_id, tag_ids[(facet, name)]),
            )
        if reasons:
            conn.execute(
                "insert into ref.ingredient_review (ingredient_id, reason) values (%s, %s)",
                (ingredient_id, "; ".join(reasons)),
            )

    for iid, raw, origins in conn.execute(
        "select i.id, i.raw, h.origins from ref.ingredient i join ref.hop h on h.ingredient_id = i.id order by i.id"
    ).fetchall():
        intake = intake_words(raw)
        words = hop_words(raw, filler) if intake is None else intake
        known, unknown = resolve(words) if intake is None else resolve_intake(words)
        reasons = []
        if not words:
            reasons.append("no descriptor text")
        if unknown:
            reasons.append("unknown words: " + ", ".join(unknown))
        save(iid, origin=origins or (), character=known, reasons=reasons)

    for iid, name, raw, description, role in conn.execute(
        "select i.id, i.name, i.raw, f.description, f.role from ref.ingredient i "
        "join ref.fermentable f on f.ingredient_id = i.id order by i.id"
    ).fetchall():
        intake = intake_words(raw)
        reasons = []
        if intake is None:
            found, _ = scan_text(f"{name}. {description or ''}", synonyms, no_character)
        else:
            found, unknown = resolve_intake(intake)
            if unknown:
                reasons.append("unknown words: " + ", ".join(unknown))
        save(iid, family=[role] if role else [], character=found, reasons=reasons)

    for iid, name, raw, ytype in conn.execute(
        "select i.id, i.name, i.raw, y.type from ref.ingredient i join ref.yeast y on y.ingredient_id = i.id order by i.id"
    ).fetchall():
        reasons = []
        intake = intake_words(raw)
        if intake is not None:
            family = INTAKE_YEAST_FAMILY.get(ytype)
            if family is None:
                reasons.append(f"no yeast family (type {ytype!r})")
            known, unknown = resolve_intake(intake)
            if not intake:
                reasons.append("no descriptor text")
            if unknown:
                reasons.append("unknown words: " + ", ".join(unknown))
            save(iid, family=[family] if family else [], character=known, reasons=reasons)
            continue
        style = yeast_style(raw)
        family = vocab["yeast_family_override"].get(name_key(name)) or vocab["yeast_family"].get(name_key(style or ""))
        if family is None and ytype in YEAST_TYPE_FAMILIES:
            family = ytype
        if family is None:
            reasons.append(f"no yeast family (Stílus {style!r}, type {ytype!r})")

        words = yeast_words(raw, filler)
        if words:
            known, unknown = resolve(words)
        else:
            known, seen = scan_text(yeast_spec_text(raw), synonyms, no_character)
            unknown = []
            if not seen:
                reasons.append("no descriptor text")
        if unknown:
            reasons.append("unknown words: " + ", ".join(unknown))
        save(iid, family=[family] if family else [], character=known, reasons=reasons)

    return {}


# ---------------------------------------------------------------- run


def report(conn) -> None:
    print("tag rows per ingredient kind and facet:")
    for kind, facet, rows, ingredients in conn.execute(
        "select i.kind, t.facet, count(*), count(distinct i.id) from ref.ingredient_tag it "
        "join ref.ingredient i on i.id = it.ingredient_id join ref.tag t on t.id = it.tag_id "
        "group by 1, 2 order by 1, 2"
    ):
        print(f"  {kind:12} {facet:10} {rows:4} rows on {ingredients} ingredients")
    flagged = conn.execute(
        "select i.kind, i.producer, i.name, r.reason from ref.ingredient_review r "
        "join ref.ingredient i on i.id = r.ingredient_id order by i.kind, i.name"
    ).fetchall()
    print(f"flagged for review: {len(flagged)}", dict(Counter(k for k, *_ in flagged)))
    for kind, producer, name, reason in flagged:
        print(f"  {kind:11} {(producer + ' ' if producer else '') + name}: {reason}")


def main() -> None:
    vocab = read_vocab()
    with connect() as conn:  # commits on success, rolls back on error
        counts = load_vocab(conn, vocab)
        derive_tags(conn, vocab)
        print("vocabulary:", counts)
        report(conn)


if __name__ == "__main__":
    main()
