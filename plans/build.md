# Adafnia rebuild implementation plan

Approved 2026-10-15 by the owner after the complete design discussion. Build immediately; bilingual Arabic/English; hosting ready; use supplied references; allow new product families; manage certificates and expiry from dashboard; projects may be presented; owner paid and needs delivery now.

Architecture: Django 5.2 LTS server-rendered site, custom staff dashboard, SQLite locally with DATABASE_URL-ready production configuration, local static assets, accessible native CSS/JS motion. No external imagery or fabricated product measurements. Original project is a read-only reference.

## Deliverables
1. Backend: config, catalog with arbitrary families and typed pipe variants, news drafts/scheduling, projects, certificates/expiry, branches, documents, enquiries, settings, Arabic custom dashboard CRUD with upload validation, login/logout, pagination and search. Public URLs /ar/ and /en/. Dashboard /dashboard/.
2. Public presentation: elegant industrial blue/white layout, real reference artwork, water/pipe logo intro with skip and reduced-motion support, homepage, about, catalog/filter selector, product detail, news/detail, projects/detail, quality, technical downloads, contact/quote, responsive mobile menu and language switching.
3. Content: preserve complete original assets under reference/, extract reusable photographs from PDF, seed verified narrative and product families without inventing engineering values. Existing expired certificates marked archival. All material editable.
4. Verification: integration tests for draft visibility, expiry, staff access, uploads, contact/quote and bilingual routes; browser review desktop/mobile; document setup, content editing and Passenger deployment.

## Ownership and interfaces
Backend implementer owns Python, dashboard templates/CSS, requirements, migrations, tests, README. Main agent owns public templates, static/site.css, static/site.js, reference extraction. Public views render site/home.html, site/about.html, site/products.html, site/product_detail.html, site/news.html, site/news_detail.html, site/projects.html, site/project_detail.html, site/quality.html, site/resources.html, site/contact.html.

Context contract: lang='ar'|'en', is_ar boolean, prefix='/' + lang, settings SiteSettings instance, nav_path current path with locale stripped, products/news/projects/certificates/resources/branches as appropriate. Translated models expose title_ar/title_en, description_ar/description_en and optional image. Template tag library site_tags provides translated attr filter `tr` (usage object|tr:lang for title and object|field:'description'|tr:lang if desired; agree via agent message), localized field access `translated` as simple_tag `{% translated object 'title' lang %}`. Product fields category, material, image, variants. Variant diameter_mm, pressure_bar, sdr, wall_mm, weight_kg_m, length_m, approved. Contact form carries name, phone, email optional, subject, message, honeypot website. All POST forms CSRF protected.

## Progress
- Reference copied to final project reference/.
- Implementation in adafnia-build temporary workspace because final folder requires escalated write; sync reviewed source into final project without removing inputs/reference.
