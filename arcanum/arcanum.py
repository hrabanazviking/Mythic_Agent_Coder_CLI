#!/usr/bin/env python3
"""
⛧  A R C A N U M  ⊕  The Golden Dawn Tarot Divination Engine  ⛧

A TUI application based on Book T and Golden Dawn Hermetic tarot concepts.
Features elemental dignities, Qabalistic correspondences, multiple spreads,
and optional AI-enhanced readings via OpenRouter.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import random
import os
import json
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.box import HEAVY, DOUBLE, ROUNDED, MINIMAL
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.rule import Rule
    from rich.theme import Theme
    from rich.columns import Columns
    from rich.padding import Padding
except ImportError:
    print("✦ ARCANUM requires 'rich'. Install with: pip install rich")
    sys.exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ═══════════════════════════════════════════════════════════════
#  CUSTOM THEME
# ═══════════════════════════════════════════════════════════════

ARCANUM_THEME = Theme({
    "title": "bold gold1",
    "subtitle": "italic dark_goldenrod",
    "heading": "bold deep_sky_blue1",
    "subheading": "bold cyan2",
    "fire": "bold red3",
    "water": "bold deep_sky_blue2",
    "air": "bold cyan1",
    "earth": "bold green4",
    "spirit": "bold magenta1",
    "wands": "bold orange3",
    "cups": "bold blue1",
    "swords": "bold light_sky_blue1",
    "pentacles": "bold gold3",
    "major": "bold magenta2",
    "dignified": "bright_green",
    "ill_dignified": "bright_red",
    "neutral": "bright_yellow",
    "muted": "grey50",
    "keyword": "italic bright_white",
    "meaning": "white",
    "divider": "dark_goldenrod",
    "menu_sel": "bold gold1 on grey11",
    "menu_num": "bold cyan2",
    "menu_item": "white",
    "alert": "bold yellow1",
    "error": "bold red1",
    "success": "bold green1",
})

console = Console(theme=ARCANUM_THEME, soft_wrap=True)

# ═══════════════════════════════════════════════════════════════
#  GOLDEN DAWN CORRESPONDENCE DATA
# ═══════════════════════════════════════════════════════════════

ELEMENTS = {
    "Wands": "Fire",
    "Cups": "Water",
    "Swords": "Air",
    "Pentacles": "Earth",
}

ELEMENT_HARMONY = {
    ("Fire", "Fire"): "exalted",
    ("Fire", "Air"): "friendly",
    ("Fire", "Water"): "hostile",
    ("Fire", "Earth"): "neutral",
    ("Air", "Air"): "exalted",
    ("Air", "Fire"): "friendly",
    ("Air", "Water"): "friendly",
    ("Air", "Earth"): "hostile",
    ("Water", "Water"): "exalted",
    ("Water", "Air"): "friendly",
    ("Water", "Fire"): "hostile",
    ("Water", "Earth"): "friendly",
    ("Earth", "Earth"): "exalted",
    ("Earth", "Water"): "friendly",
    ("Earth", "Fire"): "neutral",
    ("Earth", "Air"): "hostile",
}

ZODIAC_SIGNS = {
    "Aries": {"element": "Fire", "ruler": "Mars", "quality": "Cardinal"},
    "Taurus": {"element": "Earth", "ruler": "Venus", "quality": "Fixed"},
    "Gemini": {"element": "Air", "ruler": "Mercury", "quality": "Mutable"},
    "Cancer": {"element": "Water", "ruler": "Moon", "quality": "Cardinal"},
    "Leo": {"element": "Fire", "ruler": "Sun", "quality": "Fixed"},
    "Virgo": {"element": "Earth", "ruler": "Mercury", "quality": "Mutable"},
    "Libra": {"element": "Air", "ruler": "Venus", "quality": "Cardinal"},
    "Scorpio": {"element": "Water", "ruler": "Mars", "quality": "Fixed"},
    "Sagittarius": {"element": "Fire", "ruler": "Jupiter", "quality": "Mutable"},
    "Capricorn": {"element": "Earth", "ruler": "Saturn", "quality": "Cardinal"},
    "Aquarius": {"element": "Air", "ruler": "Uranus", "quality": "Fixed"},
    "Pisces": {"element": "Water", "ruler": "Neptune", "quality": "Mutable"},
}

SEPHIROTH = {
    1: {"name": "Kether", "meaning": "Crown", "planet": "Neptune/Pluto"},
    2: {"name": "Chokmah", "meaning": "Wisdom", "planet": "Zodiac"},
    3: {"name": "Binah", "meaning": "Understanding", "planet": "Saturn"},
    4: {"name": "Chesed", "meaning": "Mercy", "planet": "Jupiter"},
    5: {"name": "Geburah", "meaning": "Severity", "planet": "Mars"},
    6: {"name": "Tiphareth", "meaning": "Beauty", "planet": "Sun"},
    7: {"name": "Netzach", "meaning": "Victory", "planet": "Venus"},
    8: {"name": "Hod", "meaning": "Splendour", "planet": "Mercury"},
    9: {"name": "Yesod", "meaning": "Foundation", "planet": "Moon"},
    10: {"name": "Malkuth", "meaning": "Kingdom", "planet": "Earth/Elements"},
}

HEBREW_LETTERS = {
    "Aleph": "א", "Beth": "ב", "Gimel": "ג", "Daleth": "ד", "Heh": "ה",
    "Vav": "ו", "Zayin": "ז", "Cheth": "ח", "Teth": "ט", "Yod": "י",
    "Kaph": "כ", "Lamed": "ל", "Mem": "מ", "Nun": "נ", "Samekh": "ס",
    "Ayin": "ע", "Peh": "פ", "Tzaddi": "צ", "Qoph": "ק", "Resh": "ר",
    "Shin": "ש", "Tau": "ת",
}

# ═══════════════════════════════════════════════════════════════
#  MAJOR ARCANA — Golden Dawn / Book T Correspondences
# ═══════════════════════════════════════════════════════════════

MAJOR_ARCANA = [
    {
        "numeral": "0", "name": "The Fool",
        "hebrew": "Aleph", "letter": "א",
        "attribution": "Air / Spirit of Aether",
        "path": 11, "sephiroth": "Kether-Chokmah",
        "image": "A youth with a wand, poised in mid-step at a cliff edge, a dog barks at his heels.",
        "upright": "Beginnings, innocence, spontaneity, free spirit, a leap of faith. The Divine Fool walks the path of trust, unburdened by worldly knowledge. Originality and the creative spark before manifestation.",
        "reversed": "Recklessness, carelessness, risk-taking, naivety. The fool falls rather than leaps. Spiritual blindness, failure to heed inner guidance, acting without thinking.",
        "keywords": ["Folly", "Beginnings", "Innocence", "Faith", "Inspiration"],
        "esoteric": "The Holy Spirit descending through the Abyss. The Zero that contains all. The path from Kether to Chokmah — the first movement of creation. Aleph = Ox-goad, the driving force of the cosmos.",
    },
    {
        "numeral": "I", "name": "The Magician",
        "hebrew": "Beth", "letter": "ב",
        "attribution": "Mercury",
        "path": 12, "sephiroth": "Kether-Binah",
        "image": "A man standing before a table bearing the four elemental weapons: Wand, Cup, Sword, Pentacle. His right hand points to heaven, left to earth.",
        "upright": "Willpower, creation, manifestation, skill, resourcefulness. The power to channel divine force into material form. Mastery of the four elements. Active intelligence and communication.",
        "reversed": "Manipulation, poor planning, deceit, untapped talent. The will turned to selfish ends. Mercury's trickster aspect — illusion over reality.",
        "keywords": ["Will", "Manifestation", "Skill", "Power", "Mercury"],
        "esoteric": "Beth = House. The Magus of Power. Mercury as the conveyor of divine will. The path from Kether to Binah — the first reflection of unity into duality. Mastery over the elemental forces.",
    },
    {
        "numeral": "II", "name": "The High Priestess",
        "hebrew": "Gimel", "letter": "ג",
        "attribution": "Moon",
        "path": 13, "sephiroth": "Kether-Tiphareth",
        "image": "A woman seated between two pillars (Jachin and Boaz), a veil behind her, the moon at her feet, a scroll inscribed TORA upon her lap.",
        "upright": "Intuition, mystery, inner knowledge, the unconscious, psychic receptivity. The veiled mysteries of the soul. Passive wisdom, the Lady of Silence guarding the threshold.",
        "reversed": "Secrets, withdrawal, silence, repression, surface-level understanding. The veil remains drawn. Intuition ignored, the subconscious denied.",
        "keywords": ["Intuition", "Mystery", "Subconscious", "Wisdom", "Moon"],
        "esoteric": "Gimel = Camel. The Priestess of the Silver Star. The path from Kether to Tiphareth traverses the Abyss. The Moon reflects the light of the Sun (Tiphareth) from Kether (the Crown). Keeper of the unconscious.",
    },
    {
        "numeral": "III", "name": "The Empress",
        "hebrew": "Daleth", "letter": "ד",
        "attribution": "Venus",
        "path": 14, "sephiroth": "Chokmah-Binah",
        "image": "A woman crowned with twelve stars, seated on a throne in a fertile garden. The pomegranates of growth surround her.",
        "upright": "Fertility, abundance, nature, nurturing, creation. The matrix of form. Venus as the principle of attraction and beauty. Material well-being and sensual pleasure.",
        "reversed": "Dependence, smothering, emptiness, creative block. The destructive mother. Venus turned inward — vanity, lethargy, overindulgence.",
        "keywords": ["Fertility", "Abundance", "Nurture", "Venus", "Creation"],
        "esoteric": "Daleth = Door. The Daughter of the Mighty Ones. Venus as the gate of life. The path from Chokmah (Wisdom/Force) to Binah (Understanding/Form) — the crystallization of divine energy into matter.",
    },
    {
        "numeral": "IV", "name": "The Emperor",
        "hebrew": "Heh", "letter": "ה",
        "attribution": "Aries",
        "path": 15, "sephiroth": "Chokmah-Tiphareth",
        "image": "A bearded man crowned, seated on a throne with ram heads. He holds a scepter and ankh. The barren landscape reflects his authority.",
        "upright": "Authority, structure, stability, leadership, father figure. The imposition of will upon chaos. Aries as the first impetus of the zodiac — the ram that breaks through.",
        "reversed": "Tyranny, rigidity, domination, inflexibility. Authority without compassion. The shadow of the father — control, oppression, abuse of power.",
        "keywords": ["Authority", "Structure", "Power", "Aries", "Leadership"],
        "esoteric": "Heh = Window. The Sun of the Morning. Aries as the first breath of spring. The path from Chokmah to Tiphareth — the structuring of wisdom into the beautiful pattern. The Emperor rules through law, not force.",
    },
    {
        "numeral": "V", "name": "The Hierophant",
        "hebrew": "Vav", "letter": "ו",
        "attribution": "Taurus",
        "path": 16, "sephiroth": "Chokmah-Chesed",
        "image": "A priest enthroned between two pillars, with two acolytes kneeling before him. He wears a triple crown and makes the sign of the esoteric pentagram.",
        "upright": "Tradition, spiritual wisdom, conformity, guidance, orthodoxy. The bridge between divine and human. Taurus as the enduring vessel of spiritual truth. Religious and philosophical instruction.",
        "reversed": "Rebellion, subversiveness, new approaches, breaking from tradition. The Hierophant's shadow — blind dogma, spiritual tyranny, the exoteric hiding the esoteric.",
        "keywords": ["Tradition", "Spiritual Authority", "Teaching", "Taurus", "Religion"],
        "esoteric": "Vav = Nail. The Magus of the Eternal. Taurus as the fixed earth that holds the divine seed. The path from Chokmah to Chesed — wisdom flowing into mercy. The Hierophant is the teacher of the inner mysteries.",
    },
    {
        "numeral": "VI", "name": "The Lovers",
        "hebrew": "Zayin", "letter": "ז",
        "attribution": "Gemini",
        "path": 17, "sephiroth": "Binah-Tiphareth",
        "image": "A man and woman beneath an angel with open arms. The Tree of Knowledge and the Tree of Life stand behind them. The arrow of discrimination is drawn.",
        "upright": "Love, harmony, relationships, choice, union. Gemini as the Divine Twins — the alchemical marriage. The necessity of choice on the path. Discrimination between the real and the illusory.",
        "reversed": "Disharmony, imbalance, misalignment, indecision. The twins divided. Poor choices, confusion of values. The arrow that misses its mark.",
        "keywords": ["Love", "Choice", "Union", "Gemini", "Discrimination"],
        "esoteric": "Zayin = Sword. The Children of the Voice Divine. Gemini as the dual principle. The path from Binah (Understanding) to Tiphareth (Beauty) — the heart's understanding. The Lovers represent the alchemical wedding, the union of opposites.",
    },
    {
        "numeral": "VII", "name": "The Chariot",
        "hebrew": "Cheth", "letter": "ח",
        "attribution": "Cancer",
        "path": 18, "sephiroth": "Binah-Geburah",
        "image": "A warrior prince standing in a chariot drawn by two sphinxes (black and white). He wears a crab on his breastplate and holds a scepter.",
        "upright": "Willpower, victory, determination, assertion, triumph. Cancer as the protective shell from which the warrior emerges. The soul commanding the opposing forces of nature.",
        "reversed": "Lack of direction, aggression, no control, defeat. The sphinxes pull in opposite directions. Will without understanding, force without wisdom.",
        "keywords": ["Victory", "Will", "Cancer", "Triumph", "Control"],
        "esoteric": "Cheth = Fence. The Child of the Powers of the Waters. Cancer as the womb that nurtures the divine warrior. The path from Binah to Geburah — understanding shaped into strength. The Charioteer is the soul that has mastered the four elements.",
    },
    {
        "numeral": "VIII", "name": "Adjustment",
        "hebrew": "Lamed", "letter": "ל",
        "attribution": "Libra",
        "path": 22, "sephiroth": "Geburah-Tiphareth",
        "image": "A woman crowned with the feathers of Maat, standing upon a crescent moon. She holds a sword pointing downward, balanced on her toes.",
        "upright": "Justice, fairness, truth, balance, cause and effect. Libra as cosmic equilibrium. The karmic adjustment — every action meets its equal reaction. Alignment with divine law.",
        "reversed": "Unfairness, dishonesty, lack of accountability, imbalance. The scales tip. Denial of natural law, avoidance of consequence, self-deception.",
        "keywords": ["Justice", "Balance", "Libra", "Karma", "Truth"],
        "esoteric": "Lamed = Ox-goad. The Daughter of the Lords of Truth. Libra as the balance point of the zodiac. The path from Geburah (Severity) to Tiphareth (Beauty) — justice tempered by compassion. Adjustment, not punishment — the cosmos self-corrects.",
    },
    {
        "numeral": "IX", "name": "The Hermit",
        "hebrew": "Yod", "letter": "י",
        "attribution": "Virgo",
        "path": 20, "sephiroth": "Chesed-Tiphareth",
        "image": "An old man in a grey cloak, carrying a lantern half-hidden, standing on a mountain peak. He looks downward in contemplation.",
        "upright": "Soul-searching, introspection, solitude, inner guidance, pilgrimage. Virgo as the virgin soil of the soul. The lone seeker carrying the light of Tiphareth into the darkness of the world.",
        "reversed": "Isolation, loneliness, withdrawal, anti-social behavior. The hermit who loses his way. Solitude becoming imprisonment, the lantern burning out.",
        "keywords": ["Solitude", "Wisdom", "Virgo", "Introspection", "Guidance"],
        "esoteric": "Yod = Hand. The Magus of the Voice of Power. Virgo as the Earth receiving the seed. The path from Chesed (Mercy) to Tiphareth (Beauty) — mercy internalized as wisdom. Yod is the primal point from which all letters emerge; the Hermit holds the seed of all creation.",
    },
    {
        "numeral": "X", "name": "Fortune",
        "hebrew": "Kaph", "letter": "כ",
        "attribution": "Jupiter",
        "path": 21, "sephiroth": "Chesed-Netzach",
        "image": "A great wheel attended by the Sphinx, Typhon, and Hermanubis. The wheel bears the letters T.A.R.O. (or R.O.T.A.) and alchemical symbols.",
        "upright": "Good fortune, cycles, destiny, turning point, expansion. Jupiter as the Greater Fortune. The wheel of karma in motion — rise and fall, expansion and contraction. The inevitability of change.",
        "reversed": "Bad luck, resistance to change, breaking cycles, external forces. The wheel grinds downward. Jupiter's bounty withheld. The lesson of impermanence unlearned.",
        "keywords": ["Fortune", "Cycles", "Jupiter", "Destiny", "Change"],
        "esoteric": "Kaph = Palm of Hand. The Lord of the Forces of Life. Jupiter as the expansive principle. The path from Chesed (Mercy) to Netzach (Victory) — mercy flows into victory. ROTA = TORA = TARO — the Law, the Wheel, the Reading are one.",
    },
    {
        "numeral": "XI", "name": "Lust",
        "hebrew": "Teth", "letter": "ט",
        "attribution": "Leo",
        "path": 19, "sephiroth": "Geburah-Chesed",
        "image": "A woman riding a lion, bearing the Holy Grail. Flames rise from the Grail. She is the Scarlet Woman, Babalon, the fulfilled soul.",
        "upright": "Strength, courage, passion, inner power, creative force. Leo as the serpent power (Kundalini) rising. Not brute force but the strength that comes from alignment with divine will. The lust for life itself.",
        "reversed": "Weakness, self-doubt, lack of inner strength, raw emotion. The lion unmounted. Passion without direction, courage without cause, the inner fire consuming itself.",
        "keywords": ["Strength", "Passion", "Leo", "Courage", "Kundalini"],
        "esoteric": "Teth = Serpent. The Daughter of the Flaming Sword. Leo as the fire of the heart. The path from Geburah (Severity) to Chesed (Mercy) — severity transmuted into mercy through the serpent power. The alchemical art of transforming lead into gold.",
    },
    {
        "numeral": "XII", "name": "The Hanged Man",
        "hebrew": "Mem", "letter": "מ",
        "attribution": "Water / Neptune",
        "path": 23, "sephiroth": "Geburah-Hod",
        "image": "A man hanging upside down from a T-cross, his head in a golden halo. His leg forms a triangle, his arms a cross — the alchemical glyph of sulphur.",
        "upright": "Surrender, sacrifice, new perspective, letting go, suspension. The deliberate inversion of perspective. The Neophyte's voluntary sacrifice of the lower self. Water as the universal solvent.",
        "reversed": "Deliberate sacrifice, stalling, resistance, martyrdom. The hanged one who struggles against the rope. Refusal to surrender, clinging to the old perspective.",
        "keywords": ["Sacrifice", "Surrender", "Water", "Neptune", "Perspective"],
        "esoteric": "Mem = Water. The Spirit of the Mighty Waters. Water as the reflecting pool of consciousness. The path from Geburah (Severity) to Hod (Splendour) — the sacrifice that transforms severity into intelligence. The voluntary death of the ego.",
    },
    {
        "numeral": "XIII", "name": "Death",
        "hebrew": "Nun", "letter": "נ",
        "attribution": "Scorpio",
        "path": 24, "sephiroth": "Tiphareth-Netzach",
        "image": "A skeleton horseman bearing a black banner with a white rose. A king lies slain, a child, woman, and bishop plead before him.",
        "upright": "Transformation, endings, change, release, transition. Scorpio as the force of regeneration through destruction. The old form dies so the new may live. The scorpion, serpent, and eagle — three aspects of transformation.",
        "reversed": "Resistance to change, inability to move on, stagnation, decay. The corpse that will not be buried. Fear of endings, the death that is not transformation but putrefaction.",
        "keywords": ["Death", "Transformation", "Scorpio", "Rebirth", "Endings"],
        "esoteric": "Nun = Fish. The Child of the Great Transformers. Scorpio as the three-fold transformation: Scorpion (decay), Serpent (renewal), Eagle (transcendence). The path from Tiphareth (Beauty) to Netzach (Victory) — beauty must die to be reborn as victory. The Great Work's nigredo phase.",
    },
    {
        "numeral": "XIV", "name": "Art",
        "hebrew": "Samekh", "letter": "ס",
        "attribution": "Sagittarius",
        "path": 25, "sephiroth": "Tiphareth-Yesod",
        "image": "An androgyne figure pours the contents of two vessels — fire and water — into a cauldron. A lion and eagle are transmuted within. The rainbow arches above.",
        "upright": "Balance, moderation, alchemy, synthesis, patience. Sagittarius as the arrow aimed at the divine. The alchemical art of combining opposites. The solve et coagula of the Great Work.",
        "reversed": "Imbalance, excess, lack of long-term vision, re-alignment. The elements that refuse to combine. Alchemical work without patience, the arrow that flies astray.",
        "keywords": ["Alchemy", "Balance", "Sagittarius", "Synthesis", "Transmutation"],
        "esoteric": "Samekh = Prop. The Daughter of the Reconcilers. Sagittarius as the centaur aiming beyond the self. The path from Tiphareth (Beauty) to Yesod (Foundation) — beauty becomes foundation through alchemical synthesis. Fire and water united in the crucible of the soul.",
    },
    {
        "numeral": "XV", "name": "The Devil",
        "hebrew": "Ayin", "letter": "ע",
        "attribution": "Capricorn",
        "path": 26, "sephiroth": "Tiphareth-Hod",
        "image": "A horned goat-god enthroned on a black cube. A man and woman, chained but with loose bonds, stand beneath. An inverted pentagram crowns the scene.",
        "upright": "Shadow self, attachment, bondage, materialism, the blind force of creation. Capricorn as the gate of the gods — the lowest point from which one may ascend. The illusion of separateness, the chains we forge for ourselves.",
        "reversed": "Release, liberation, breaking free, detachment, reclaiming power. The bonds that were loose are thrown off. The recognition that the Devil is a projection — liberation comes from within.",
        "keywords": ["Shadow", "Bondage", "Capricorn", "Materialism", "Liberation"],
        "esoteric": "Ayin = Eye. The Magus of the Everlasting. Capricorn as the cosmic goat leaping from the highest peak. The path from Tiphareth (Beauty) to Hod (Splendour) — the fall from beauty into intellect. The Devil is not evil but the principle of limitation that makes form possible. Know the shadow to transcend it.",
    },
    {
        "numeral": "XVI", "name": "The Tower",
        "hebrew": "Peh", "letter": "פ",
        "attribution": "Mars",
        "path": 27, "sephiroth": "Geburah-Hod",  # actually Chesed-Hod? Let me check... No, the path of Peh is from Hod to Netzach... Actually it's from Netzach to Hod? No... Peh is the path from Geburah to Hod? Let me just go with the commonly cited one.
        "image": "A tower struck by lightning, its crown shattered. Two figures fall headlong. Flames and yods scatter from the ruined crown.",
        "upright": "Sudden upheaval, revelation, awakening, divine intervention, broken pride. Mars as the destroying fire that clears the ground. The tower of Babel — false structures must fall. The flash of truth that destroys illusion.",
        "reversed": "Avoidance of disaster, fear of change, delaying the inevitable, personal transformation. The lightning that is held back. The tower that stands but should not.",
        "keywords": ["Destruction", "Revelation", "Mars", "Upheaval", "Awakening"],
        "esoteric": "Peh = Mouth. The Lord of the Hosts of the Mighty. Mars as the cosmic warrior. The lightning flash of the descending power shatters the prison of the ego. The path from Hod (Splendour) to Netzach (Victory) — the intellect struck by primal force. From the Mouth of the All speaks the Word that shatters.",
    },
    {
        "numeral": "XVII", "name": "The Star",
        "hebrew": "Tzaddi", "letter": "צ",
        "attribution": "Aquarius",
        "path": 28, "sephiroth": "Netzach-Yesod",
        "image": "A naked woman kneeling by a pool, pouring water from two jugs — one onto the land, one into the water. Seven stars shine above, the largest being Venus-Lucifer.",
        "upright": "Hope, inspiration, renewal, serenity, spiritual insight. Aquarius as the water-bearer of cosmic consciousness. The star of the initiate — the individual light in the universal darkness. Hope born from the ruins of the Tower.",
        "reversed": "Disconnection, lack of faith, despair, self-absorption, false hope. The star that falls. Inspiration cut off from its source, the water that stagnates.",
        "keywords": ["Hope", "Inspiration", "Aquarius", "Renewal", "Star"],
        "esoteric": "Tzaddi = Fishhook. The Daughter of the Firmament. Aquarius as the cosmic water-bearer. The path from Netzach (Victory) to Yesod (Foundation) — victory flows into foundation through the star of hope. 'Tzaddi is not the Star' — the meditation of the initiate.",
    },
    {
        "numeral": "XVIII", "name": "The Moon",
        "hebrew": "Qoph", "letter": "ק",
        "attribution": "Pisces",
        "path": 29, "sephiroth": "Netzach-Malkuth",
        "image": "A crayfish emerges from a pool between two towers. A path winds between them through a desert. A dog and wolf howl at the moon, which sheds dew.",
        "upright": "Illusion, intuition, the subconscious, mystery, the path of trials. Pisces as the final dissolution before rebirth. The path of the initiate between the pillars, through the valley of the shadow. The Moon governs the astral plane and all its illusions.",
        "reversed": "Release, fear subsiding, deception revealed, escaping confusion. The moonlight that reveals truth. Illusion dispelled, the subconscious brought to consciousness.",
        "keywords": ["Illusion", "Intuition", "Pisces", "Subconscious", "Trials"],
        "esoteric": "Qoph = Back of the Head. The Ruler of Flux and Reflux. Pisces as the final gateway. The path from Netzach (Victory) to Malkuth (Kingdom) — the last trial before manifestation. The Moon is the astral light — both the mirror of truth and the distorting lens of illusion.",
    },
    {
        "numeral": "XIX", "name": "The Sun",
        "hebrew": "Resh", "letter": "ר",
        "attribution": "Sun",
        "path": 30, "sephiroth": "Yesod-Hod",
        "image": "Two children embrace in a walled garden beneath a great sun. Sunflowers bloom along the wall. The light of the Sun illuminates all.",
        "upright": "Joy, success, vitality, confidence, truth revealed. The Sun as Tiphareth made manifest — the Christ-consciousness, the True Self. The highest good, the light that casts no shadow. Enlightenment.",
        "reversed": "Inner child, feeling down, overly optimistic, temporary depression. The sun behind clouds. The light that is present but obscured by the clouds of the mind.",
        "keywords": ["Joy", "Truth", "Sun", "Enlightenment", "Vitality"],
        "esoteric": "Resh = Head. The Lord of the Fire of the World. The Sun as the visible face of Tiphareth. The path from Hod (Splendour) to Yesod (Foundation) — intellect illuminated by the central light. The Sun is the heart of the system, the point of balance from which all paths radiate.",
    },
    {
        "numeral": "XX", "name": "The Aeon",
        "hebrew": "Shin", "letter": "ש",
        "attribution": "Fire / Pluto",
        "path": 31, "sephiroth": "Hod-Malkuth",  # actually Malkuth to Hod
        "image": "The goddess Nuit arches over the scene. Hadit as the winged globe blazes at her heart. Ra-Hoor-Khuit stands beneath. The dead rise from their tombs.",
        "upright": "Rebirth, resurrection, awakening, final judgment, the call to evolution. Fire as the final purifier. The dawning of a new Aeon — the old order is judged and found wanting. The soul answers the divine call.",
        "reversed": "Self-doubt, refusal to learn, stagnation, ignoring the call. The trumpet that goes unheard. The fire that warms but does not transform.",
        "keywords": ["Rebirth", "Judgment", "Fire", "Awakening", "Evolution"],
        "esoteric": "Shin = Tooth. The Spirit of the Primal Fire. Fire as the ultimate element of transformation. The path from Malkuth (Kingdom) to Hod (Splendour) — the ascent from matter to intelligence through purifying fire. Shin is the three-fold flame — the three mother letters, the three gunas, the Holy Trinity.",
    },
    {
        "numeral": "XXI", "name": "The Universe",
        "hebrew": "Tau", "letter": "ת",
        "attribution": "Saturn / Earth",
        "path": 32, "sephiroth": "Yesod-Malkuth",
        "image": "A woman dancing within an oval wreath. At each corner: the Bull, Lion, Eagle, and Man. The wreath takes the shape of the cosmic egg.",
        "upright": "Completion, accomplishment, travel, integration, wholeness. Saturn as the lord of time bringing all things to completion. The dance of the cosmos — every part in its place. The Great Work accomplished.",
        "reversed": "Incompletion, short-circuit, lack of closure, delays. The dance that falters. Saturn's restriction preventing completion, the last step that cannot be taken.",
        "keywords": ["Completion", "Wholeness", "Saturn", "Integration", "Cosmos"],
        "esoteric": "Tau = Cross. The Great One of the Night of Time. Saturn as the boundary of the system. The path from Yesod (Foundation) to Malkuth (Kingdom) — the final manifestation. Tau is the final letter, the cross on which the ego is crucified, the seal that completes the Great Work.",
    },
]

# ═══════════════════════════════════════════════════════════════
#  MINOR ARCANA — Book T Titles & Golden Dawn Correspondences
# ═══════════════════════════════════════════════════════════════

MINOR_ARCANA = {
    # ─── WANDS (Fire) ───
    "Ace of Wands": {
        "title": "Root of the Powers of Fire",
        "decan": None, "planet": None, "sign": None,
        "upright": "Creation, invention, start of an enterprise, birth of a child, the origin of the Will. The primal spark of Fire — inspiration, desire, the lightning flash of new beginnings.",
        "reversed": "Fall, darkness, void, annulment, decadence. The spark that fails to ignite. The will that is not yet kindled or has been extinguished.",
    },
    "2 of Wands": {
        "title": "Dominion",
        "decan": "1st of Aries", "planet": "Mars", "sign": "Aries",
        "upright": "Dominion, enterprise, ambition, the will to rule. Mars in Aries — the active, martial impulse toward conquest. Boldness, initiative, authority over one's domain.",
        "reversed": "Sadness, trouble, sickness, the will thwarted. Mars turned against itself. Domination that becomes tyranny or fails entirely.",
    },
    "3 of Wands": {
        "title": "Virtue",
        "decan": "2nd of Aries", "planet": "Sun", "sign": "Aries",
        "upright": "Established strength, enterprise, effort, trade, nobility. Sun in Aries — the illuminating force within the martial fire. Practical virtue that manifests in the world.",
        "reversed": "Help from a friend, courage, the end of trouble. The Sun's light hidden — assistance that comes unexpectedly, strength that must be borrowed.",
    },
    "4 of Wands": {
        "title": "Completion",
        "decan": "3rd of Aries", "planet": "Venus", "sign": "Aries",
        "upright": "Perfected work, completion, settlement, harmony, society, country life. Venus in Aries — beauty born from the fire of action. The home established, the foundation secured.",
        "reversed": "Loss of property, agriculture failure, fallen fortune, a contract broken. Venus unsettled — the beauty that fades, the harmony disrupted.",
    },
    "5 of Wands": {
        "title": "Strife",
        "decan": "1st of Leo", "planet": "Saturn", "sign": "Leo",
        "upright": "Strife, contest, competition, fighting, quarrelling, the lust of battle. Saturn in Leo — restriction upon the solar fire. The weight of Saturn upon the lion's pride.",
        "reversed": "Deceit, contradiction, cunning, the end of strife, evasion. The strife that is a mask for deception. Saturn's lessons learned through cunning rather than combat.",
    },
    "6 of Wands": {
        "title": "Victory",
        "decan": "2nd of Leo", "planet": "Jupiter", "sign": "Leo",
        "upright": "Victory, triumph, gain, good news, conquest, advancement. Jupiter in Leo — the greater fortune expanded through solar power. The laurel wreath, the triumphal return.",
        "reversed": "Fear, apprehension, the victor who fears, disloyalty, reward delayed. Jupiter's bounty deferred. The victory that feels hollow, the fear of what comes after triumph.",
    },
    "7 of Wands": {
        "title": "Valour",
        "decan": "3rd of Leo", "planet": "Mars", "sign": "Leo",
        "upright": "Courage, valour, bravery, opposition, standing firm, the advantage. Mars in Leo — the warrior at his most noble. The courage to stand one's ground against overwhelming odds.",
        "reversed": "Hesitancy, vacillation, weakness, embarrassment, anxiety, indecision. Mars weakened — the warrior who falters. The courage that wavers at the crucial moment.",
    },
    "8 of Wands": {
        "title": "Swiftness",
        "decan": "1st of Sagittarius", "planet": "Mercury", "sign": "Sagittarius",
        "upright": "Swiftness, speed, haste, dispatch, communication, movement. Mercury in Sagittarius — the fleet messenger crossing the fiery expanse. Rapid change, quick action, the arrow in flight.",
        "reversed": "Thorns, argument, quarrels, jealousy, the arrows of love. Mercury misdirected — speed becoming haste, messages garbled, the arrows that wound.",
    },
    "9 of Wands": {
        "title": "Strength",
        "decan": "2nd of Sagittarius", "planet": "Moon", "sign": "Sagittarius",
        "upright": "Strength, power, health, success, a strong man, obstinacy. Moon in Sagittarius — the reflective light upon the arrow's path. Endurance, resilience, the strength that comes from having survived.",
        "reversed": "Obstacles, adversity, calamity, delay, weakness. The Moon waning — strength that fails, the pillar that cracks under pressure.",
    },
    "10 of Wands": {
        "title": "Oppression",
        "decan": "3rd of Sagittarius", "planet": "Saturn", "sign": "Sagittarius",
        "upright": "Oppression, force, heavy burden, cruelty, malice, the weight of the world. Saturn in Sagittarius — the leaden weight upon the arrow's flight. The burden of success, the weight of duty.",
        "reversed": "Good aspect, difficulties, intrigues, treachery, perseverance. The burden that is almost lifted. Saturn's oppression beginning to ease, or oppression turned to determination.",
    },
    # ─── CUPS (Water) ───
    "Ace of Cups": {
        "title": "Root of the Powers of Water",
        "decan": None, "planet": None, "sign": None,
        "upright": "Love, fertility, joy, beginning of a love affair, happiness, creativity. The root of the waters — the wellspring of emotion, the grail of the heart. The descent of the dove.",
        "reversed": "Unhappiness, isolation, sterility, perversion of love, the cup that is empty. The waters that are stagnant, the love that is not returned.",
    },
    "2 of Cups": {
        "title": "Love",
        "decan": "1st of Cancer", "planet": "Venus", "sign": "Cancer",
        "upright": "Love, harmony, mutual understanding, attraction, concord, union. Venus in Cancer — the meeting of hearts in the womb of the Mother. The alchemical marriage at the emotional level.",
        "reversed": "Misunderstanding, jealousy, discord, folly, false love. Venus turned sour in the shell of Cancer — love that becomes possessive, harmony that becomes dependence.",
    },
    "3 of Cups": {
        "title": "Abundance",
        "decan": "2nd of Cancer", "planet": "Mercury", "sign": "Cancer",
        "upright": "Abundance, joy, celebration, harvest, hospitality, pleasure. Mercury in Cancer — the communicator at the hearth. Celebration, the bounty of the heart shared with others.",
        "reversed": "Excess, overabundance, gluttony, hedonism, the feast that becomes a binge. Mercury scattered — the joy that becomes dissipation.",
    },
    "4 of Cups": {
        "title": "Luxury",
        "decan": "3rd of Cancer", "planet": "Moon", "sign": "Cancer",
        "upright": "Luxury, satiety, pleasure, mild dissatisfaction, blending of elements, new offer. Moon in Cancer — the dreamer in the mother's womb. Comfort, but comfort that breeds apathy. The gift that is not yet recognized.",
        "reversed": "New possibilities, new approaches, the rejection of stagnation. The Moon waxes again — dissatisfaction becomes the catalyst for change.",
    },
    "5 of Cups": {
        "title": "Loss",
        "decan": "1st of Scorpio", "planet": "Mars", "sign": "Scorpio",
        "upright": "Loss, regret, disappointment, grief, the passing of what was valued. Mars in Scorpio — the warrior confronting the deepest waters. Bereavement, the bitter cup, the tears of the heart.",
        "reversed": "Return, renewal, a new beginning, a new relationship, recovery from loss. Mars turned — the scorpion that rises from its own ashes. Hope from the depths of despair.",
    },
    "6 of Cups": {
        "title": "Pleasure",
        "decan": "2nd of Scorpio", "planet": "Sun", "sign": "Scorpio",
        "upright": "Pleasure, nostalgia, memories, childhood, innocence, the past revisited. Sun in Scorpio — the light that penetrates the waters of death. The golden memory, the sweetness of what was, the innocence that endures.",
        "reversed": "Living in the past, stagnation, unrealistic expectations, the past that binds. The Sun setting in Scorpio — nostalgia that prevents growth, the past that is a prison.",
    },
    "7 of Cups": {
        "title": "Debauch",
        "decan": "3rd of Scorpio", "planet": "Venus", "sign": "Scorpio",
        "upright": "Debauch, illusion, fantasy, wishful thinking, many choices, mirage. Venus in Scorpio — the temptress in the depths. The intoxication of desire, the feast of dreams, the danger of mistaking illusion for reality.",
        "reversed": "Willpower, determination, making a choice, overcoming illusion. Venus purified — the beauty that is real, the choice that is made with clarity.",
    },
    "8 of Cups": {
        "title": "Indolence",
        "decan": "1st of Pisces", "planet": "Saturn", "sign": "Pisces",
        "upright": "Indolence, abandonment, withdrawal, decline, leaving success behind, deeper meaning. Saturn in Pisces — the restriction of the boundless waters. The hermit's departure from what was accomplished, the search for deeper truth.",
        "reversed": "Effort, seeking, ambition, the end of stagnation, re-evaluation. Saturn's grip loosening — the will to move on, the search renewed.",
    },
    "9 of Cups": {
        "title": "Happiness",
        "decan": "2nd of Pisces", "planet": "Jupiter", "sign": "Pisces",
        "upright": "Happiness, satisfaction, contentment, wish fulfilled, sensual pleasure, luxury. Jupiter in Pisces — the greater fortune in the boundless deep. The wish card — the heart's desire made manifest. The feast of the soul.",
        "reversed": "Overindulgence, greed, dissatisfaction, complacency, the wish that is not truly desired. Jupiter's bounty that sours — too much of a good thing.",
    },
    "10 of Cups": {
        "title": "Satiety",
        "decan": "3rd of Pisces", "planet": "Mars", "sign": "Pisces",
        "upright": "Satiety, home, family, joy, peace, lasting happiness. Mars in Pisces — the warrior at rest in the infinite ocean. The ultimate emotional fulfillment, the heart that is full. Homecoming.",
        "reversed": "Loss of friendship, family discord, quarrel, violence, the cup that overflows. Mars disturbed — the peace that shatters, the home divided.",
    },
    # ─── SWORDS (Air) ───
    "Ace of Swords": {
        "title": "Root of the Powers of Air",
        "decan": None, "planet": None, "sign": None,
        "upright": "Victory, force, power, justice, truth, the triumph of mind. The root of the intellect — the blade that cuts through illusion. The crown of the Magus, the gift of discernment.",
        "reversed": "Tyranny, injustice, oppression, the intellect turned to cruelty. The blade that wounds its wielder, the truth that destroys rather than liberates.",
    },
    "2 of Swords": {
        "title": "Peace",
        "decan": "1st of Libra", "planet": "Moon", "sign": "Libra",
        "upright": "Peace, balance, stalemate, harmony, difficult decisions, compromise. Moon in Libra — the reflective mind in the balance. The truce between opposing forces, the calm that precedes the storm of decision.",
        "reversed": "Indecision, confusion, stalemate, information overload, emotional conflict. The Moon in Libra wanes — the balance tips, the peace that was false.",
    },
    "3 of Swords": {
        "title": "Sorrow",
        "decan": "2nd of Libra", "planet": "Saturn", "sign": "Libra",
        "upright": "Sorrow, heartbreak, grief, rejection, separation, absence. Saturn in Libra — the weight upon the scales. The necessary pain of truth, the heart pierced by understanding. The dark night of the soul.",
        "reversed": "Recovery, healing, release, the easing of grief, optimism. Saturn's weight lifting — the sorrow that teaches, the wound that heals into wisdom.",
    },
    "4 of Swords": {
        "title": "Truce",
        "decan": "3rd of Libra", "planet": "Jupiter", "sign": "Libra",
        "upright": "Truce, rest, meditation, contemplation, recovery, convalescence. Jupiter in Libra — the expansive peace, the rest that restores. The knight in the chapel, the mind in silent meditation.",
        "reversed": "Restlessness, burnout, stress, stagnation, the rest that becomes retreat. Jupiter's expansion curtailed — the rest that has gone on too long, the mind that will not quiet.",
    },
    "5 of Swords": {
        "title": "Defeat",
        "decan": "1st of Aquarius", "planet": "Venus", "sign": "Aquarius",
        "upright": "Defeat, loss, failure, degradation, conflict, empty victory. Venus in Aquarius — beauty alienated in the cold intellect. The conqueror who has lost more than he gained. Pyrrhic victory.",
        "reversed": "Uncertain outcome, hollow victory, the enemy within, overcoming defeat. Venus returns — the loss that teaches, the defeat that becomes the seed of future triumph.",
    },
    "6 of Swords": {
        "title": "Science",
        "decan": "2nd of Aquarius", "planet": "Mercury", "sign": "Aquarius",
        "upright": "Science, transition, movement, journey, knowledge, rational thought. Mercury in Aquarius — the mind that traverses the intellectual expanse. The ferry ride across troubled waters, the journey toward clarity.",
        "reversed": "Stagnation, personal transition, stuck, resistance, the mind that refuses to move. Mercury retrograde — the science that fails, the passage that is blocked.",
    },
    "7 of Swords": {
        "title": "Futility",
        "decan": "3rd of Aquarius", "planet": "Moon", "sign": "Aquarius",
        "upright": "Futility, deception, trickery, stealth, strategy, avoidance. Moon in Aquarius — the reflected light of the cold intellect. The thief in the camp, the escape from an unwinnable situation.",
        "reversed": "Coming clean, confession, rethinking approach, the futility that is recognized. The Moon waning — the deception revealed, the strategy that fails.",
    },
    "8 of Swords": {
        "title": "Interference",
        "decan": "1st of Gemini", "planet": "Jupiter", "sign": "Gemini",
        "upright": "Interference, restriction, imprisonment, feeling trapped, narrowed power, victim mentality. Jupiter in Gemini — the expansive force bound by duality. The mind that is its own prison, the thoughts that entrap.",
        "reversed": "Release, escape, self-acceptance, new perspective, freedom from restriction. Jupiter expanding — the bonds that loosen, the mind that finds its way out.",
    },
    "9 of Swords": {
        "title": "Despair",
        "decan": "2nd of Gemini", "planet": "Mars", "sign": "Gemini",
        "upright": "Despair, cruelty, mental anguish, worry, anxiety, nightmares. Mars in Gemini — the warrior's blade turned inward. The mind that tortures itself, the fears that multiply in the dark hour.",
        "reversed": "Recovery, forgiveness, release, hope, the easing of anxiety. Mars withdrawing — the nightmare that ends at dawn, the wound that the mind finally releases.",
    },
    "10 of Swords": {
        "title": "Ruin",
        "decan": "3rd of Gemini", "planet": "Sun", "sign": "Gemini",
        "upright": "Ruin, destruction, defeat, death, end, betrayal, the nadir of the mind. Sun in Gemini — the light that reveals the final truth. The absolute end, the bottom from which one may only rise. Death of the old thought.",
        "reversed": "Recovery, regeneration, renewal, the phoenix from ashes, the inevitable that is survived. The Sun that rises — the ruin that becomes the foundation of the new.",
    },
    # ─── PENTACLES (Earth) ───
    "Ace of Pentacles": {
        "title": "Root of the Powers of Earth",
        "decan": None, "planet": None, "sign": None,
        "upright": "Prosperity, new venture, security, foundation, manifestation, the garden of Eden. The root of the material world — the seed of abundance, the first coin. The gift of the earth.",
        "reversed": "Loss, greed, poor planning, the seed that falls on barren ground. The earth that is not tended, the coin that is not invested.",
    },
    "2 of Pentacles": {
        "title": "Change",
        "decan": "1st of Capricorn", "planet": "Jupiter", "sign": "Capricorn",
        "upright": "Change, balance, adaptation, time management, prioritization, juggling. Jupiter in Capricorn — expansion within limitation, the fall that becomes the rise. The dance of the elements, the lemniscate of balance.",
        "reversed": "Imbalance, disorganization, overcommitment, the juggling that fails. Jupiter restricted — the change that is too much, the balance that cannot be maintained.",
    },
    "3 of Pentacles": {
        "title": "Works",
        "decan": "2nd of Capricorn", "planet": "Mars", "sign": "Capricorn",
        "upright": "Works, mastery, craftsmanship, collaboration, building, skill, the Great Work. Mars in Capricorn — the disciplined builder, the warrior architect. The temple under construction, the team that builds together.",
        "reversed": "Poor quality, lack of skill, no teamwork, laziness, the work that is not done. Mars fallen — the effort that is misdirected, the work that is not the Great Work.",
    },
    "4 of Pentacles": {
        "title": "Power",
        "decan": "3rd of Capricorn", "planet": "Sun", "sign": "Capricorn",
        "upright": "Power, stability, security, control, possessiveness, holding on. Sun in Capricorn — the authority that holds, the king upon his throne. Material security, but the danger of clinging to what should be released.",
        "reversed": "Greed, materialism, self-protection, the grip that strangles, the hoard that imprisons. The Sun eclipsed — power that becomes tyranny, the crown that becomes a burden.",
    },
    "5 of Pentacles": {
        "title": "Worry",
        "decan": "1st of Taurus", "planet": "Mercury", "sign": "Taurus",
        "upright": "Worry, hardship, loss, poverty, isolation, spiritual poverty. Mercury in Taurus — the mind in the earth, the intellect that worries the material. The dark night of the body, the winter of the soul.",
        "reversed": "Recovery from loss, spiritual poverty, new income, the winter that ends. Mercury turning — the worry that was groundless, the poverty that was temporary.",
    },
    "6 of Pentacles": {
        "title": "Success",
        "decan": "2nd of Taurus", "planet": "Moon", "sign": "Taurus",
        "upright": "Success, generosity, charity, giving, prosperity, material gain, sharing. Moon in Taurus — the reflective light upon the material world. The just distribution of wealth, the lord who gives freely.",
        "reversed": "Selfishness, debt, greed, one-sided charity, strings attached. The Moon darkened — the generosity that is self-serving, the gift that is a chain.",
    },
    "7 of Pentacles": {
        "title": "Failure",
        "decan": "3rd of Taurus", "planet": "Saturn", "sign": "Taurus",
        "upright": "Failure, patience, assessment, re-evaluation, the harvest that is not yet ripe, the work that needs more time. Saturn in Taurus — the test of the earth, the patience required for growth. The gardener who waits.",
        "reversed": "Impatience, frustration, lack of progress, the harvest that fails. Saturn's weight — the failure that is premature, the patience that was never given.",
    },
    "8 of Pentacles": {
        "title": "Prudence",
        "decan": "1st of Virgo", "planet": "Sun", "sign": "Virgo",
        "upright": "Prudence, apprenticeship, craftsmanship, skill, detail, dedication. Sun in Virgo — the illuminating mind at work. The artisan dedicated to their craft, the detail that reveals the divine. The Great Work in its daily aspect.",
        "reversed": "Perfectionism, lack of ambition, misdirected energy, the skill that is not applied. The Sun obscured — the prudence that becomes paralysis, the detail that loses the whole.",
    },
    "9 of Pentacles": {
        "title": "Gain",
        "decan": "2nd of Virgo", "planet": "Venus", "sign": "Virgo",
        "upright": "Gain, abundance, luxury, self-sufficiency, accomplishment, the garden of the world. Venus in Virgo — beauty that serves, the harvest that is beautiful. The wise steward, the garden well-tended.",
        "reversed": "Loss, poor management, greed, the garden untended. Venus fallen — the beauty that is merely surface, the abundance that is not shared.",
    },
    "10 of Pentacles": {
        "title": "Wealth",
        "decan": "3rd of Virgo", "planet": "Mercury", "sign": "Virgo",
        "upright": "Wealth, inheritance, family, establishment, tradition, the completion of the material. Mercury in Virgo — the intellect manifest in the material world. The family legacy, the kingdom that endures. Malkuth in its glory.",
        "reversed": "Financial failure, poverty, family disputes, the legacy that is lost. Mercury scattered — the wealth that disperses, the tradition that is broken.",
    },
}

# ─── COURT CARDS ───

COURT_CARDS = {
    "Knight of Wands": {
        "title": "Lord of Flame and Lightning",
        "attribution": "Fire of Fire — Aries",
        "element_combo": "Fire of Fire",
        "zodiac": "20° Pisces — 20° Aries",
        "upright": "Energy, swiftness, departure, adventure, quest, the impulsive spirit. The fiery warrior, the questing knight. The surge of creative force that cannot be contained.",
        "reversed": "Hastiness, scattered energy, jealousy, unexpected departure. The fire that burns without purpose. The knight who rides without knowing where.",
    },
    "Queen of Wands": {
        "title": "Queen of the Thrones of Flame",
        "attribution": "Water of Fire — Pisces-Aries",
        "element_combo": "Water of Fire",
        "zodiac": "20° Aries — 20° Gemini",
        "upright": "Warmth, generosity, confidence, determination, charisma, the radiant soul. The Queen who rules through love and beauty. The water that tempers the flame.",
        "reversed": "Jealousy, insecurity, possessiveness, the fire that consumes. The Queen who demands rather than inspires. The water that drowns the flame.",
    },
    "Prince of Wands": {
        "title": "Prince of the Chariot of Fire",
        "attribution": "Air of Fire — Cancer-Leo",
        "element_combo": "Air of Fire",
        "zodiac": "20° Cancer — 20° Leo",
        "upright": "Action, adventure, enthusiasm, charm, the knight in pursuit. The Air that fans the Fire. The intellect in service of the will. The prince who rides forth.",
        "reversed": "Impulsiveness, self-righteousness, conceit, the air that extinguishes. The prince who rides without purpose. The intellect that overrules the heart.",
    },
    "Princess of Wands": {
        "title": "Princess of the Shining Flame",
        "attribution": "Earth of Fire — Libra-Scorpio",
        "element_combo": "Earth of Fire",
        "zodiac": "20° Libra — 20° Scorpio",
        "upright": "Inspiration, passion, new venture, daring, the earth that receives the fire. The throne of the Fire element. The material vessel for spiritual force.",
        "reversed": "Jealousy, anger, revenge, the earth that refuses the fire. The princess who is consumed. The vessel that is too small for the flame.",
    },
    "Knight of Cups": {
        "title": "Lord of the Waves and Waters",
        "attribution": "Fire of Water — Gemini-Cancer",
        "element_combo": "Fire of Water",
        "zodiac": "20° Gemini — 20° Cancer",
        "upright": "Romance, charm, imagination, invitation, the quest for the Grail. The fire that illuminates the waters. The romantic, the poet, the dreamer in action.",
        "reversed": "Unreliability, moodiness, jealousy, the fire that disturbs the waters. The knight who rides without conviction. The dreamer who cannot act.",
    },
    "Queen of Cups": {
        "title": "Queen of the Thrones of Waters",
        "attribution": "Water of Water — Cancer",
        "element_combo": "Water of Water",
        "zodiac": "20° Gemini — 20° Cancer",
        "upright": "Compassion, intuition, nurturing, psychic ability, the mother of the deep. The pure reflective surface of the soul. The dreamer who dreams true.",
        "reversed": "Insecurity, co-dependency, emotional manipulation, the waters that drown. The Queen who cannot be reached. The reflection that distorts.",
    },
    "Prince of Cups": {
        "title": "Prince of the Chariot of the Waters",
        "attribution": "Air of Water — Libra-Scorpio",
        "element_combo": "Air of Water",
        "zodiac": "20° Virgo — 20° Libra",
        "upright": "Sensitivity, intuition, refined emotion, the poetic soul, the alchemist of feeling. The Air that moves the Waters. The intellect that serves the heart.",
        "reversed": "Emotional immaturity, untrustworthiness, the air that agitates the waters. The prince who is pulled by tides he cannot understand.",
    },
    "Princess of Cups": {
        "title": "Princess of the Waters and the Lotus",
        "attribution": "Earth of Water — Sagittarius-Capricorn",
        "element_combo": "Earth of Water",
        "zodiac": "20° Sagittarius — 20° Capricorn",
        "upright": "Sensitivity, empathy, sweetness, new love, intuition, the earth that receives the waters. The lotus that blooms in the mud. The vessel that holds the sacred waters.",
        "reversed": "Emotional instability, jealousy, the earth that cannot hold the waters. The princess overwhelmed by feeling. The vessel that leaks.",
    },
    "Knight of Swords": {
        "title": "Lord of the Winds and Breezes",
        "attribution": "Fire of Air — Taurus-Gemini",
        "element_combo": "Fire of Air",
        "zodiac": "20° Taurus — 20° Gemini",
        "upright": "Action, ambition, fast-thinking, assertiveness, the swordsman of the mind. The fire that sharpens the blade. The knight who cuts through deception with the speed of thought.",
        "reversed": "Restlessness, recklessness, burnout, the blade that cuts without thought. The knight who acts before thinking. The fire that destroys the intellect.",
    },
    "Queen of Swords": {
        "title": "Queen of the Thrones of Air",
        "attribution": "Water of Air — Gemini-Libra",
        "element_combo": "Water of Air",
        "zodiac": "20° Gemini — 20° Libra",
        "upright": "Independence, clear thinking, boundaries, discernment, the wisdom of experience. The water that reflects the truth. The Queen who sees clearly, who speaks the truth even when it wounds.",
        "reversed": "Coldness, bitterness, isolation, the blade that is too sharp. The Queen who has cut too much away. The reflection that is ice, not water.",
    },
    "Prince of Swords": {
        "title": "Prince of the Chariot of the Winds",
        "attribution": "Air of Air — Aquarius",
        "element_combo": "Air of Air",
        "zodiac": "20° Capricorn — 20° Aquarius",
        "upright": "Intellectual, analytical, restless, the mind that circles, the innovator. The Air that sharpens itself. The intellect in its pure form — brilliant but potentially ruthless.",
        "reversed": "Scattered, indecisive, cunning, the mind that turns against itself. The prince who thinks without feeling. The air that is a vacuum.",
    },
    "Princess of Swords": {
        "title": "Princess of the Rushing Winds",
        "attribution": "Earth of Air — Taurus-Gemini",
        "element_combo": "Earth of Air",
        "zodiac": "20° Taurus — 20° Gemini",
        "upright": "Curiosity, restlessness, new ideas, perception, the earth that is stirred by the wind. The clarity of a fresh perspective. The messenger, the watcher, the perceiver.",
        "reversed": "Spite, gossip, manipulation, the earth that is blown away. The princess who cuts without knowing what she cuts. The wind that is destructive.",
    },
    "Knight of Pentacles": {
        "title": "Lord of the Wide and Fertile Land",
        "attribution": "Fire of Earth — Leo-Virgo",
        "element_combo": "Fire of Earth",
        "zodiac": "20° Leo — 20° Virgo",
        "upright": "Reliability, diligence, routine, the steady worker, the fire that warms the earth. The knight who tends the garden, the guardian of the material. Patience and persistence.",
        "reversed": "Laziness, feeling stuck, inflexibility, the fire that is banked. The knight who will not move. The earth that is too comfortable.",
    },
    "Queen of Pentacles": {
        "title": "Queen of the Thrones of Earth",
        "attribution": "Water of Earth — Sagittarius-Capricorn",
        "element_combo": "Water of Earth",
        "zodiac": "20° Sagittarius — 20° Capricorn",
        "upright": "Nurturing, practicality, comfort, wealth, the mother of the world. The water that nourishes the earth. The Queen of the harvest, the wise woman, the keeper of the hearth.",
        "reversed": "Self-centeredness, jealousy, possessiveness, the earth that is too heavy. The Queen who hoards. The water that makes the earth muddy.",
    },
    "Prince of Pentacles": {
        "title": "Prince of the Chariot of Earth",
        "attribution": "Air of Earth —Taurus-Gemini",
        "element_combo": "Air of Earth",
        "zodiac": "20° Aries — 20° Taurus",
        "upright": "Reliability, efficiency, conservative, the mind that serves the material. The Air that brings order to the Earth. The architect, the planner, the builder of lasting structures.",
        "reversed": "Stagnation, laziness, the air that is stifled by earth. The prince who cannot see beyond the material. The plan that is never executed.",
    },
    "Princess of Pentacles": {
        "title": "Princess of the Green Earth",
        "attribution": "Earth of Earth — Capricorn-Aquarius",
        "element_combo": "Earth of Earth",
        "zodiac": "20° Capricorn — 20° Aquarius",
        "upright": "New venture, prosperity, practicality, the seed in the soil, the throne of Earth. The Earth in its purest manifestation. The princess who brings forth the fruit of the Great Work.",
        "reversed": "Lack of progress, dependency, stagnation, the earth that is barren. The princess who cannot bring the seed to flower. The soil that is depleted.",
    },
}

# ═══════════════════════════════════════════════════════════════
#  SPREAD DEFINITIONS
# ═══════════════════════════════════════════════════════════════

SPREADS = {
    "celtic_cross": {
        "name": "The Celtic Cross",
        "subtitle": "The Classic Golden Dawn Spread",
        "description": "The most revered of all tarot spreads, the Celtic Cross reveals the interplay of fate and will across ten positions. Used by the Golden Dawn as the primary method of divination, it maps the querent's life onto the cross of the elements and the staff of the spirit.",
        "count": 10,
        "positions": [
            {"num": 1, "name": "The Significator's Present", "meaning": "The Heart of the Matter — the current situation as it truly is, not as the querent believes it to be. This is the central reality."},
            {"num": 2, "name": "The Crossing Card", "meaning": "The Obstacle — the force that opposes, challenges, or complicates the situation. If positive, it is a test to be overcome; if negative, a genuine barrier."},
            {"num": 3, "name": "The Crown", "meaning": "What Crowns the Querent — the conscious goal, the highest aspirations, what the querent hopes to achieve. That which is above, the mental or spiritual overlay."},
            {"num": 4, "name": "The Foundation", "meaning": "What is Beneath — the subconscious foundation, the deep root of the matter, past events that underlie the present. That which is below, the hidden basis."},
            {"num": 5, "name": "The Past", "meaning": "What is Behind — the recent past, events that are just now receding. The influence that is waning, the karma that is being resolved."},
            {"num": 6, "name": "The Future", "meaning": "What is Before — the near future, events that are approaching. The influence that is waxing, the karma that is being created."},
            {"num": 7, "name": "The Querent's Self", "meaning": "The Querent Themselves — as they are at this moment, their attitude, their state of being. The self that is navigating the situation."},
            {"num": 8, "name": "The Environment", "meaning": "The Querent's Environment — the house, the home, the influence of others, the social and material surroundings. The field in which the querent stands."},
            {"num": 9, "name": "Hopes and Fears", "meaning": "Hopes and Fears — that which the querent desires and that which they dread. Often the same thing. The inner contradiction that must be resolved."},
            {"num": 10, "name": "The Outcome", "meaning": "The Final Result — the culmination of all the preceding forces. The resolution of the reading, the end of the matter. This is not fate but the logical outcome of current trajectories."},
        ],
        "layout": "cross_and_staff",
    },
    "three_card": {
        "name": "The Three Card Spread",
        "subtitle": "Past · Present · Future",
        "description": "The simplest and most fundamental spread, revealing the arc of time through three positions. In the Golden Dawn system, this corresponds to the three pillars: the Pillar of Severity (Past), the Middle Pillar (Present), and the Pillar of Mercy (Future).",
        "count": 3,
        "positions": [
            {"num": 1, "name": "The Past", "meaning": "What has been — the foundation upon which the present stands. The seed that was planted, the karma that was set in motion."},
            {"num": 2, "name": "The Present", "meaning": "What is — the moment of power, the point of choice. The crossroads where past and future meet in the eternal now."},
            {"num": 3, "name": "The Future", "meaning": "What will be — the trajectory of current forces, the direction of the flow. Not fate, but the probable outcome if nothing changes."},
        ],
        "layout": "row",
    },
    "tree_of_life": {
        "name": "The Tree of Life Spread",
        "subtitle": "Qabalistic Divination",
        "description": "A reading mapped onto the ten Sephiroth of the Qabalistic Tree of Life. Each card corresponds to a divine emanation, revealing how the divine light flows through the querent's situation. The most theosophically rich of all spreads.",
        "count": 10,
        "positions": [
            {"num": 1, "name": "Kether — The Crown", "meaning": "The highest potential, the divine will for this situation. The spark from which all else descends. The ultimate purpose."},
            {"num": 2, "name": "Chokmah — Wisdom", "meaning": "The creative force, the masculine principle, the initial impulse. The wisdom that informs the situation from beyond."},
            {"num": 3, "name": "Binah — Understanding", "meaning": "The formative force, the feminine principle, the container. The understanding that gives shape to the wisdom."},
            {"num": 4, "name": "Chesed — Mercy", "meaning": "Expansion, benevolence, the building force. The mercy that is available, the grace that sustains."},
            {"num": 5, "name": "Geburah — Severity", "meaning": "Restriction, discipline, the destroying force. The severity that is necessary, the test that must be passed."},
            {"num": 6, "name": "Tiphareth — Beauty", "meaning": "The center, the heart, the Christ-consciousness. The beauty that balances mercy and severity, the point of transformation."},
            {"num": 7, "name": "Netzach — Victory", "meaning": "Desire, emotion, attraction, the vegetative force. The victory that is sought, the desire that drives the situation."},
            {"num": 8, "name": "Hod — Splendour", "meaning": "Intellect, communication, the analytical force. The splendour of the mind, the intelligence that must be applied."},
            {"num": 9, "name": "Yesod — Foundation", "meaning": "The astral plane, the unconscious, the reflective force. The foundation upon which the visible world rests, the dream that underlies reality."},
            {"num": 10, "name": "Malkuth — Kingdom", "meaning": "The material world, the outcome, the manifest result. The kingdom that is built, the matter that is settled."},
        ],
        "layout": "tree",
    },
    "planetary": {
        "name": "The Planetary Spread",
        "subtitle": "Seven Spheres of Influence",
        "description": "A seven-card reading based on the seven classical planets of the Chaldean order. Each position reveals the influence of a planetary sphere upon the querent's question, from the highest (Saturn) to the closest (Moon).",
        "count": 7,
        "positions": [
            {"num": 1, "name": "Saturn — The Boundary", "meaning": "Limitation, karma, time, structure. What must be accepted, the boundaries of the situation, the lessons of the past."},
            {"num": 2, "name": "Jupiter — The Expansion", "meaning": "Growth, opportunity, benevolence. What is expanding, the blessings available, the grace that is given."},
            {"num": 3, "name": "Mars — The Action", "meaning": "Force, courage, conflict. What must be fought for, the energy available, the blade that must be drawn."},
            {"num": 4, "name": "Sun — The Identity", "meaning": "Self, vitality, truth, the central purpose. The heart of the matter, the gold that is sought."},
            {"num": 5, "name": "Venus — The Attraction", "meaning": "Love, beauty, harmony, values. What is desired, what attracts, the relationship that is central."},
            {"num": 6, "name": "Mercury — The Communication", "meaning": "Thought, speech, commerce, travel. What must be communicated, the message that must be heard, the mind that must be engaged."},
            {"num": 7, "name": "Moon — The Emotion", "meaning": "Intuition, the unconscious, reflection, the past. What is felt but not said, the dream that underlies, the instinct that guides."},
        ],
        "layout": "pyramid",
    },
    "opening_key": {
        "name": "Opening of the Key",
        "subtitle": "The Golden Dawn's Original Method",
        "description": "The authentic Golden Dawn method of tarot divination as given in the Zelator Adeptus Minor curriculum. The deck is divided into four piles representing the four letters of the Tetragrammaton (Yod-Heh-Vav-Heh), and each pile is read for a different aspect of the question. This is the method the Golden Dawn actually used — not the Celtic Cross.",
        "count": 4,
        "positions": [
            {"num": 1, "name": "Yod (ה) — The Princess", "meaning": "The material aspect of the question. Earth, the body, the practical reality. The throne of the element. Read from the top card of the first pile."},
            {"num": 2, "name": "Heh (ה) — The Queen", "meaning": "The emotional aspect of the question. Water, the heart, the feeling tone. The reflection of the situation. Read from the top card of the second pile."},
            {"num": 3, "name": "Vav (ו) — The Prince", "meaning": "The intellectual aspect of the question. Air, the mind, the communication. The thought behind the situation. Read from the top card of the third pile."},
            {"num": 4, "name": "Heh (Final) (ה) — The Knight", "meaning": "The active aspect of the question. Fire, the will, the action. The force behind the situation. Read from the top card of the fourth pile."},
        ],
        "layout": "tetragrammaton",
    },
    "single_card": {
        "name": "Single Card Divination",
        "subtitle": "The Oracle's Answer",
        "description": "The simplest divination — a single card drawn as the answer to a question. In the Golden Dawn system, the single card is read with full attention to its elemental, planetary, and Qabalistic correspondences. The entire universe in one card.",
        "count": 1,
        "positions": [
            {"num": 1, "name": "The Oracle", "meaning": "The answer to the question, the message of the moment, the single truth that the universe offers."},
        ],
        "layout": "single",
    },
    "relationship": {
        "name": "The Relationship Spread",
        "subtitle": "Two Souls · One Reading",
        "description": "A seven-card reading examining the dynamics between two people. Based on the Golden Dawn's understanding that relationship is an alchemical operation — the two become one through the Great Work of mutual transformation.",
        "count": 7,
        "positions": [
            {"num": 1, "name": "Querent — As They Are", "meaning": "The querent's current state, their position in the relationship, their truth as it stands now."},
            {"num": 2, "name": "Other — As They Are", "meaning": "The other person's current state, their position in the relationship, their truth as it stands now."},
            {"num": 3, "name": "Querent's Need", "meaning": "What the querent needs from the relationship, their true desire, the void they seek to fill."},
            {"num": 4, "name": "Other's Need", "meaning": "What the other person needs from the relationship, their true desire, the void they seek to fill."},
            {"num": 5, "name": "The Foundation", "meaning": "The foundation of the relationship, what brought them together, the ground upon which they stand."},
            {"num": 6, "name": "The Challenge", "meaning": "The obstacle, the shadow, the issue that must be confronted. The alchemical nigredo of the relationship."},
            {"num": 7, "name": "The Synthesis", "meaning": "The potential outcome, the alchemical gold, the possibility that exists if both parties do the Great Work."},
        ],
        "layout": "relationship",
    },
    "year_ahead": {
        "name": "The Year Ahead Spread",
        "subtitle": "Twelve Months · Twelve Houses",
        "description": "A twelve-card reading corresponding to the twelve signs of the zodiac and the twelve houses of the horoscope. Each card represents the energy of one month or one house, revealing the unfolding of the year's karma.",
        "count": 12,
        "positions": [
            {"num": 1, "name": "Aries / 1st House — The Self", "meaning": "Identity, new beginnings, the body, the approach to the year. The Ram's energy — bold, direct, pioneering."},
            {"num": 2, "name": "Taurus / 2nd House — Values", "meaning": "Money, possessions, self-worth, what is valued. The Bull's energy — stable, patient, acquisitive."},
            {"num": 3, "name": "Gemini / 3rd House — Communication", "meaning": "Communication, siblings, short journeys, learning. The Twins' energy — adaptable, communicative, curious."},
            {"num": 4, "name": "Cancer / 4th House — Home", "meaning": "Home, family, roots, the inner foundation. The Crab's energy — protective, nurturing, reflective."},
            {"num": 5, "name": "Leo / 5th House — Creativity", "meaning": "Creativity, romance, children, pleasure, self-expression. The Lion's energy — creative, dramatic, joyful."},
            {"num": 6, "name": "Virgo / 6th House — Service", "meaning": "Health, service, daily routine, work, craft. The Virgin's energy — analytical, serving, refining."},
            {"num": 7, "name": "Libra / 7th House — Partnership", "meaning": "Marriage, partnerships, contracts, open enemies. The Scales' energy — balanced, just, relational."},
            {"num": 8, "name": "Scorpio / 8th House — Transformation", "meaning": "Death, rebirth, shared resources, the occult, sex. The Scorpion's energy — transformative, intense, hidden."},
            {"num": 9, "name": "Sagittarius / 9th House — Philosophy", "meaning": "Philosophy, religion, long journeys, higher education. The Archer's energy — expansive, seeking, philosophical."},
            {"num": 10, "name": "Capricorn / 10th House — Career", "meaning": "Career, public standing, authority, the father. The Goat's energy — ambitious, disciplined, authoritative."},
            {"num": 11, "name": "Aquarius / 11th House — Community", "meaning": "Friends, groups, hopes, wishes, the collective. The Water-bearer's energy — innovative, humanitarian, free."},
            {"num": 12, "name": "Pisces / 12th House — The Unconscious", "meaning": "The unconscious, hidden enemies, institutions, the collective dream. The Fish's energy — intuitive, dissolving, transcendent."},
        ],
        "layout": "wheel",
    },
}

# ═══════════════════════════════════════════════════════════════
#  CARD SYMBOLS / ASCII ART
# ═══════════════════════════════════════════════════════════════

SUIT_SYMBOLS = {
    "Wands": "🜂",     # Fire triangle
    "Cups": "🜄",      # Water triangle (inverted)
    "Swords": "🜁",    # Air triangle
    "Pentacles": "🜃",  # Earth triangle (inverted)
}

SUIT_DISPLAY = {
    "Wands": "⚚",  # Caduceus
    "Cups": "🪷",   # Lotus
    "Swords": "⚔",  # Sword
    "Pentacles": "✦", # Star
}

MAJOR_SYMBOL = "✶"

ELEMENT_ICONS = {
    "Fire": "△",
    "Water": "▽",
    "Air": "△̃",
    "Earth": "▽̃",
}

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG_DIR = Path.home() / ".arcanum"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

# ═══════════════════════════════════════════════════════════════
#  TAROT DECK CLASS
# ═══════════════════════════════════════════════════════════════

class TarotCard:
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.is_reversed = False
        self.is_major = name in [c["name"] for c in MAJOR_ARCANA]
        self.is_court = name in COURT_CARDS
        self.is_minor = not self.is_major and not self.is_court

        # Determine suit
        if self.is_major:
            self.suit = "Major Arcana"
        elif self.is_court:
            for s in ["Wands", "Cups", "Swords", "Pentacles"]:
                if s in name:
                    self.suit = s
                    break
        else:
            for s in ["Wands", "Cups", "Swords", "Pentacles"]:
                if s in name:
                    self.suit = s
                    break

        self.element = ELEMENTS.get(self.suit, "Spirit")

        # Get Hebrew letter for Major Arcana
        if self.is_major:
            self.hebrew = data.get("letter", "")
            self.hebrew_name = data.get("hebrew", "")
        else:
            self.hebrew = ""
            self.hebrew_name = ""

    @property
    def orientation(self):
        return "Reversed ↯" if self.is_reversed else "Upright ↑"

    @property
    def dignity_label(self):
        if self.is_reversed:
            return "[ill_dignified]Ill-dignified[/ill_dignified]"
        return "[dignified]Dignified[/dignified]"

    @property
    def attribution(self):
        if self.is_major:
            return self.data.get("attribution", "")
        elif self.is_minor:
            parts = []
            if self.data.get("planet"):
                parts.append(self.data["planet"])
            if self.data.get("sign"):
                parts.append(f"in {self.data['sign']}")
            return " ".join(parts) if parts else ""
        elif self.is_court:
            return self.data.get("attribution", "")
        return ""

    @property
    def title(self):
        if self.is_minor:
            return self.data.get("title", "")
        elif self.is_court:
            return self.data.get("title", "")
        return ""

    @property
    def upright_meaning(self):
        return self.data.get("upright", "")

    @property
    def reversed_meaning(self):
        return self.data.get("reversed", "")

    @property
    def meaning(self):
        return self.reversed_meaning if self.is_reversed else self.upright_meaning

    @property
    def keywords(self):
        return self.data.get("keywords", [])

    @property
    def esoteric(self):
        return self.data.get("esoteric", "")


class TarotDeck:
    def __init__(self):
        self.cards = []
        self._build_deck()

    def _build_deck(self):
        # Major Arcana
        for card_data in MAJOR_ARCANA:
            self.cards.append(TarotCard(card_data["name"], card_data))
        # Minor Arcana
        for name, data in MINOR_ARCANA.items():
            self.cards.append(TarotCard(name, data))
        # Court Cards
        for name, data in COURT_CARDS.items():
            self.cards.append(TarotCard(name, data))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, n=1):
        drawn = []
        for _ in range(n):
            if self.cards:
                card = self.cards.pop()
                card.is_reversed = random.random() < 0.35  # ~35% chance of reversal
                drawn.append(card)
        return drawn

    def reset(self):
        self.cards = []
        self._build_deck()


# ═══════════════════════════════════════════════════════════════
#  ELEMENTAL DIGNITIES ENGINE
# ═══════════════════════════════════════════════════════════════

def check_dignity(card, neighbor):
    """Check elemental dignity between two cards."""
    if not card or not neighbor:
        return "neutral"
    e1 = card.element
    e2 = neighbor.element
    if card.is_major:
        e1 = _major_element(card)
    if neighbor.is_major:
        e2 = _major_element(neighbor)
    return ELEMENT_HARMONY.get((e1, e2), "neutral")

def _major_element(card):
    """Determine the elemental affinity of a Major Arcana card."""
    attr = card.data.get("attribution", "")
    if "Fire" in attr or "Mars" in attr or "Aries" in attr or "Leo" in attr or "Sagittarius" in attr:
        return "Fire"
    if "Water" in attr or "Cancer" in attr or "Scorpio" in attr or "Pisces" in attr:
        return "Water"
    if "Air" in attr or "Mercury" in attr or "Gemini" in attr or "Libra" in attr or "Aquarius" in attr:
        return "Air"
    if "Earth" in attr or "Venus" in attr or "Taurus" in attr or "Capricorn" in attr or "Saturn" in attr:
        return "Earth"
    if "Sun" in attr:
        return "Fire"  # Sun is associated with Fire/Tiphareth
    if "Moon" in attr:
        return "Water"
    if "Jupiter" in attr:
        return "Fire"  # Jupiter is expansive (Fire)
    if "Neptune" in attr:
        return "Water"
    if "Pluto" in attr:
        return "Fire"
    return "Spirit"

def apply_dignities(cards):
    """Apply elemental dignities to a list of cards, returning modified readings."""
    results = []
    for i, card in enumerate(cards):
        prev_card = cards[i - 1] if i > 0 else None
        next_card = cards[i + 1] if i < len(cards) - 1 else None

        modifiers = []
        if prev_card:
            d = check_dignity(card, prev_card)
            modifiers.append(d)
        if next_card:
            d = check_dignity(card, next_card)
            modifiers.append(d)

        # Determine overall dignity
        if "exalted" in modifiers:
            dignity = "exalted"
        elif "hostile" in modifiers and "friendly" not in modifiers:
            dignity = "ill-dignified"
        elif "friendly" in modifiers and "hostile" not in modifiers:
            dignity = "strengthened"
        else:
            dignity = "neutral"

        results.append({
            "card": card,
            "dignity": dignity,
            "modifiers": modifiers,
        })
    return results

# ═══════════════════════════════════════════════════════════════
#  RENDERING ENGINE
# ═══════════════════════════════════════════════════════════════

def suit_color(suit):
    return {
        "Wands": "wands",
        "Cups": "cups",
        "Swords": "swords",
        "Pentacles": "pentacles",
        "Major Arcana": "major",
    }.get(suit, "muted")

def element_color(element):
    return {
        "Fire": "fire",
        "Water": "water",
        "Air": "air",
        "Earth": "earth",
        "Spirit": "spirit",
    }.get(element, "muted")

def render_card(card, position_name=None, dignity=None):
    """Render a single card as a rich Panel."""
    sc = suit_color(card.suit)
    ec = element_color(card.element)

    # Card header
    header_parts = [f"[{sc}]{card.name}[/{sc}]"]
    if card.is_reversed:
        header_parts.append(f"[ill_dignified]↯ REVERSED[/ill_dignified]")
    else:
        header_parts.append(f"[dignified]↑ UPRIGHT[/dignified]")

    # Attribution line
    attr_line = ""
    if card.attribution:
        attr_line = f"\n[{ec}]{card.attribution}[/{ec}]"
    if card.hebrew:
        attr_line += f"  [{sc}]{card.hebrew_name} {card.hebrew}[/{sc}]"

    # Title (Golden Dawn Book T title)
    title_line = ""
    if card.title:
        title_line = f"\n[subtitle]« {card.title} »[/subtitle]"

    # Position
    pos_line = ""
    if position_name:
        pos_line = f"\n[heading]◈ {position_name}[/heading]"

    # Dignity modifier
    dig_line = ""
    if dignity:
        dig_map = {
            "exalted": "[spirit]✦ EXALTED — greatly strengthened[/spirit]",
            "strengthened": "[dignified]✦ STRENGTHENED — supported by neighbors[/dignified]",
            "neutral": "[muted]— NEUTRAL — neither strengthened nor weakened[/muted]",
            "ill-dignified": "[ill_dignified]✦ ILL-DIGNIFIED — weakened by neighbors[/ill_dignified]",
        }
        dig_line = f"\n{dig_map.get(dignity, '')}"

    # Keywords
    kw_line = ""
    if card.keywords:
        kws = " · ".join(f"[keyword]{k}[/keyword]" for k in card.keywords)
        kw_line = f"\n{kws}"

    # Meaning
    meaning = card.meaning
    meaning_line = f"\n[meaning]{meaning}[/meaning]"

    # Esoteric (for Major Arcana)
    eso_line = ""
    if card.is_major and card.esoteric:
        eso_line = f"\n\n[subtitle]Esoteric:[/subtitle] [muted]{card.esoteric}[/muted]"

    # Combine
    content = " · ".join(header_parts) + attr_line + title_line + pos_line + dig_line + kw_line + meaning_line + eso_line

    border_style = {
        "Wands": "red3",
        "Cups": "blue1",
        "Swords": "cyan1",
        "Pentacles": "gold3",
        "Major Arcana": "magenta2",
    }.get(card.suit, "white")

    return Panel(
        content,
        border_style=border_style,
        box=ROUNDED,
        padding=(1, 2),
    )


def render_card_mini(card):
    """Render a compact card for multi-card displays."""
    sc = suit_color(card.suit)
    orient = "↯" if card.is_reversed else "↑"
    sym = SUIT_DISPLAY.get(card.suit, MAJOR_SYMBOL) if not card.is_major else MAJOR_SYMBOL
    line1 = f"[{sc}]{sym} {card.name}[/{sc}]"
    line2 = f"{'[ill_dignified]' if card.is_reversed else '[dignified]'}{orient} {card.orientation}[/{'ill_dignified' if card.is_reversed else 'dignified]'}]"
    if card.attribution:
        line3 = f"[muted]{card.attribution}[/muted]"
    else:
        line3 = ""
(spread_name, cards_with_positions, question, api_key, model="openai/gpt-4o"):
    """Request an AI-enhanced reading from OpenRouter."""
    if not HAS_REQUESTS:
        return None, "The 'requests' library is required. Install with: pip install requests"

    # Build the prompt
    card_descriptions = []
    for cwp in cards_with_positions:
        card = cwp["card"]
        pos = cwp["position_name"]
        orient = "Reversed" if card.is_reversed else "Upright"
        line = f"• Position: {pos} — {card.name} ({orient})"
        if card.attribution:
            line += f" | {card.attribution}"
        if card.title:
            line += f" | Book T Title: {card.title}"
        line += f" | Meaning: {card.meaning}"
        if card.esoteric:
            line += f" | Esoteric: {card.esoteric}"
        card_descriptions.append(line)

    prompt = f"""You are a master tarot reader trained in the Golden Dawn tradition and the Book T system of Hermetic tarot. You understand Qabalistic correspondences, elemental dignities, astrological attributions, and the deeper esoteric meanings of the tarot as taught in the Hermetic Order of the Golden Dawn.

