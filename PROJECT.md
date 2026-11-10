# ADAFNIA / الدافنية

## Visual revision v2

The owner rejected the first visual direction as too simplified. The original application was run locally and inspected on desktop/mobile; v2 restores its industrial photographic scale, Cairo typography and navy/cyan identity while retaining the new content system. Added photographic product cards, manufacturing tabs, a geographic project map and more substantial inner-page styling. See reviews/visual-comparison-v2.md. Prior public templates/CSS remain in reviews/v1-snapshot/.

Owner decisions, 15 October 2026:

- Complete rebuild approved. Codex implements directly.
- Hosting ready; publish after actual hosting access is configured.
- Arabic and English public site; Arabic content dashboard.
- Existing reference assets are the visual and factual source. Original files preserved at reference/.
- Products must remain extensible: categories, products and independently approved dimensions.
- News supports drafts, publication and scheduling.
- Certificates can be replaced from dashboard, with expiry dates and archival presentation.
- Projects may be shown publicly. Do not invent quantities, dates or images.
- Paid project with immediate delivery priority.

Local preview: http://127.0.0.1:8766/ar/
Dashboard: http://127.0.0.1:8766/dashboard/
Local credentials: LOCAL_ACCESS.md (ignored by Git; do not deploy).
Start after closing the preview: ./start.sh

## Content awaiting factory approval

Engineering variant rows are deliberately not inferred from the low-resolution tables. The original PDF is available in the technical library. Staff can enter and approve dimensions in the dashboard; the specification selector activates as approved rows are published.

No real news was supplied. The newsroom is functional and has a deliberate empty state until staff publishes an article.

Existing ISO PDFs expired on 10 May 2026. They are explicitly archival; upload renewed copies and actual dates through Certificates.

## Delivery scope

Includes homepage and animated introduction, story, catalogue and filtering, product specifications/print-to-PDF, projects, news, certificate archive/current documents, technical library, enquiry/quote capture, staff CRUD, image optimization, bilingual content and publication privacy, sitemap/robots, Passenger configuration, and local verification.

The website is running locally. It is not deployed to the customer's domain; no hosting credentials or domain were provided in this conversation.

## Claude redesign (approved direction v2), 15 October 2026

The owner rejected GPT's visual layer and approved homepage mockup v2 (`mockups/home-v2/`, a Rivulis + Wavin mix: warm, photo-led, one brand blue). All public templates were rebuilt on that system. The backend, dashboard and tests were kept.

- Public templates: `templates/site/` + `templates/site/parts/`. Styles: `static/css/site.css` (tokens at the top, formatted). Behaviour: `static/js/site.js`.
- Interface copy (AR/EN): `factory/strings.py`, available as `{{ t.key }}`. Company content stays in the DB.
- Wording rule (owner, 10 Nov 2026): say «مواصفات عالمية» / "international standards", never «مواصفات ألمانية» / German standards. A test guards the interface copy.
- Product page: size picker plus full table from approved `ProductVariant` rows. WhatsApp and the contact form get the exact size.
- Catalogue sizes (PE100, 20–225 mm × PN 4–25) are in `factory/catalogue.py`, transcribed from profile pages 7 and 10. `seed_content` adds them **unapproved**. **The local DB has them approved for the preview only. Production must be approved by the factory engineer.**
- Data fixes: Ouagadougou hall moved to Sirte (was Tripoli). Hero tagline set to the approved headline.
- Removed: AI-generated hero image, GPT public CSS/JS, Phosphor icon font.

### Dashboard redesign and self-hosting (15 October 2026)

- Dashboard rebuilt in the same family: `templates/dashboard/*`, `static/css/dashboard.css`, inline SVG icons in `templates/dashboard/icon.html`. Home shows alerts (no valid certificate, expiring certificates, pending sizes, draft products), recent enquiries and content counts. Lists have thumbnails and status pills. Forms are two-column with Arabic/English pairs, switches and an Arabic file picker. Mobile uses a drawer.
- Sizes: pending/approved filter, search by product name or diameter, bulk approval by id. Engineer sign-off is a single screen: Sizes → Pending → select all → Approve.
- Almarai (OFL) and GSAP 3.13 are self-hosted (`static/fonts/almarai/`, `static/vendor/gsap/`). There are no third-party requests. Old Cairo/IBM Plex fonts and GPT dashboard CSS were removed.
- `check --deploy` passes with production env vars. Deploy steps: README → Production / Passenger.

### Before launch

1. Factory: renewed ISO certificates; confirm the Ouagadougou hall is in Sirte; photo shoot; engineer approves the 81 sizes.
2. Hosting: cPanel/hosting access and the domain. Then set env vars, migrate, `seed_content`, create the owner account, `collectstatic`, and configure media serving (README).

