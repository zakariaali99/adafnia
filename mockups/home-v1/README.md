# Adafnia: homepage mockup v1 (2026-10-15)

Static HTML mockup of the new homepage. It goes to the owner for approval before any template work in the Django app.

- Open: `python3 -m http.server 8790` in this folder, then http://127.0.0.1:8790/
- `?intro=1` replays the intro. `?nointro` skips it. Otherwise it plays once per browser session and is skipped with reduced motion.
- Arabic only for now (the EN link is inert).

## Design system (all in `:root`)
- 9 colour tokens. Blue `#2860B0` and water `#20B8E8` are sampled from the logo.
- One family: IBM Plex Sans Arabic, plus IBM Plex Mono for numbers and specs. No letter-spacing on Arabic.
- 7 type sizes (14 → 56px). Arabic body text is 17px.
- 8 spacing steps, and one radius (2px).
- No decorative arrows. Links are underlined text.

## Content provenance
- Photos and logo: extracted from the factory's own profile PDF and LOGO.pdf. No AI imagery.
- Spec values (20–225 mm, PN 4–25): transcribed from catalogue pages 7 and 10. **Pending engineer sign-off.**
- News cards are labelled "نموذج للتصميم" (design sample); there is no real news yet.
- ISO certificates are shown as "awaiting renewed copy", because the current ones expired on 2026-05-10.
- «قاعة واغادوغو» is placed in Sirte. **Confirm with the factory.**