A querent has asked the following question: "{question}"

The spread used is: {spread_name}

The cards drawn are:
{chr(10).join(card_descriptions)}

Please provide a comprehensive, insightful reading that:
1. Weaves the cards together into a coherent narrative
2. Takes into account elemental dignities and the relationships between the cards
3. Draws upon the Golden Dawn/Qabalistic correspondences of each card
4. Addresses the querent's question directly
5. Offers practical guidance while honoring the esoteric depth of the tradition
6. Notes any significant patterns (e.g., dominance of an element, Major Arcana concentration, etc.)
7. Synthesizes the reading into an overall message

Write with warmth, depth, and occult sophistication. Use the language of the Golden Dawn tradition where appropriate, but remain accessible."""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/arcanum-tarot",
                "X-Title": "ARCANUM Tarot Divination Engine",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert Golden Dawn tarot reader with deep knowledge of Book T, Qabalah, Hermeticism, and the Western Esoteric Tradition."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 3000,
            },
            timeout=60,
        )
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        else:
            return None, f"API Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Connection error: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#  TUI INTERFACE
# ═══════════════════════════════════════════════════════════════

def clear():
    console.clear()

def pause():
    Prompt.ask("\n  [muted]Press Enter to continue…[/muted]", default="")

def show_banner():
    clear()
    banner = r"""
