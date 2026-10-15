# Claude evaluation of the GPT/Codex build (2026-10-15)

Scope: code read, 28/28 tests run (pass), `manage.py check` clean, site captured at 1440×900 and 390×844 (Arabic: home, products, quality, contact, projects, about).

## Verdict
Keep it. Strong backend and honest content handling; weak on visual identity, copy, maintainability, and the one feature that matters most (the spec selector) is empty.

| Area | Score | Note |
|---|---|---|
| Backend / data model | 8/10 | Variants, drafts/scheduling, certificate expiry, upload validation, throttling, id-based dashboard |
| Content honesty | 7/10 | No invented specs/news, expired ISO shown as archive. But: invented project city + AI hero image |
| Visual design | 6/10 | Clean, competent, responsive. Reads as a generic corporate template: rounded cards, ↗ on everything |
| Copy | 4/10 | Every section uses the same two-line AI slogan formula |
| Maintainability | 4/10 | Templates/CSS/views written as single very long lines; bilingual text via inline `{% if is_ar %}` |
| Launch completeness | 5/10 | 0 variant rows, 0 news, 2 products, not under git, hosting unverified |

## Must fix (P0/P1)
1. **Hero image is AI-generated.** `static/img/industry-hero.png` is byte-identical to the old site's `static/images/hero.png` (1024×1024, Gemini-style). It is not the Adafnia factory. A factory's first screen must show the real factory. Use `factory.webp`/`production.webp` until a photo shoot happens.
2. **Invented, wrong location.** Seed puts «قاعة مؤتمرات واغادوغو» in Tripoli (also drawn on the map). The Ouagadougou Conference Centre is in **Sirte**. The profile gives no city; don't assign one without the factory's confirmation.
3. **Spec selector is empty (0 `ProductVariant` rows).** GPT called the tables "low-resolution", but the PDF embeds them at **2001×1644 px** (pages 7 and 10) and they are legible. Transcribe them into **unapproved draft rows** so the engineer only has to check and approve, instead of typing ~190 rows × 3 values from scratch.
4. **Code formatting.** `templates/site/*.html`, `static/site.css` (24 KB on 6 lines), `static/presentation.css`, `factory/views.py` are written as one-line blobs. Run a formatter (djlint for templates, prettier for CSS/JS, ruff/black for Python) before anyone else touches it.
5. **No git repository.** Run `git init` and make the first commit before more changes. Add `.venv`, `db.sqlite3`, `media/`, `staticfiles/` and `LOCAL_ACCESS.md` to `.gitignore`.

## Should fix (P2)
- **Copy formula:** «قوة تُصنع بدقة. وثقة تمتد.» / «مصنع ينمو. وثقة تتراكم.» / «الدقة تبدأ من المادة. وترافق كل متر.» / «نترك أثراً. من مشروع إلى آخر.» / «معاً، نصل إلى ما هو أبعد.». Same rhythm in every section. Rewrite with concrete facts (2006, 6–25 bar, 20–1600 mm, ISO, Misrata), written in Arabic first.
- **i18n:** inline `{% if is_ar %}…{% else %}…{% endif %}` for every string. It's acceptable for 2 languages, but move static copy to one dictionary or the Django i18n catalogue, so wording changes happen in one place.
- **News section:** the homepage news block shows a factory photo plus "explore the profile" when there is no news. Fine for now, but the client needs 2–3 real posts at launch.
- **Stray staging dir:** `~/projects/Claude/talks./adafnia-build` (8.2 MB) plus the odd `talks.` folder. Delete once confirmed unused. `README.md` still references it.
- **Hosting:** Passenger config exists, but nothing was verified on the real host (Python availability, media alias, HTTPS).

## Good, keep
- Dashboard routes are `<int:pk>` (complies with the id-not-slug rule). Public detail links use pk.
- Variant approval flag, so nothing technical is published without sign-off.
- Expired ISO certificates are presented as an archive with dates, never as current.
- Contact: phone required, email optional, honeypot, rate limit. WhatsApp/quote prefill from a variant.
- Intro follows the water-drop/ripple/logo concept, is skippable, and respects reduced motion.
- Responsive at 390 px with no overflow. Sitemap/robots in place. 28 integration tests.

