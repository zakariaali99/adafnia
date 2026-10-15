# Adafnia factory

Django 5.2 bilingual factory site with a custom Arabic staff dashboard. Python 3.11+ recommended. Final deployment directory: `/Users/zakaria/projects/Claude/adafnia`; implementation staging directory: `/Users/zakaria/projects/Claude/talks./adafnia-build`. Preserve `reference/` when copying source to the final directory.

## Local setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DJANGO_DEBUG=1
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_content
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Environment variables must be exported by the shell or hosting environment; `.env.example` is documentation and is not automatically loaded. No credentials are seeded. `/ar/` and `/en/` are public; `/dashboard/` requires an active staff account. Django admin is also available at `/admin/`. All staff users can manage all content: grant staff status only to trusted content editors. Logout uses POST.

## Editing

Manage categories before products. Products/projects default to draft. Add engineering variants separately and check `approved` only after review against the manufacturer's source. Slugs are generated automatically and hidden from employees; edits preserve existing URLs. The seed adds PE100 straight pipes and coils with extracted images, four reference projects without invented years/quantities, four actual sales centres and a factory address without assigning a sales telephone to the factory. Existing products and branches are never corrected or unpublished by the seed. No database is cleared. Certificate expiry archival remains date-based. Sales-centre additional phone numbers are preserved in bilingual descriptions. All imagery uses supplied references only; no fabricated imagery is generated. Verify contact details before publication.

News with status `published` and a future `published_at` stays hidden until its scheduled time, without a worker. Times in the dashboard use Africa/Tripoli. Certificates expiring before today are excluded from current certificates and available in the archive. `seed_content` also sets expired certificates inactive; renewed certificates must be explicitly reactivated. Null expiry means no recorded expiry, not independently verified certification. Upload certificate PDFs and enter actual expiry dates from the supplied references; no certificate dates are invented. Run `python manage.py seed_content` when archival flags need updating; public expiry filtering works continuously regardless.

Uploads accept JPEG/PNG/WebP images up to 5 MB (decoded/verified with Pillow). Dashboard images become WebP copies, fit within 1920 by 1920 pixels with EXIF orientation corrected; source files are never edited. Resource PDFs accept up to 32 MB to accommodate the actual profile, while certificate/settings PDFs retain a 10 MB limit. Extension and PDF signature are checked. Upload rights are staff-only. Replacing/deleting records preserves old files; clean orphans only after backups and review. Uploaded URLs are not confidential storage. Set the web server request limit to at least 35 MB.

The supplied certificate PDF records ISO 9001:2015 (23.03.530-QM), ISO 14001:2015 (23.03.530-EM), and ISO 45001:2018 (23.03.530-OHS), issued 11 May 2023 and expiring 10 May 2026. These seed as inactive archival records. Pass `seed_content --reference-dir /absolute/path/to/reference` to attach certificate PDFs and the company profile Resource; missing files can be attached on later runs. No engineering measurements are seeded. Active certificates expiring within 30 days appear on the dashboard home.

## Public template contract

Backend owns `config/`, `factory/`, `templates/dashboard/`, `static/dashboard.css`, migrations, requirements and deployment docs. Frontend owns `templates/site/*`, `static/site.css`, `static/site.js` and reference assets.

Every public context has `lang`, `is_ar`, `prefix`, `settings`, `current_path` (locale-free, NO leading slash), `nav_path` (locale-free with leading slash), `categories`, `branches`, `products`, `news`, `projects`, `certificates`, `archived_certificates`, `resources`, and `form`. Switch languages with `/en/{{ current_path }}` or `/ar/{{ current_path }}`. Product/news/project lists use `page_obj` with 12 items. Product filters accept `q`, `category` (primary key or legacy slug), and `page`, exposing `q` and `selected_category`. Categories shown publicly have published products.

Detail pages expose `object` plus `product`, `article`, or `project`; products additionally expose `variants` containing approved rows. Product related `variants.all` is prefetched with the same approval filter. Draft records and future news return 404 on detail routes. Public paths: `/<lang>/`, `about/`, `products/`, `products/<slug>/`, `news/`, `news/<slug>/`, `projects/`, `projects/<slug>/`, `quality/`, `resources/`, `contact/`. Named URL identifiers match page names, details use `product_detail`, `news_detail`, `project_detail`; all take `lang`.

