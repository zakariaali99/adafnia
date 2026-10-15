# Final integration, security and code review

Reviewed 2026-10-15 against `plans/build.md` and `reviews/frontend.md`, using the latest available Python, public/dashboard templates, CSS/JS, seed, SEO and deployment documentation. Source inspection only: no tests rerun, no subagents, no application/database changes. This report is the only requested write. Findings describe code paths, not newly executed reproductions.

## Verdict

Spec compliance: **partial; fix the five issues below before final acceptance**. Bilingual routes, primary-key detail links, staff CRUD, publishing/scheduling, upload checks, expiry archives, and contact/quote wiring are present. The editable-content and no-invented-content requirements have concrete gaps.

Quality: **needs targeted corrections, not a rewrite**. No authentication bypass or public draft/article-body disclosure was found in the inspected routes. Production cPanel readiness remains conditional on real hosting configuration and the main agent's verification; this source review does not certify a live deployment or responsive browser behavior.

Counts: five P2 correctness/accessibility findings; zero P0/P1 findings. No stylistic mandates.

## Must-fix findings

### 1. [P2] Numeric query parsing can raise uncaught exceptions

Locations: `factory/views.py:49-55`, `factory/views.py:82`, `factory/views.py:113`.

`isdigit()` accepts characters that `int()` does not, such as superscript two. Consequently `/en/products/?category=%C2%B2`, `/en/contact/?product=%C2%B2`, and `/en/api/variants/?product=%C2%B2` reach integer conversion directly or through a model integer field and raise `ValueError` instead of returning a controlled response. The API also converts arbitrarily long digit strings without a length bound; sufficiently long values exceed Python's integer-conversion limit.

Fix: parse IDs through a shared bounded integer validator, catch conversion failures, and return 400 or an explicitly defined empty selection. Apply it to product, variant and category query parameters. Keep slug support separate from malformed numeric inputs.

### 2. [P2] Dashboard settings save successfully but do not update public content

Locations: `factory/models.py:87-98`, `factory/dashboard.py:114-120`, `templates/site/base.html:6`, `templates/site/about.html:1`, `templates/site/resources.html:1`.

The settings form exposes bilingual titles, taglines, about text, addresses and a profile upload. Public templates consume only phone/email/WhatsApp from settings: branding/about copy is hardcoded, and the downloads page reads only Resource records. Editing the company description or uploading a replacement profile through Settings therefore reports success without changing its public presentation. This contradicts the plan's “All material editable” requirement and makes profile replacement misleading.

Fix: render the relevant bilingual settings in public pages and expose the settings profile download, or consolidate profile editing into one working Resource workflow and remove the disconnected settings field. Make the remaining required editorial sections editable rather than leaving staff-facing controls disconnected.

### 3. [P2] Blank material becomes an invented PE100 specification

Location: `templates/site/home.html:8`, expression `product.material|default:'PE100'`.

Staff can publish arbitrary product families and leave the optional material field blank. Any such product appearing among the first three homepage products is labelled PE100 even though that value was never entered or approved. This is a concrete violation of the no-invented-content requirement; the catalogue/detail templates correctly avoid this fallback.

Fix: show material only when populated, or use a neutral nontechnical label. Never infer a material grade from a missing value.

### 4. [P2] Contact page omits the supplied secondary sales numbers

Locations: `factory/management/commands/seed_content.py:32-38`, `templates/site/contact.html:1`.

The seed preserves all supplied sales numbers in bilingual branch descriptions but assigns only the first number to `branch.phone`. Contact renders address and `branch.phone` only; branch descriptions are not displayed anywhere publicly. For example, Tripoli sales centre 2 exposes 092-6160178 while hiding 091-8070400 and 091-6602222. Staff edits to those preserved descriptions likewise have no visible effect.

Fix: display the translated branch description on Contact, or model/render multiple phone entries with separate telephone links, preserving every supplied number.

### 5. [P2] Escape closes mobile navigation without restoring keyboard focus

Locations: `static/site.js:5-12`; `static/site.css:4` (the `max-width:1023px` navigation rules).

Opening the mobile menu explicitly focuses its first link. Pressing Escape invokes `closeMenu()`, which hides the navigation with visibility/opacity rules but leaves focus on that now-hidden link. Keyboard users lose their visible focus position and a predictable return to the menu control.

Fix: when closing an open menu with focus inside navigation, restore focus to the menu toggle; do this for Escape and relevant close actions. Also give the intro equivalent focus management: `playIntro()` makes header/main inert without focusing Skip, and footer controls remain active behind its overlay (`static/site.js:19-35`). Focus Skip on entry, contain background interaction, and restore the initiating focus when leaving.

## Inspected requirement coverage and limits

- Public routes/links: Arabic/English route context and locale switching preserve detail paths; templates use primary-key product/news/project links and views accept those keys. Public list pagination and product family/search filters are wired.
- Staff dashboard: active staff checks protect list/create/edit/delete; login rejects nonstaff; POST forms contain CSRF tokens; deletion handles protected categories. Dynamic forms expose publication, scheduling, variant approval, certificate dates and uploads. All staff are intentionally trusted editors, as documented.
- Drafts/scheduling: public list/detail queries, variant API and sitemap filter unpublished products/projects, draft/future news and unapproved variants. No article-body bypass found. Uploaded files themselves use ordinary public media URLs, explicitly documented as nonconfidential; draft route privacy is not a claim of authenticated media storage.
- Certificates: expiry is checked against the current local date; expired/inactive records enter the archive with an explicit historical disclaimer. Existing expired seed certificates are not represented as current. Null expiry is accepted as an editorial assumption; independent validity is not verified by the application.
- Contact/quote: required fields, email validation, phone digit minimum, published-only product choices, approved/matching quote variant selection, honeypot, CSRF and database throttles are present. Finding 1 covers the malformed GET boundary. No tests were executed during this review.
- Uploads: staff forms apply image decoding/format/size checks and image re-encoding; PDF extension/signature/size checks exist. This is not a full PDF-content safety assessment. Production media serving depends on the documented untrusted-download configuration.
- Production/cPanel: Passenger entry point, environment-based secret/host validation, secure cookies/HTTPS defaults, database URL support and static collection instructions exist. Actual Passenger Python/dependency installation, TLS/proxy scheme recognition, media alias/headers and database setup were not observable here. Do not treat this report as live-host approval.
- Responsive/accessibility: responsive public/dashboard styles, labels, skip link, focus styling, reduced-motion handling and native CSS/JS animations are present. Finding 5 concerns a specific keyboard interaction. Desktop/mobile rendering and image loading rely on the main agent's browser review; no fresh browser pass or suite results are claimed.
- Content provenance: seed contains no engineering variant rows or invented news; source notes map imagery to supplied references. Finding 3 identifies a new-family fallback that violates this policy. Original references exist in the final project's separate reference directory; this staging directory does not itself contain that directory, so delivery must preserve it as planned.

## Review checklist coverage

The clean-code-guard checklist was applied for correctness; user instructions exclude style-only findings.

- Naming/functions: no additional actionable correctness finding.
- Comments/formatting: no actionable finding; style excluded.
- SOLID: no additional actionable correctness finding.
- DRY/KISS/YAGNI: no additional actionable correctness finding.
- Failure modes/input boundaries: findings 1–5 cover unsafe conversion, disconnected behavior, invented fallback content, omitted data and focus-state handling.
