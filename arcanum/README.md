# ⛧ ARCANUM ⊕ The Golden Dawn Tarot Divination Engine

A menu-driven TUI (Text User Interface) tarot divination application based on **Book T** and the **Hermetic Order of the Golden Dawn**'s esoteric tarot system.

## Features

### 🃏 Full 78-Card Deck with Golden Dawn Correspondences
- **22 Major Arcana** — Hebrew letter, astrological attribution, Qabalistic path, esoteric meaning
- **40 Minor Arcana** — Book T titles, decan/planet/sign attributions, upright & reversed meanings
- **16 Court Cards** — Knight/Queen/Prince/Princess system, element-of-element attributions, zodiac ranges

### 📖 Multiple Occult-Based Spreads
- **Celtic Cross** (10 cards) — The classic Golden Dawn divination method with visual cross layout
- **Three Card** (3 cards) — Past/Present/Future mapped to the Three Pillars
- **Tree of Life** (10 cards) — Qabalistic divination on the ten Sephiroth
- **Planetary** (7 cards) — Seven classical planets in Chaldean order
- **Opening of the Key** (4 cards) — The *authentic* Golden Dawn method (Tetragrammaton)
- **Single Card** (1 card) — The Oracle's direct answer
- **Relationship** (7 cards) — Alchemical relationship analysis
- **Year Ahead** (12 cards) — Twelve signs/houses of the zodiac

### ⚖️ Elemental Dignities System
- Automatic dignity calculation between neighboring cards
- Friendly/hostile/neutral/exalted relationships per Golden Dawn rules
- Cards modified by their neighbors — readings in *combination*, not isolation

### 🔮 AI-Enhanced Readings (Optional)
- Integrates with **OpenRouter API** for AI-powered interpretive readings
- Sends full Golden Dawn correspondences, Book T titles, esoteric meanings to the AI
- AI reads with occult sophistication using Golden Dawn framework
- Works with any OpenRouter model (GPT-4o, Claude, Llama, etc.)
- Fully optional — works perfectly without an API key

### 📊 Elemental Analysis
- Automatic count of elements in each reading
- Dominant element identification and interpretation
- Visual element bar chart

### 💾 Reading Persistence
- Save readings as JSON to `~/.arcanum/readings/`
- Full metadata including positions, orientations, and dignities

## Installation

```bash
pip install rich requests
```

(`requests` is only needed for AI-enhanced readings — the app works without it)

## Usage

```bash
python arcanum.py
```

## Configuration

Settings are stored in `~/.arcanum/config.json`:

| Setting | Description | Default |
|---------|-------------|---------|
| `openrouter_api_key` | Your OpenRouter API key | Not set |
| `openrouter_model` | AI model to use | `openai/gpt-4o` |
| `reversal_pct` | Probability of card reversal | `35` |

### Setting API Key

Either through the Settings menu in the app, or directly:

```bash
# Edit ~/.arcanum/config.json
{
  "openrouter_api_key": "sk-or-...",
  "openrouter_model": "openai/gpt-4o"
}
```

Get an API key at [openrouter.ai](https://openrouter.ai)

## Golden Dawn Concepts Used

This app implements the following from the Golden Dawn / Book T tradition:

- **Book T card titles** for all Minor Arcana (e.g., "Dominion", "Strife", "Virtue")
- **Decan attributions** — each Minor Arcana 2-10 has a specific zodiacal decan and planetary ruler
- **Court card attributions** — Knight/Queen/Prince/Princess with element-of-element system
- **Hebrew letter correspondences** for the 22 Major Arcana paths
- **Astrological attributions** — zodiac signs, planets, elements
- **Qabalistic Tree of Life** — Sephiroth and paths
- **Elemental Dignities** — the Golden Dawn's system for reading cards in combination
- **Opening of the Key** — the actual Golden Dawn divination method (YHVH)

## License

Open source — use as you will.

⛧ « In the name of the Lord of the Universe, we work. » ⛧