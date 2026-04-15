"""Synthetic forensic case generator for Trace.

Produces 60 fictional records: 30 missing-persons + 30 unidentified-remains.
Six of the missing records are ground-truth paired with six unidentified
records describing the same fictional person, using maximally different
vocabulary (lay vs. forensic) so semantic search can be evaluated against
zero-keyword-overlap matches.

CANONICAL DATA LIVES IN cases.json. That file was hand-authored to the
same contract this generator follows and has higher narrative quality
for the 48 singletons than procedural templating gives. Running this
script will OVERWRITE cases.json with a seeded-random stand-in. Only do
that intentionally (e.g. to fuzz-test the pipeline on different singleton
wording). The 12 paired cases are identical between this script and the
hand-authored JSON, so the demo query always works either way.

CASE_ID SEMANTICS:
  - MP-001 ↔ UP-001 ... MP-006 ↔ UP-006  → ground-truth pairs (same fictional person).
  - MP-007 and above, UP-007 and above   → unrelated singletons that happen to share
                                            a numeric suffix. DO NOT pair by suffix
                                            for anything other than suffixes ≤ 006.

ETHICS:
  - No case models a real unsolved missing-persons or UID case.
  - The Benton County "jester tattoo" case and any lookalikes are excluded
    by project policy.
  - All names, locales beyond state level, and distinctive marks are fictional.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

random.seed(42)

OUT_PATH = Path(__file__).resolve().parent / "cases.json"


def iso_to_epoch(date_iso: str) -> int:
    """Convert 'YYYY-MM-DD' to unix seconds at UTC midnight."""
    dt = datetime.strptime(date_iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def case(
    case_id: str,
    case_type: str,
    sex: str,
    age_low: int,
    age_high: int,
    state: str,
    date_iso: str,
    physical_text: str,
    circumstances: str,
    clothing: str,
) -> dict:
    return {
        "case_id": case_id,
        "case_type": case_type,
        "sex": sex,
        "age_low": age_low,
        "age_high": age_high,
        "state": state,
        "date_epoch": iso_to_epoch(date_iso),
        "date_iso": date_iso,
        "physical_text": physical_text,
        "circumstances": circumstances,
        "clothing": clothing,
        "image_url": None,
    }


# ---------------------------------------------------------------------------
# Ground-truth pairs (12 cases). Each MP-00N pairs with UP-00N.
# Same fictional person, lay vs. forensic vocabulary, no keyword overlap.
# ---------------------------------------------------------------------------

PAIRS: list[dict] = []

# Pair 1 — SHIP EXACTLY THIS WORDING (Tennessee eagle-tattoo demo moment)
PAIRS.append(case(
    case_id="MP-001",
    case_type="missing",
    sex="Male",
    age_low=34,
    age_high=34,
    state="TN",
    date_iso="2019-10-14",
    physical_text=(
        "He was about 6 feet tall, had a distinctive tattoo of an eagle on "
        "his right forearm, and a small scar above his left eyebrow."
    ),
    circumstances=(
        "My brother went missing in 2019 in Tennessee. He was last seen near "
        "a highway after leaving a gas station outside Nashville."
    ),
    clothing="Wore blue jeans, a dark green flannel shirt, and brown work boots.",
))
PAIRS.append(case(
    case_id="UP-001",
    case_type="unidentified",
    sex="Male",
    age_low=30,
    age_high=38,
    state="TN",
    date_iso="2020-06-02",
    physical_text=(
        "Male, mid-30s, avian motif dermagraphic on right ventral "
        "antebrachium, 2cm linear scar superior to left supraorbital ridge. "
        "Estimated stature 178cm."
    ),
    circumstances=(
        "Recovered along I-40 corridor east of Nashville, 2020. Remains were "
        "in a partially wooded area adjacent to the highway shoulder."
    ),
    clothing=(
        "Denim trousers, dark forest-toned plaid overshirt, heavy-soled "
        "leather footwear."
    ),
))

# Pair 2 — Texas, late 20s female, hiking, rose ankle tattoo + scar
PAIRS.append(case(
    case_id="MP-002",
    case_type="missing",
    sex="Female",
    age_low=28,
    age_high=28,
    state="TX",
    date_iso="2021-04-11",
    physical_text=(
        "About 5 foot 5, slim build, with a red rose tattoo on her right "
        "ankle and a noticeable scar on the back of her right hand from a "
        "childhood burn."
    ),
    circumstances=(
        "My cousin set off on a solo day hike in the hill country west of "
        "Austin and never made it back to her car. She told family she was "
        "taking a marked trail and would be home by dinner."
    ),
    clothing=(
        "Gray hiking leggings, a peach-colored technical t-shirt, and low "
        "trail-running shoes."
    ),
))
PAIRS.append(case(
    case_id="UP-002",
    case_type="unidentified",
    sex="Female",
    age_low=25,
    age_high=32,
    state="TX",
    date_iso="2021-09-23",
    physical_text=(
        "Adult female, late 20s estimated. Floral motif dermagraphic, right "
        "lateral malleolus region. Healed hypertrophic scar across dorsum of "
        "right hand consistent with remote thermal injury. Estimated stature "
        "165cm, gracile build."
    ),
    circumstances=(
        "Skeletal remains recovered in a limestone drainage ravine west of "
        "Austin, discovered by recreational hikers. Recovery site approximately "
        "400m off a backcountry trail network."
    ),
    clothing=(
        "Stretch athletic lower-garment, short-sleeved synthetic upper-garment "
        "in a warm pastel tone, low-profile mesh-upper footwear."
    ),
))

# Pair 3 — Pennsylvania, 50s male fisherman, anchor bicep tattoo
PAIRS.append(case(
    case_id="MP-003",
    case_type="missing",
    sex="Male",
    age_low=56,
    age_high=56,
    state="PA",
    date_iso="2018-05-20",
    physical_text=(
        "Weathered, tanned skin and calloused hands from years on the water. "
        "Has a faded blue anchor tattoo on his upper right arm. Full salt-"
        "and-pepper beard."
    ),
    circumstances=(
        "My dad went out alone to fish the Susquehanna after heavy spring "
        "rains. His truck was found at a put-in north of Harrisburg but his "
        "small aluminum boat was never recovered."
    ),
    clothing=(
        "Khaki cargo pants, a navy-blue windbreaker over a white t-shirt, and "
        "rubber-soled deck shoes."
    ),
))
PAIRS.append(case(
    case_id="UP-003",
    case_type="unidentified",
    sex="Male",
    age_low=50,
    age_high=62,
    state="PA",
    date_iso="2018-07-28",
    physical_text=(
        "Adult male, 50s estimated. Chronic solar elastosis of exposed "
        "integument. Nautical motif dermagraphic, right proximal humerus, "
        "markedly faded. Dense facial pilosity present at time of recovery."
    ),
    circumstances=(
        "Remains recovered in a debris accumulation on the east bank of the "
        "Susquehanna River, approximately 14 miles downstream of a reported "
        "watercraft launch point. Signs of prolonged aqueous exposure."
    ),
    clothing=(
        "Heavyweight cotton-blend utility trousers, wind-resistant outer "
        "shell over a plain undershirt, slip-resistant low-top footwear."
    ),
))

# Pair 4 — California, 40s female nurse, butterfly shoulder tattoo
PAIRS.append(case(
    case_id="MP-004",
    case_type="missing",
    sex="Female",
    age_low=44,
    age_high=44,
    state="CA",
    date_iso="2022-02-08",
    physical_text=(
        "Shoulder-length brown hair, brown eyes, roughly 5 foot 6. Has a "
        "colorful butterfly tattoo on her left shoulder that she got for her "
        "40th birthday."
    ),
    circumstances=(
        "My sister is an ER nurse and was last seen walking to the staff lot "
        "after a night shift at a hospital in the Bay Area. Her car was "
        "still in the lot the next morning."
    ),
    clothing=(
        "Light blue hospital scrubs, a white zip-up fleece, and white "
        "clog-style work shoes."
    ),
))
PAIRS.append(case(
    case_id="UP-004",
    case_type="unidentified",
    sex="Female",
    age_low=38,
    age_high=48,
    state="CA",
    date_iso="2022-05-17",
    physical_text=(
        "Adult female, early to mid-40s estimated. Lepidopteran motif "
        "dermagraphic, left posterior deltoid, polychromatic. Cranial "
        "pilosity medium-length, mid-brown pigmentation. Estimated stature "
        "168cm."
    ),
    circumstances=(
        "Partial remains located in dense coastal scrubland along a county "
        "open-space preserve south of San Francisco Bay. Discovered during "
        "a routine trail-maintenance survey."
    ),
    clothing=(
        "Two-piece institutional-style garment set in pale blue, lightweight "
        "full-zip outer layer in off-white, closed-upper occupational "
        "footwear in white."
    ),
))

# Pair 5 — Florida, 20s male college student, dragon chest tattoo, pierced ear
PAIRS.append(case(
    case_id="MP-005",
    case_type="missing",
    sex="Male",
    age_low=22,
    age_high=22,
    state="FL",
    date_iso="2017-03-04",
    physical_text=(
        "Lean build, around 5 foot 10, with a large black dragon tattoo "
        "across his chest. His left ear is pierced. Short dark hair."
    ),
    circumstances=(
        "My son was a junior at a university in north Florida. He left a "
        "friend's apartment after a party near campus and never made it "
        "back to his dorm."
    ),
    clothing=(
        "Black graphic t-shirt, dark gray jeans, and black low-top canvas "
        "sneakers."
    ),
))
PAIRS.append(case(
    case_id="UP-005",
    case_type="unidentified",
    sex="Male",
    age_low=18,
    age_high=26,
    state="FL",
    date_iso="2017-11-12",
    physical_text=(
        "Adult male, early 20s estimated. Serpentine / mythological motif "
        "dermagraphic, sternal region, monochromatic. Healed left auricular "
        "perforation. Slender build, estimated stature 178cm."
    ),
    circumstances=(
        "Remains recovered in a retention pond margin within a state "
        "conservation parcel in north Florida, roughly 9 miles from a "
        "university campus district."
    ),
    clothing=(
        "Short-sleeved dark cotton upper-garment bearing a printed graphic, "
        "dark-wash denim trousers, low-profile canvas-upper footwear."
    ),
))

# Pair 6 — Arizona, 60s female hiker, cross wrist tattoo, prior hip replacement
PAIRS.append(case(
    case_id="MP-006",
    case_type="missing",
    sex="Female",
    age_low=63,
    age_high=63,
    state="AZ",
    date_iso="2023-10-02",
    physical_text=(
        "Silver hair in a short cut, blue eyes, about 5 foot 4. Has a tiny "
        "cross tattoo on the inside of her left wrist. Had a hip replacement "
        "surgery about ten years ago and walked with a slight limp."
    ),
    circumstances=(
        "My grandmother is an experienced hiker and set out on a morning "
        "loop trail in a national forest north of Flagstaff. She didn't "
        "return to the trailhead and her vehicle was still parked there "
        "that evening."
    ),
    clothing=(
        "Tan zip-off hiking pants, a long-sleeved sun-protective shirt in "
        "lavender, and broken-in hiking boots."
    ),
))
PAIRS.append(case(
    case_id="UP-006",
    case_type="unidentified",
    sex="Female",
    age_low=58,
    age_high=70,
    state="AZ",
    date_iso="2024-04-19",
    physical_text=(
        "Adult female, approximately 60–70 years. Cruciform motif "
        "dermagraphic, left volar wrist, small format. Orthopedic hardware "
        "consistent with prior hip arthroplasty, approximately 10–15 years "
        "post-operative. Estimated stature 163cm."
    ),
    circumstances=(
        "Partial skeletal remains located off-trail in a ponderosa forest "
        "drainage north of Flagstaff during a springtime search-and-rescue "
        "training exercise."
    ),
    clothing=(
        "Convertible technical lower-garment in a neutral earth tone, "
        "long-sleeved UV-protective upper-garment in muted violet, over-the-"
        "ankle lugged-sole footwear."
    ),
))


# ---------------------------------------------------------------------------
# Procedural singletons (24 missing + 24 unidentified). MP-007..MP-030 and
# UP-007..UP-030. Composed from small word-banks so nothing here accidentally
# collides with a paired case or a known real case.
# ---------------------------------------------------------------------------

STATES_SINGLETON = [
    "OH", "NY", "WA", "OR", "CO", "NM", "GA", "NC", "SC", "VA",
    "MI", "IL", "IN", "WI", "MN", "IA", "MO", "KY", "AL", "LA",
    "OK", "KS", "NE", "MT", "ID", "UT", "NV", "MA", "ME", "VT",
]

# Lay word-bank (for missing narratives)
LAY_TATTOOS = [
    ("a small star tattoo", "on the back of the neck"),
    ("a tattoo of a compass", "on the left calf"),
    ("a heart-and-banner tattoo", "on the right forearm"),
    ("an infinity-symbol tattoo", "on the left wrist"),
    ("a sun tattoo", "on the right shoulder blade"),
    ("a crescent-moon tattoo", "behind the right ear"),
    ("a music-note tattoo", "on the left forearm"),
    ("a tree-branch tattoo", "along the spine"),
    ("a small wave tattoo", "on the right ankle"),
    ("a dog paw-print tattoo", "on the inside of the right wrist"),
]
LAY_HAIR = [
    "sandy blond hair",
    "dark brown curly hair",
    "long black hair",
    "short red hair",
    "thinning gray hair",
    "chin-length auburn hair",
    "shoulder-length blond hair",
    "close-cropped dark hair",
]
LAY_EYES = ["blue eyes", "brown eyes", "green eyes", "hazel eyes", "gray-blue eyes"]
LAY_HEIGHTS = [
    "about 5 foot 2", "about 5 foot 5", "about 5 foot 7",
    "about 5 foot 9", "about 6 feet tall", "about 6 foot 2",
]
LAY_MARKS = [
    "a pale surgical scar on the abdomen",
    "a chipped front tooth",
    "a birthmark on the left cheek",
    "a missing tip on the right pinky finger",
    "a scar across the chin",
    "stretched earlobes",
    "a crooked nose from an old break",
    "freckles across the nose and cheeks",
]
LAY_CLOTHING = [
    "dark wash jeans, a heather-gray hoodie, and white sneakers",
    "black leggings, an oversized maroon sweatshirt, and gray running shoes",
    "khaki work pants, a light blue button-up shirt, and brown loafers",
    "cargo shorts, a faded band t-shirt, and black flip-flops",
    "a navy polo, tan chinos, and brown leather boots",
    "a floral summer dress and white canvas sneakers",
    "black slacks, a cream-colored blouse, and low black heels",
    "carpenter jeans, a gray henley, and steel-toed boots",
    "a yellow rain jacket over a white t-shirt, and dark-wash jeans",
    "a green flannel, blue jeans, and tan hiking boots",
]
LAY_CIRCUMSTANCES = [
    "My family member was last seen leaving their apartment on a Friday night and never arrived at a friend's place across town.",
    "He walked out of a convenience store near a rural highway and hasn't been seen since.",
    "She left work at the end of a shift and was supposed to drive straight home but never arrived.",
    "He went out to walk the dog in the early evening and only the dog came back.",
    "She was visiting a state park with friends, wandered off from the picnic area, and didn't return.",
    "He told a roommate he was going for a short drive to clear his head and never came back.",
    "She was dropped off at a bus station downtown and missed every expected check-in afterward.",
    "He left a family gathering at a relative's farm on foot and didn't make it to the main road.",
    "She went to a late-night laundromat two blocks from home and never returned.",
    "He was last seen at a highway rest stop mid-road-trip by a passing trucker.",
]

# Forensic word-bank (for unidentified narratives)
FORENSIC_TATTOOS = [
    ("stellate motif dermagraphic", "posterior cervical region"),
    ("cartographic-instrument motif dermagraphic", "left lateral lower leg"),
    ("cordiform motif dermagraphic with banner element", "right ventral antebrachium"),
    ("lemniscate motif dermagraphic", "left volar wrist"),
    ("solar motif dermagraphic", "right superior posterior scapular region"),
    ("lunar motif dermagraphic", "right retroauricular region"),
    ("musical-notation motif dermagraphic", "left ventral antebrachium"),
    ("arboreal motif dermagraphic", "paravertebral region, midline"),
    ("undulatory (wave) motif dermagraphic", "right lateral malleolus region"),
    ("pedal-print motif dermagraphic", "right volar wrist"),
]
FORENSIC_MARKS = [
    "linear hypopigmented scar traversing anterior abdominal wall consistent with remote laparotomy",
    "fractured enamel of maxillary central incisor",
    "congenital hyperpigmented nevus on left zygomatic region",
    "traumatic amputation, distal phalanx, right fifth digit, well-healed",
    "linear scar transiting the mental region",
    "bilateral earlobe conchal expansion, prior gauge piercings",
    "remote nasal bone fracture with residual deviation",
    "ephelides concentrated across nasal and malar surfaces",
]
FORENSIC_BUILDS = [
    "gracile build, estimated stature 158cm",
    "average build, estimated stature 165cm",
    "average build, estimated stature 170cm",
    "robust build, estimated stature 175cm",
    "average build, estimated stature 183cm",
    "tall gracile build, estimated stature 188cm",
]
FORENSIC_HAIR = [
    "cranial pilosity short, light-blond pigmentation",
    "cranial pilosity medium-length, dark-brown, curly texture",
    "cranial pilosity long, black pigmentation, straight texture",
    "cranial pilosity short, reddish pigmentation",
    "cranial pilosity thinning, gray pigmentation",
    "cranial pilosity chin-length, auburn pigmentation",
]
FORENSIC_CLOTHING = [
    "dark-wash denim trousers, mid-weight hooded knit upper-garment in heather gray, low-top athletic footwear in white",
    "stretch athletic lower-garment in black, oversized fleece upper-garment in maroon, low-top athletic footwear in gray",
    "utility-cut cotton trousers in khaki, long-sleeved collared button-front upper-garment in pale blue, slip-on leather footwear in brown",
    "knee-length utility shorts, short-sleeved printed cotton upper-garment, open-toe thong-style footwear",
    "short-sleeved collared knit upper-garment in navy, mid-weight cotton trousers in tan, mid-calf leather footwear in brown",
    "lightweight printed lower-garment with floral pattern, low-top canvas footwear in white",
    "tailored trousers in black, long-sleeved lightweight blouse in off-white, low-profile closed-toe heeled footwear in black",
    "reinforced-pocket denim trousers, long-sleeved cotton upper-garment in gray, lace-up occupational footwear with reinforced toe",
    "waterproof outer shell in high-visibility yellow, plain undershirt in white, dark-wash denim trousers",
    "plaid flannel upper-garment in green tones, blue denim trousers, over-the-ankle lugged-sole footwear in tan",
]
FORENSIC_CIRCUMSTANCES = [
    "Remains recovered from a wooded drainage approximately {dist} off a rural secondary road. Signs of extended environmental exposure.",
    "Remains located adjacent to an abandoned service road on the perimeter of a {env}. Discovery made by {finder}.",
    "Partial skeletal remains recovered from a {env} during a {finder}-led survey.",
    "Body recovered in a {env}, approximately {dist} from the nearest maintained access point.",
    "Remains located within a culvert complex beneath a county highway embankment in a predominantly {env} corridor.",
    "Remains found in secondary-growth woodland adjacent to a disused rail corridor, discovered by {finder}.",
    "Remains recovered {dist} inland from a reservoir shoreline in a mixed {env} parcel.",
    "Body located in an agricultural drainage ditch bordering a {env}, discovered by {finder}.",
    "Skeletal remains found at the base of a rock outcrop in a {env}, consistent with prolonged exposure.",
    "Remains recovered in dense underbrush along a hiking spur within a {env}.",
]
ENV_TOKENS = [
    "mixed hardwood forest tract", "pine plantation", "desert scrubland parcel",
    "grassland preserve", "state wildlife management area",
    "municipal open-space preserve", "wetland conservation easement",
    "high-desert canyon complex",
]
FINDER_TOKENS = [
    "a utility-maintenance crew", "a hunter", "a forestry contractor",
    "a land-survey team", "a trail-maintenance volunteer group",
    "a park ranger on routine patrol",
]
DIST_TOKENS = [
    "200 meters", "half a mile", "three-quarters of a mile",
    "1.2 kilometers", "roughly 50 meters", "approximately 2 kilometers",
]


def random_lay_physical(rng: random.Random) -> str:
    tat, loc = rng.choice(LAY_TATTOOS)
    hair = rng.choice(LAY_HAIR)
    eyes = rng.choice(LAY_EYES)
    height = rng.choice(LAY_HEIGHTS)
    mark = rng.choice(LAY_MARKS)
    return (
        f"{height.capitalize()}, with {hair} and {eyes}. Has {tat} {loc}, "
        f"and {mark}."
    )


def random_forensic_physical(rng: random.Random, age_low: int, age_high: int) -> str:
    tat, loc = rng.choice(FORENSIC_TATTOOS)
    mark = rng.choice(FORENSIC_MARKS)
    build = rng.choice(FORENSIC_BUILDS)
    hair = rng.choice(FORENSIC_HAIR)
    return (
        f"Adult, estimated age range {age_low}-{age_high} years. {tat.capitalize()}, "
        f"{loc}. {mark.capitalize()}. {build.capitalize()}. {hair.capitalize()}."
    )


def random_circumstances_lay(rng: random.Random, state: str) -> str:
    base = rng.choice(LAY_CIRCUMSTANCES)
    return f"{base} Case is in {state}."


def random_circumstances_forensic(rng: random.Random, state: str) -> str:
    tpl = rng.choice(FORENSIC_CIRCUMSTANCES)
    return tpl.format(
        dist=rng.choice(DIST_TOKENS),
        env=rng.choice(ENV_TOKENS),
        finder=rng.choice(FINDER_TOKENS),
    ) + f" Jurisdiction: {state}."


def random_iso_date(rng: random.Random, year_low: int = 2015, year_high: int = 2024) -> str:
    year = rng.randint(year_low, year_high)
    month = rng.randint(1, 12)
    # Keep day safely within every month
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def build_singleton_missing(rng: random.Random, idx: int) -> dict:
    case_id = f"MP-{idx:03d}"
    sex = rng.choice(["Male", "Female"])
    age = rng.randint(18, 75)
    state = rng.choice(STATES_SINGLETON)
    date_iso = random_iso_date(rng)
    return case(
        case_id=case_id,
        case_type="missing",
        sex=sex,
        age_low=age,
        age_high=age,
        state=state,
        date_iso=date_iso,
        physical_text=random_lay_physical(rng),
        circumstances=random_circumstances_lay(rng, state),
        clothing=f"Was wearing {rng.choice(LAY_CLOTHING)}.",
    )


def build_singleton_unid(rng: random.Random, idx: int) -> dict:
    case_id = f"UP-{idx:03d}"
    sex = rng.choice(["Male", "Female"])
    age_low = rng.randint(18, 65)
    age_high = age_low + rng.randint(5, 12)
    if age_high > 85:
        age_high = 85
    state = rng.choice(STATES_SINGLETON)
    date_iso = random_iso_date(rng)
    return case(
        case_id=case_id,
        case_type="unidentified",
        sex=sex,
        age_low=age_low,
        age_high=age_high,
        state=state,
        date_iso=date_iso,
        physical_text=random_forensic_physical(rng, age_low, age_high),
        circumstances=random_circumstances_forensic(rng, state),
        clothing=rng.choice(FORENSIC_CLOTHING) + ".",
    )


def main() -> None:
    rng = random.Random(42)

    cases: list[dict] = list(PAIRS)  # 12 paired cases

    # 24 missing singletons: MP-007..MP-030
    for idx in range(7, 31):
        cases.append(build_singleton_missing(rng, idx))

    # 24 unidentified singletons: UP-007..UP-030
    for idx in range(7, 31):
        cases.append(build_singleton_unid(rng, idx))

    # Stable sort: missing first, then unidentified, by case_id
    cases.sort(key=lambda c: (0 if c["case_type"] == "missing" else 1, c["case_id"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    missing_count = sum(1 for c in cases if c["case_type"] == "missing")
    unid_count = sum(1 for c in cases if c["case_type"] == "unidentified")
    # 6 MP-00N <-> UP-00N pairs
    mp_ids = {c["case_id"] for c in cases if c["case_type"] == "missing"}
    up_ids = {c["case_id"] for c in cases if c["case_type"] == "unidentified"}
    pair_count = sum(
        1 for n in range(1, 7)
        if f"MP-{n:03d}" in mp_ids and f"UP-{n:03d}" in up_ids
    )

    rel_path = OUT_PATH.relative_to(Path.cwd()) if OUT_PATH.is_relative_to(Path.cwd()) else OUT_PATH
    print(
        f"Wrote {len(cases)} cases ({missing_count} missing, "
        f"{unid_count} unidentified, {pair_count} ground-truth pairs) "
        f"to {rel_path}"
    )


if __name__ == "__main__":
    main()
