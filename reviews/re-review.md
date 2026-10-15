# Scoped re-review of final five findings

Reviewed 2026-10-15. Scope: the five findings in `reviews/final-review.md`, their fixes, and direct regressions introduced by those fixes. Inspected current identifiers/views, new backend test definitions, public includes and their callers, translation/context helpers, and menu/intro code. No tests rerun, no subagents, no source edits. This report is the only write. Conclusions are from source inspection, not fresh browser execution.

## Verdict

The five original failure paths are corrected in source. **Scoped acceptance still needs one P2 fix below**: the new settings address display conflicts with the existing factory Branch source. One P3 empty-state regression should also be corrected. No new P0/P1 issue found within this scope. This does not replace the main agent's suite/browser results or certify broader production readiness.

## Original finding disposition

| Finding | Disposition | Evidence |
| --- | --- | --- |
| 1. Numeric IDs cause uncontrolled exceptions | Fixed | `factory/identifiers.py:5-24` bounds positive ASCII IDs to signed 64-bit range and separates bounded slugs. `factory/views.py` catches invalid product/variant/category/API identifiers with 400 and invalid detail identifiers with 404. Public publication/approval filters remain in place. |
| 2. Settings do not reach public pages | Original disconnected fields fixed; address regression below | `templates/site/base.html:5` uses translated settings title; `home.html:4` uses tagline; `about.html:1` includes `editable_company.html`; `resources.html:1` includes the guarded settings profile link; `contact.html:1` includes settings address. New includes load their own tag library, retain escaping, and use bilingual fallback. This closes the named disconnected controls, not the broader claim that every static editorial passage is editable. |
| 3. Invented PE100 fallback | Fixed | `templates/site/home.html:8` now renders `product.material` directly. A blank product material no longer becomes a grade assertion. |
| 4. Missing secondary branch numbers | Fixed | `templates/site/contact.html:1` renders translated branch descriptions when either language is populated, exposing the additional numbers preserved by the seed. |
| 5. Menu/intro focus handling | Fixed in inspected paths | `static/site.js:5-9` returns focus to the menu toggle when closing navigation containing focus. Lines 25–43 focus Skip on intro entry, make skip-link/header/main/footer inert, remove inert on exit, and restore the initiator or brand. `templates/site/home.html:17` declares the intro dialog/modal. Reduced-motion early return remains intact. Browser behavior was not rerun. |

The new tests in `factory/tests.py:18-37` cover adversarial identifier requests in both languages plus parser boundaries. They were read, not executed; no passing-test claim is made here.

## Direct regressions

### [P2] Two independently editable factory addresses can contradict each other

Locations: `templates/site/contact.html:1`, `templates/site/contact_address.html:2`. Supporting existing data flow: `factory/context.py:10`, `factory/management/commands/seed_content.py:26-30`.

Contact now renders settings address, then every Branch. The normal seed already creates a factory Branch with its own address, so the factory address appears twice. If staff correct the address in Settings, the new “Factory address” card changes but the “Adafnia Factory” card immediately below retains the old address. Editing the Branch instead creates the opposite disagreement. This makes the new address control misleading for visitors and editors.

Fix: choose one authoritative factory-address record. For example, retain the factory as an explicitly identified Branch and update/render that record through the intended editor, or render Settings for the factory and exclude only the explicitly identified factory Branch while keeping sales centres. Avoid identifying the factory by mutable display text. Ensure an edit cannot leave a second stale factory address on Contact.

### [P3] A profile-only library displays a contradictory empty state

Locations: `templates/site/resources.html:1`, `templates/site/profile_download.html:2`.

When `settings.profile` is present and Resource records are empty, the new include renders “Latest company profile” with a working download, but the Resource loop's `{% empty %}` also renders “Documents on request” and asks visitors to contact the company for its profile. This is a new valid configuration introduced by the Settings profile fix.

Fix: show that empty state only when both `resources` and `settings.profile` are absent, or make it explicitly refer to additional documents rather than the profile already available.

## Quality and compliance within scope

Identifier boundary handling, material provenance, secondary contact data and the requested focus restoration now match the five findings' intended corrections. Settings integration is functional, with the address conflict above preventing unconditional acceptance. No style-only changes are requested. No unrelated routing, dashboard, deployment or content audit was reopened.

## Follow-up verdict: two regressions closed

Verified by source inspection on 2026-10-15, limited strictly to the two regressions above. This verdict supersedes their earlier open status.

- **P2 factory-address conflict: fixed.** `factory/models.py:82` adds the explicit `Branch.is_factory` flag; migration `0003` adds its database field. `factory/context.py:10` supplies only branches with `is_factory=False`, while Contact renders the canonical Settings address through `contact_address.html`. `factory/management/commands/seed_content.py:26-34` flags newly seeded factory records and marks the known existing seed record without replacing editorial address fields. Public filtering uses the flag rather than display text. Existing installations require migration and the seed/record flagging step; migration alone defaults existing flags to false. Execution of those steps was not checked here.
- **P3 profile-only empty state: fixed.** `templates/site/resources.html:1` guards the Resource loop's empty state with `{% if not settings.profile %}`. A settings profile suppresses the contradictory message; no profile plus no resources still displays the intended empty state.

**Scoped verdict: accepted in source; both reported regressions closed, with no remaining finding in this two-fix review.** No tests or browser checks were run, no broader audit was performed, and no source files were edited. Only this report was appended.
