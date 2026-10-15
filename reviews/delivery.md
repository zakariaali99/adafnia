# Local delivery verification

15 October 2026. Final project: /Users/zakaria/projects/Claude/adafnia.

- Complete supplied assets preserved under reference/.
- New isolated Django runtime installed in .venv/; database migrated and reference seed loaded.
- Local website on http://127.0.0.1:8766/ar/ and English at /en/.
- Custom Arabic dashboard at /dashboard/. Local account details in ignored LOCAL_ACCESS.md, mode0600.
- Desktop1440px and mobile390px route matrix: all tested public pages200 and no horizontal overflow; language switching retains page path.
- Authenticated dashboard: product/variant/news/project/certificate/resource/branch/enquiry/settings listings200; mobile dashboard no overflow.
- Intro skip, reduced-motion bypass and keyboard focus restoration verified in browser.
- Malformed query IDs return400; sitemap and robots200; no browser console errors.
- Production-mode Django security check reports no issues using temporary verification-only environment values. Actual hosting still requires its domain, credentials, TLS/media configuration and a separate production administrator.
- Automated integration coverage includes staff authorization, CSRF, draft/scheduling privacy, certificate expiry, validated/re-encoded uploads, bilingual templates, quote variants, enquiries/throttling, idempotent seed, settings/branch visibility, malformed IDs and SEO routes.

No live deployment was performed. News and engineering values were not invented. Approve engineering rows in the dashboard before publication; the original catalogue remains downloadable.