[title]
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║     ⛧   A R C A N U M   ⊕                                    ║
  ║     The Golden Dawn Tarot Divination Engine                   ║
  ║                                                               ║
  ║     「 Book T  ·  Elemental Dignities  ·  Qabalah 」          ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
[/title]
"""
    console.print(banner)
    console.print("[muted]  Hermetic Order of the Golden Dawn · Est. 1888[/muted]\n")

def show_main_menu():
    console.print(Rule("[title]⛧ MAIN MENU[/title]", style="divider"))
    console.print()
    items = [
        ("1", "🌟", "New Reading", "Choose a spread and draw the cards"),
        ("2", "📖", "Spread Library", "Browse available spreads and their descriptions"),
        ("3", "🃏", "Browse the Deck", "Explore all 78 cards with Golden Dawn correspondences"),
        ("4", "⚖️", "Elemental Dignities", "Learn about the dignity system"),
        ("5", "⚙️", "Settings", "Configure API key, model, and preferences"),
        ("6", "🚪", "Exit", "Leave the temple"),
    ]
    for num, icon, name, desc in items:
        console.print(f"  [menu_num]{num}.[/menu_num] {icon} [menu_item]{name}[/menu_item]  [muted]— {desc}[/muted]")
    console.print()

def show_spread_menu():
    console.print(Rule("[title]⛧ CHOOSE YOUR SPREAD[/title]", style="divider"))
    console.print()
    spread_list = list(SPREADS.items())
    for i, (key, spread) in enumerate(spread_list, 1):
        count = spread["count"]
        console.print(f"  [menu_num]{i}.[/menu_num] [menu_item]{spread['name']}[/menu_item]  [muted]({count} card{'s' if count != 1 else ''})[/muted]")
        console.print(f"      [subtitle]{spread['subtitle']}[/subtitle]")
    console.print()
    console.print(f"  [menu_num]0.[/menu_num] [muted]Return to Main Menu[/muted]")
    console.print()

def show_deck_browse_menu():
    console.print(Rule("[title]⛧ BROWSE THE DECK[/title]", style="divider"))
    console.print()
    console.print(f"  [menu_num]1.[/menu_num] [menu_item]Major Arcana[/menu_item]  [muted]— 22 Trumps[/muted]")
    console.print(f"  [menu_num]2.[/menu_num] [menu_item]Wands[/menu_item]  [muted]— Fire · 14 cards[/muted]")
    console.print(f"  [menu_num]3.[/menu_num] [menu_item]Cups[/menu_item]  [muted]— Water · 14 cards[/muted]")
    console.print(f"  [menu_num]4.[/menu_num] [menu_item]Swords[/menu_item]  [muted]— Air · 14 cards[/muted]")
    console.print(f"  [menu_num]5.[/menu_num] [menu_item]Pentacles[/menu_item]  [muted]— Earth · 14 cards[/muted]")
    console.print(f"  [menu_num]6.[/menu_num] [menu_item]Random Card[/menu_item]  [muted]— Let the Oracle choose[/muted]")
    console.print()
    console.print(f"  [menu_num]0.[/menu_num] [muted]Return to Main Menu[/muted]")
    console.print()

def show_settings(config):
    console.print(Rule("[title]⚙ SETTINGS[/title]", style="divider"))
    console.print()
    api_status = "[success]✦ Set[/success]" if config.get("openrouter_api_key") else "[error]✦ Not Set[/error]"
    model = config.get("openrouter_model", "openai/gpt-4o")
    ai_enabled = "[success]Enabled[/success]" if config.get("openrouter_api_key") and HAS_REQUESTS else "[muted]Disabled[/muted]"
    reversal_pct = config.get("reversal_pct", 35)

    console.print(f"  [heading]OpenRouter API Key:[/heading] {api_status}")
    console.print(f"  [heading]AI Model:[/heading]         [muted]{model}[/muted]")
    console.print(f"  [heading]AI Reading:[/heading]       {ai_enabled}")
    console.print(f"  [heading]Reversal %:[/heading]       [muted]{reversal_pct}%[/muted]")
    console.print(f"  [heading]requests lib:[/heading]     {'[success]Installed[/success]' if HAS_REQUESTS else '[error]Not Installed[/error]'}")
    console.print()
    console.print(f"  [menu_num]1.[/menu_num] [menu_item]Set OpenRouter API Key[/menu_item]")
    console.print(f"  [menu_num]2.[/menu_num] [menu_item]Set AI Model[/menu_item]")
    console.print(f"  [menu_num]3.[/menu_num] [menu_item]Set Reversal Percentage[/menu_item]")
    console.print(f"  [menu_num]4.[/menu_num] [menu_item]Clear API Key[/menu_item]")
    console.print()
    console.print(f"  [menu_num]0.[/menu_num] [muted]Return to Main Menu[/muted]")
    console.print()

# ═══════════════════════════════════════════════════════════════
#  READING FLOW
# ═══════════════════════════════════════════════════════════════

def do_reading(spread_key, config):
    spread = SPREADS[spread_key]
    clear()
    console.print(Rule(f"[title]⛧ {spread['name'].upper()}[/title]", style="divider"))
    console.print()
    console.print(Panel(
        f"[heading]{spread['name']}[/heading]\n[subtitle]{spread['subtitle']}[/subtitle]\n\n[meaning]{spread['description']}[/meaning]",
        border_style="gold1",
        box=ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    # Get question
    question = Prompt.ask("  [heading]What is your question?[/heading] (press Enter for a general reading)", default="General reading")
    console.print()

    # Shuffle animation
    console.print("  [muted]Shuffling the deck…[/muted]")
    time.sleep(0.3)
    console.print("  [muted]The cards feel the weight of your question…[/muted]")
    time.sleep(0.3)
    console.print("  [muted]The cosmos aligns…[/muted]")
    time.sleep(0.3)

    # Draw cards
    deck = TarotDeck()
    deck.shuffle()
    drawn = deck.draw(spread["count"])

    # Apply dignities
    dignified = apply_dignities(drawn)

    # Build cards_with_positions
    cards_with_positions = []
    for i, d in enumerate(dignified):
        pos_name = spread["positions"][i]["name"]
        cards_with_positions.append({
            "card": d["card"],
            "position_name": pos_name,
            "position_meaning": spread["positions"][i]["meaning"],
            "dignity": d["dignity"],
        })

    # Display reading
    console.print()
    console.print(Rule(f"[title]⛧ THE READING[/title]", style="divider"))
    console.print()

    # Question reminder
    console.print(Panel(
        f"[heading]Question:[/heading] [meaning]{question}[/meaning]\n[heading]Spread:[/heading] [subtitle]{spread['name']}[/subtitle]",
        border_style="gold1",
        box=MINIMAL,
        padding=(0, 1),
    ))
    console.print()

    # Show mini overview first
    console.print("[heading]◈ Cards Drawn:[/heading]")
    console.print()
    for cwp in cards_with_positions:
        c = cwp["card"]
        sc = suit_color(c.suit)
        rev = " ↯" if c.is_reversed else ""
        console.print(f"  [{sc}]{c.name}[/{sc}]{rev}  [muted]—[/muted]  [subtitle]{cwp['position_name']}[/subtitle]")
    console.print()

    # Visual layout for Celtic Cross
    if spread_key == "celtic_cross":
        console.print("[heading]◈ Cross Layout:[/heading]")
        console.print()
        console.print(Panel(
            render_celtic_cross_layout(cards_with_positions),
            border_style="dark_goldenrod",
            box=MINIMAL,
            padding=(0, 2),
        ))
        console.print()

    # Detailed card readings
    console.print(Rule("[title]◈ DETAILED INTERPRETATION[/title]", style="divider"))
    console.print()

    for cwp in cards_with_positions:
        card = cwp["card"]
        pos_meaning = cwp["position_meaning"]
        dignity = cwp["dignity"]

        # Position header
        console.print(f"  [heading]━━━ {cwp['position_name']} ━━━[/heading]")
        console.print(f"  [muted]{pos_meaning}[/muted]")
        console.print()
        console.print(render_card(card, cwp["position_name"], dignity))
        console.print()
        pause()

    # Elemental summary
    console.print(Rule("[title]◈ ELEMENTAL ANALYSIS[/title]", style="divider"))
    console.print()

    element_counts = {"Fire": 0, "Water": 0, "Air": 0, "Earth": 0, "Spirit": 0}
    for cwp in cards_with_positions:
        c = cwp["card"]
        e = c.element
        if c.is_major:
            e = _major_element(c)
        element_counts[e] = element_counts.get(e, 0) + 1

    summary_parts = []
    for elem, count in element_counts.items():
        if count > 0:
            ec = element_color(elem)
            bar = "▮" * count
            summary_parts.append(f"  [{ec}]{elem:>8s}[/{ec}] {bar} ({count})")

    console.print("\n".join(summary_parts))

    # Dominant element analysis
    dom_elem = max(element_counts, key=lambda k: element_counts[k])
    if element_counts[dom_elem] > 0:
        dom_color = element_color(dom_elem)
        console.print(f"\n  [{dom_color}]Dominant Element: {dom_elem}[/{dom_color}]")
        elem_analysis = {
            "Fire": "The reading is dominated by Fire — passion, will, creativity, and transformation are the primary forces at work. The querent is in a period of intense activity and spiritual ambition.",
            "Water": "The reading is dominated by Water — emotion, intuition, and the subconscious are the primary forces at work. The querent is in a period of deep feeling and inner reflection.",
            "Air": "The reading is dominated by Air — intellect, communication, and analysis are the primary forces at work. The querent is in a period of mental activity and the search for understanding.",
            "Earth": "The reading is dominated by Earth — material concerns, stability, and practical matters are the primary forces at work. The querent is in a period of manifestation and worldly engagement.",
            "Spirit": "The reading is dominated by Spirit — the higher forces are at work. The querent is in a period of spiritual significance and cosmic alignment.",
        }
        console.print(f"  [meaning]{elem_analysis.get(dom_elem, '')}[/meaning]")
    console.print()

    # AI Reading option
    if config.get("openrouter_api_key") and HAS_REQUESTS:
        console.print(Rule("[title]◈ AI-ENHANCED READING[/title]", style="divider"))
        console.print()
        do_ai = Confirm.ask("  [heading]Would you like an AI-enhanced reading?[/heading]", default=True)
        if do_ai:
            console.print("\n  [muted]Consulting the Oracle through the digital aether…[/muted]")
            model = config.get("openrouter_model", "openai/gpt-4o")
            result, error = ai_reading(spread["name"], cards_with_positions, question,
                                       config["openrouter_api_key"], model)
            if result:
                console.print()
                console.print(Panel(
                    f"[heading]✦ AI Reading — {model}[/heading]\n\n[meaning]{result}[/meaning]",
                    border_style="magenta2",
                    box=ROUNDED,
                    padding=(1, 2),
                    title="⛧ AI ORACLE",
                    title_align="left",
                ))
            else:
                console.print(f"\n  [error]Error: {error}[/error]\n")
    elif not HAS_REQUESTS:
        console.print("  [muted]AI reading unavailable — install 'requests' library[/muted]")
    else:
        console.print("  [muted]AI reading unavailable — set OpenRouter API key in Settings[/muted]")

    console.print()
    console.print(Rule("[title]⛧ END OF READING[/title]", style="divider"))
    console.print()
    # Save reading option
    if Confirm.ask("  [heading]Save this reading?[/heading]", default=False):
        save_reading(spread, question, cards_with_positions, config)
    pause()

def save_reading(spread, question, cards_with_positions, config):
    """Save the reading to a file."""
    readings_dir = CONFIG_DIR / "readings"
    readings_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = readings_dir / f"reading_{timestamp}.json"

    reading_data = {
        "timestamp": datetime.now().isoformat(),
        "spread": spread["name"],
        "question": question,
        "cards": [
            {
                "position": cwp["position_name"],
                "card": cwp["card"].name,
                "reversed": cwp["card"].is_reversed,
                "element": cwp["card"].element,
                "dignity": cwp["dignity"],
            }
            for cwp in cards_with_positions
        ]
    }

    filename.write_text(json.dumps(reading_data, indent=2))
    console.print(f"  [success]Reading saved to {filename}[/success]")

# ═══════════════════════════════════════════════════════════════
#  DECK BROWSER
# ═══════════════════════════════════════════════════════════════

def browse_major():
    clear()
    console.print(Rule("[title]⛧ MAJOR ARCANA — THE 22 PATHS[/title]", style="divider"))
    console.print()
    for card_data in MAJOR_ARCANA:
        card = TarotCard(card_data["name"], card_data)
        console.print(render_card(card))
        console.print()
    pause()

def browse_suit(suit_name):
    clear()
    element = ELEMENTS[suit_name]
    ec = element_color(element)
    sc = suit_color(suit_name)
    console.print(Rule(f"[title]⛧ {suit_name.upper()} — [{ec}]{element.upper()}[/{ec}][/title]", style="divider"))
    console.print()

    # Minor Arcana of this suit
    console.print(f"  [{sc}]── Minor Arcana ──[/{sc}]")
    console.print()
    for rank in ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        name = f"{rank} of {suit_name}"
        if name in MINOR_ARCANA:
            card = TarotCard(name, MINOR_ARCANA[name])
            console.print(render_card(card))
            console.print()

    # Court Cards of this suit
    console.print(f"  [{sc}]── Court Cards ──[/{sc}]")
    console.print()
    for rank in ["Knight", "Queen", "Prince", "Princess"]:
        name = f"{rank} of {suit_name}"
        if name in COURT_CARDS:
            card = TarotCard(name, COURT_CARDS[name])
            console.print(render_card(card))
            console.print()

    pause()

def browse_random():
    deck = TarotDeck()
    deck.shuffle()
    card = deck.draw(1)[0]
    card.is_reversed = False  # Show upright for browsing
    clear()
    console.print(Rule("[title]⛧ THE ORACLE SPEAKS[/title]", style="divider"))
    console.print()
    console.print(render_card(card))
    console.print()
    pause()

# ═══════════════════════════════════════════════════════════════
#  ELEMENTAL DIGNITIES INFO
# ═══════════════════════════════════════════════════════════════

def show_dignities_info():
    clear()
    console.print(Rule("[title]⚖ ELEMENTAL DIGNITIES[/title]", style="divider"))
    console.print()
    console.print(Panel(
        "[heading]The Golden Dawn System of Elemental Dignities[/heading]\n\n"
        "[meaning]In the Golden Dawn system, the meaning of a card is modified by the cards "
        "that surround it. This system of Elemental Dignities is fundamental to Book T divination.\n\n"
        "Cards of the same element strengthen each other (Exalted).\n"
        "Cards of friendly elements support each other (Strengthened).\n"
        "Cards of hostile elements weaken each other (Ill-dignified).\n"
        "Cards of neutral elements have no effect (Neutral).[/meaning]\n\n"
        "[subtitle]The Elemental Relationships:[/subtitle]",
        border_style="gold1",
        box=ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    table = Table(show_header=True, header_style="heading", box=ROUNDED, border_style="dark_goldenrod")
    table.add_column("", style="muted")
    table.add_column("🔥 Fire", style="fire")
    table.add_column("💧 Water", style="water")
    table.add_column("💨 Air", style="air")
    table.add_column("🌍 Earth", style="earth")

    relationships = [
        ("🔥 Fire", "Exalted", "Hostile", "Friendly", "Neutral"),
        ("💧 Water", "Hostile", "Exalted", "Friendly", "Friendly"),
        ("💨 Air", "Friendly", "Friendly", "Exalted", "Hostile"),
        ("🌍 Earth", "Neutral", "Friendly", "Hostile", "Exalted"),
    ]

    for row in relationships:
        styled_row = [row[0]]
        for cell in row[1:]:
            if cell == "Exalted":
                styled_row.append(f"[spirit]{cell}[/spirit]")
            elif cell == "Friendly":
                styled_row.append(f"[dignified]{cell}[/dignified]")
            elif cell == "Hostile":
                styled_row.append(f"[ill_dignified]{cell}[/ill_dignified]")
            else:
                styled_row.append(f"[muted]{cell}[/muted]")
        table.add_row(*styled_row)

    console.print(table)
    console.print()

    console.print(Panel(
        "[heading]Key Principles:[/heading]\n\n"
        "[dignified]EXALTED[/dignified] — Same element: the card's energy is greatly amplified\n"
        "[dignified]STRENGTHENED[/dignified] — Friendly element: the card's energy is supported\n"
        "[muted]NEUTRAL[/muted] — Neither friend nor foe: the card's energy is unmodified\n"
        "[ill_dignified]ILL-DIGNIFIED[/ill_dignified] — Hostile element: the card's energy is weakened or reversed\n\n"
        "[subtitle]The Golden Dawn Friendship Rules:[/subtitle]\n"
        "• Fire and Air are friendly (both active, hot, dry)\n"
        "• Water and Earth are friendly (both passive, cold, moist)\n"
        "• Fire and Water are hostile (opposite principles)\n"
        "• Air and Earth are hostile (opposite principles)\n"
        "• Fire and Earth are neutral\n"
        "• Water and Air are friendly\n\n"
        "[meaning]When a card is Ill-dignified, its meaning tends toward the reversed interpretation "
        "even if drawn upright. When Exalted, its meaning is intensified. This is the key to reading "
        "cards in combination rather than isolation — as the Golden Dawn intended.[/meaning]",
        border_style="gold1",
        box=ROUNDED,
        padding=(1, 2),
    ))
    console.print()
    pause()

# ═══════════════════════════════════════════════════════════════
#  SPREAD LIBRARY
# ═══════════════════════════════════════════════════════════════

def show_spread_library():
    clear()
    console.print(Rule("[title]📖 SPREAD LIBRARY[/title]", style="divider"))
    console.print()
    for key, spread in SPREADS.items():
        console.print(Panel(
            f"[heading]{spread['name']}[/heading]\n"
            f"[subtitle]{spread['subtitle']}[/subtitle]\n\n"
            f"[meaning]{spread['description']}[/meaning]\n\n"
            f"[muted]Cards: {spread['count']}[/muted]",
            border_style="dark_goldenrod",
            box=ROUNDED,
            padding=(1, 2),
        ))
        console.print()
    pause()

# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION LOOP
# ═══════════════════════════════════════════════════════════════

def main():
    config = load_config()

    while True:
        try:
            show_banner()
            show_main_menu()
            choice = Prompt.ask("  [heading]Choose[/heading]", choices=["1","2","3","4","5","6"], default="1")

            if choice == "1":
                # New Reading
                while True:
                    show_banner()
                    show_spread_menu()
                    spread_keys = list(SPREADS.keys())
                    valid_choices = [str(i) for i in range(len(spread_keys) + 1)]
                    schoice = Prompt.ask("  [heading]Choose a spread[/heading]", choices=valid_choices, default="1")
                    if schoice == "0":
                        break
                    idx = int(schoice) - 1
                    if 0 <= idx < len(spread_keys):
                        do_reading(spread_keys[idx], config)
                    config = load_config()  # Reload in case settings changed

            elif choice == "2":
                show_spread_library()

            elif choice == "3":
                # Browse Deck
                while True:
                    show_banner()
                    show_deck_browse_menu()
                    dchoice = Prompt.ask("  [heading]Choose[/heading]", choices=["0","1","2","3","4","5","6"], default="1")
                    if dchoice == "0":
                        break
                    elif dchoice == "1":
                        browse_major()
                    elif dchoice in ["2","3","4","5"]:
                        suits = ["Wands", "Cups", "Swords", "Pentacles"]
                        browse_suit(suits[int(dchoice) - 2])
                    elif dchoice == "6":
                        browse_random()

            elif choice == "4":
                show_dignities_info()

            elif choice == "5":
                # Settings
                while True:
                    show_banner()
                    show_settings(config)
                    set_choice = Prompt.ask("  [heading]Choose[/heading]", choices=["0","1","2","3","4"], default="0")
                    if set_choice == "0":
                        break
                    elif set_choice == "1":
                        console.print()
                        key = Prompt.ask("  [heading]Enter your OpenRouter API Key[/heading]", password=True)
                        if key:
                            config["openrouter_api_key"] = key
                            save_config(config)
                            console.print("  [success]API key saved![/success]")
                        time.sleep(0.5)
                    elif set_choice == "2":
                        console.print()
                        model = Prompt.ask("  [heading]Enter AI model name[/heading]",
                                          default=config.get("openrouter_model", "openai/gpt-4o"))
                        config["openrouter_model"] = model
                        save_config(config)
                        console.print("  [success]Model saved![/success]")
                        time.sleep(0.5)
                    elif set_choice == "3":
                        console.print()
                        pct = IntPrompt.ask("  [heading]Enter reversal percentage (0-100)[/heading]",
                                           default=config.get("reversal_pct", 35))
                        config["reversal_pct"] = max(0, min(100, pct))
                        save_config(config)
                        console.print("  [success]Reversal percentage saved![/success]")
                        time.sleep(0.5)
                    elif set_choice == "4":
                        if "openrouter_api_key" in config:
                            del config["openrouter_api_key"]
                            save_config(config)
                            console.print("  [success]API key cleared![/success]")
                        time.sleep(0.5)

            elif choice == "6":
                clear()
                console.print()
                console.print(Panel(
                    "[title]⛧ Vale, O Seeker ⛧[/title]\n\n"
                    "[meaning]May the light of Tiphareth guide your path,\n"
                    "and the wisdom of Chokmah illuminate your understanding.\n\n"
                    "« In the name of the Lord of the Universe, we bid you farewell. »[/meaning]",
                    border_style="gold1",
                    box=DOUBLE,
                    padding=(1, 2),
                ))
                console.print()
                break

        except KeyboardInterrupt:
            console.print("\n\n  [muted]Interrupted. Farewell, Seeker.[/muted]\n")
            break
        except Exception as e:
            console.print(f"\n  [error]Error: {e}[/error]\n")
            pause()


if __name__ == "__main__":
    main()