Load `site_tags`. Use `{% translated object 'title' lang %}`, `{% translated object 'description' lang %}`, or `{{ object|tr:lang }}` / `{{ object|field:'description'|tr:lang }}`. Blank translations fall back to Arabic then English. All content remains autoescaped; render body with `linebreaks`, not `safe`. Guard optional images/files with `{% if object.image %}` before `.url`. Resource and certificate document attribute is `file`; settings profile PDF is `profile`. Settings has title/tagline/about/address bilingual fields and phone/whatsapp/email.

Contact POST requires CSRF, name, phone, subject, message; email/product optional, hidden honeypot `website`. Render `form.non_field_errors` and each field's errors. Successful submissions redirect to `/<lang>/contact/?success=1` and add a Django success message. A populated honeypot follows the same redirect but is not stored. Database-backed limit: five attempts per source IP per hour, then HTTP 429 with form error. Configure the trusted web server to set REMOTE_ADDR appropriately; application does not trust forwarded headers. Old throttle records contain salted hashes and can be periodically purged.

`GET /<lang>/api/variants/?product=<id-or-slug>&diameter_mm=...&pressure_bar=...&sdr=...` returns `{ "results": [...] }`, at most 500 approved variants belonging to published products. Numbers are decimal strings or null. Rows include id, product_id, translated product, diameter_mm, pressure_bar, sdr, wall_mm, weight_kg_m, length_m. Invalid numeric filters return 400; mutations return 405.

## Production / Passenger

Install requirements in the hosting virtualenv, point Passenger's application root at the final project and startup file at `passenger_wsgi.py`, and choose that virtualenv's Python executable. Export `DJANGO_DEBUG=0`, a long random `DJANGO_SECRET_KEY`, comma-separated `DJANGO_ALLOWED_HOSTS`, HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL` (PostgreSQL recommended for concurrency). Missing secret/hosts fails closed. SQLite is for local/small single-instance use. Run migrations, create your own administrator, seed once, and run `collectstatic --noinput`. Passenger imports `application` from `config.wsgi`. Gunicorn alternative: `gunicorn config.wsgi:application`.

Terminate HTTPS at a correctly configured trusted server. If TLS terminates at a proxy, configure HTTPS recognition there; this app deliberately does not globally trust spoofable forwarding headers. Redirect HTTP to HTTPS. Serve `/static/` from `staticfiles/` (WhiteNoise also handles collected static) and `/media/` as untrusted downloads with no script execution, `X-Content-Type-Options: nosniff`, and preferably a separate cookie-free media host. Never serve the project root, database or reference source directory as a web directory. Reference artwork intended for the site must be copied to public static assets by the frontend build. Back up database and media together. Use a production database account with least privilege and keep secrets outside the source tree.

```sh
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
DJANGO_DEBUG=1 python manage.py test factory
```

Detail routes accept numeric primary keys as well as slugs. Product detail exposes distinct ordered `diameters` and non-null `pressures` from approved variants. Contact GET with `product=<pk>&variant=<pk>` pre-fills the quote with exact stored approved dimensions; unpublished, unapproved and mismatched variants are excluded. Labels, product choices and validation errors follow the route language through rendering.

Dashboard login permits ten POST attempts per source IP in a 15-minute window, stored in a separate database throttle namespace. The window expires automatically and cannot permanently lock an account. Public contact has its own five-attempt hourly bucket.

Tests render all real public templates in both languages, exercise numeric and slug detail routes, and load supplied reference files into temporary test storage. Browser interaction review remains a separate frontend check.

SEO endpoints: `/robots.txt` excludes dashboard/admin crawling and points to `/sitemap.xml`. The sitemap uses the validated request hostname and scheme, includes Arabic and English public pages and published product/news/project primary-key detail URLs, excludes drafts/future news, and supplies news publication dates as `lastmod`. It does not list slug aliases, media or API routes.
