# 🗺️ pubquiz-kart

Generer pubquiz-kart over norske byer fra enkle YAML-konfig-filer.
Kartet skrives ut på A4 liggende og viser markører deltakerne skal identifisere.

## Prosjektstruktur

```
pubquiz-kart/
├── pubquiz_kart.py        # Hovedscript
├── quizzes/               # En YAML-fil per quiz
│   └── peppes_oslo.yaml
├── svgs/                  # SVG-illustrasjoner for landemerker
│   ├── slottet.svg
│   ├── oslo_s.svg
│   ├── operaen.svg
│   ├── stortinget.svg
│   └── radhuset.svg
└── output/                # Genererte HTML-filer (git-ignorert)
```

## Kom i gang

```bash
# Installer avhengighet
pip install pyyaml

# Generer quizkart
python pubquiz_kart.py quizzes/peppes_oslo.yaml

# Generer fasit
python pubquiz_kart.py quizzes/peppes_oslo.yaml --fasit

# Generer begge på én gang
python pubquiz_kart.py quizzes/peppes_oslo.yaml --begge
```

Åpne den genererte HTML-filen i en nettleser og bruk **Ctrl+P** for å skrive ut (A4 liggende).

## Lag en ny quiz

1. Kopier en eksisterende konfig:
   ```bash
   cp quizzes/peppes_oslo.yaml quizzes/min_nye_quiz.yaml
   ```

2. Rediger YAML-filen:
   - `markers` – koordinater til stedene deltakerne skal gjette (+ `answer` for fasit)
   - `landmarks` – orienteringspunkter med valgfri SVG, emoji eller prikk
   - `title`, `question` – tekst på kartet
   - `tile_style` – `light_all` | `dark_all` | `voyager` | `light_nolabels`

3. Kjør scriptet:
   ```bash
   python pubquiz_kart.py quizzes/min_nye_quiz.yaml --begge
   ```

## Legg til SVG-landemerker

Plasser en `.svg`-fil i `svgs/`-mappen og referér til den i YAML:

```yaml
landmarks:
  - lat: 59.9170
    lng: 10.7275
    svg: slottet.svg
    label: "Slottet"
```

SVG-filer bør ha `viewBox="0 0 40 40"` og bruke nøytrale farger.
Faller tilbake på emoji (`icon`) eller prikk hvis SVG ikke finnes.

## Tips til koordinater

Bruk [Google Maps](https://maps.google.com) – høyreklikk på et sted → kopier koordinater.
Format: `lat: 59.9170` / `lng: 10.7275`
