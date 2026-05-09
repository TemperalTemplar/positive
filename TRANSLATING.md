# Adding a New Language to POSITIVE

Anyone can contribute a translation. Here's how:

## Step 1 — Copy an existing translation file

```bash
mkdir -p locale/YOUR_LANG_CODE/LC_MESSAGES
cp locale/es/LC_MESSAGES/django.po locale/YOUR_LANG_CODE/LC_MESSAGES/django.po
```

Common language codes: `it` (Italian), `nl` (Dutch), `pl` (Polish), `hi` (Hindi), `tr` (Turkish), `vi` (Vietnamese), `id` (Indonesian), `sw` (Swahili)

## Step 2 — Edit the .po file

Open the file and translate each `msgstr` line. Leave `msgid` lines untouched.

```
msgid "Begin Session"
msgstr "Your translation here"
```

## Step 3 — Add your language to settings.py

In `positive_project/settings.py`, add your language to the `LANGUAGES` list:

```python
LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('it', _('Italian')),   # add your language here
]
```

## Step 4 — Submit a Pull Request

Push your `.po` file and updated `settings.py` as a pull request. Translations compile automatically when Docker starts.

## RTL Languages (Arabic, Hebrew, Urdu, etc.)

The layout automatically flips right-to-left for RTL languages — no extra work needed.

## Current Translations

| Language | Code | Status |
|----------|------|--------|
| English | en | ✅ Complete |
| Spanish | es | ✅ Complete |
| French | fr | ✅ Complete |
| German | de | ✅ Complete |
| Portuguese | pt | ✅ Complete |
| Arabic | ar | ✅ Complete (RTL) |
| Chinese (Simplified) | zh-hans | ✅ Complete |
| Japanese | ja | ✅ Complete |
| Korean | ko | ✅ Complete |
| Russian | ru | ✅ Complete |
| Italian | it | 🔲 Wanted |
| Dutch | nl | 🔲 Wanted |
| Polish | pl | 🔲 Wanted |
| Hindi | hi | 🔲 Wanted |
| Turkish | tr | ✅ Complete |
| Hebrew | he | 🔲 Wanted (RTL) |
| Swahili | sw | 🔲 Wanted |