---

# UI/UX visual review (owner: "bad to the eye, not pleasant")

## Root cause: there is no design system
Measured across `site.css` + `presentation.css` + `details.css`:
- **60 distinct font sizes** (8px … 112px). 77 declarations are ≤12px. Labels and captions at 10–13px are unreadable in Arabic.
- **155 distinct hex colours.**
- **≥12 different corner radii** (3, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16 px, plus 50%).
- **Negative letter-spacing on Arabic headings** (`h1 -2px`, `h2 -1px`, hero `-1.6px`, footer `-5px`). Arabic is a connected script, so tracking squeezes the joins and makes headings look cramped and heavy.
- **v2 is a CSS layer stacked on v1.** `h1`/`h2`/`.hero h1` are each redefined 2–3 times with different values. The look is the result of overrides, not of a design.
- **Two fonts competing.** Cairo (headings, heavy/rounded) with IBM Plex Sans Arabic (body). Different construction and different x-heights, so headings and body never feel like one family.

## What the eye sees
1. **↗ arrow on everything (43 instances).** On buttons, cards, text links, footer, the contact CTA. It's the 2021 "agency template" tic. It adds noise and carries no meaning (none of these links open a new site).
2. **Same template on every page.** Every inner page = the same darkened AI factory image + small eyebrow + two-line heading with the second line in cyan + one grey sentence. Home, products, quality, contact, projects, about all look identical, and nothing tells you which page you are on.
3. **Same slogan rhythm everywhere.** «X. / Y.» with the second line coloured. Combined with point 2, the site feels auto-generated.
4. **Hero.** A dark, low-contrast AI image under a 60% navy overlay. Heavy Cairo headline. Cyan button + ghost button, both with ↗. Generic "industrial template".
5. **Header.** The logo PNG already contains «مصنع الدافنية» in tiny unreadable text. Next to it the site types «الدافنية» again in bold plus a 10px subtitle, so the name appears twice and the mark itself is illegible. The «تواصل معنا» CTA switches from a ghost to a solid blue box when scrolling.
6. **Cards.** Rounded white cards with a 1px border, an image on top, a small blue «PE100» eyebrow, a heavy title, grey text and ↗. Only 2 products, so the catalogue looks empty rather than curated.
7. **Banners.** «المواصفات بين يديك» and «وثائق الجودة بشفافية» are thin full-width strips with an icon box and ↗. They read as filler, not content.
8. **Colour.** Navy, electric blue, cyan and a grey-blue tint all compete. No neutral rest, and cyan text on navy vibrates.
9. **Rhythm.** Light → dark → light → dark → light → dark sections with the same vertical padding. No hierarchy between chapters, so the page feels long and monotonous (7,300px at 1440).
10. **Contact.** The same phone number is printed twice per branch (in the description and again as a link). Phone numbers are left-aligned at the far edge of an RTL column.
11. **Icons.** Phosphor line icons in tinted rounded squares (applications, projects, banners). That's the stock SaaS "feature grid" look.
12. **Mobile.** Works without overflow, but it repeats the desktop problems: 4 metrics in a 2×2 boxed grid, tiny captions, and the heavy headline wraps awkwardly.

## Verdict
The visual layer is not fixable by tweaks, because the problems are systemic (no scale, no tokens, layered overrides, template patterns). **Keep the Django backend, models, dashboard logic and tests. Redo the public templates and CSS from a new, small design system**, approved first as a static mockup of the homepage (the same process as Remal).

## Minimum design system for the redo
- **One Arabic family** with Latin companion, used everywhere. No tracking on Arabic.
- **Type scale of ~7 sizes.** Body ≥17px Arabic, captions ≥14px.
- **One radius** (or none), **one border colour**, **≤8 colour tokens**: ink, paper, one brand blue, one water accent, 2 greys, success, warning.
- **Spacing scale** of 8 steps.
- **No decorative arrows.** Links are underlined text or plain buttons. A directional chevron only where something actually moves forward (pagination, carousel). In RTL it points left.
- **Each page gets its own structure.** Products = table/selector first. Quality = documents and lab. Contact = map + branches. No universal dark banner.
- **Real photography only**, no AI hero.
