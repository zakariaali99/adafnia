# Original / v1 / v2 visual comparison

The original was run from an isolated temporary copy at localhost:8770 with its original Django4.2.24 dependencies and compiled Tailwind CSS. Both desktop1440x1000 and mobile390x844 were inspected. Original project files and database were not modified.

Observed original strengths: full-screen industrial image, heavy Cairo typography, white/cyan headline contrast, more visual density and clear product cards. V1 lost those strengths through its neutral split hero, small typography, sparse sections and text-heavy presentation.

V2 intentionally combines them:
- Original industrial hero artwork, used decoratively rather than as a new documentary claim, with an immersive navy/cyan treatment and large locally hosted Cairo variable headings.
- V1 verified capabilities, source photographs and functional bilingual/admin system.
- New photographic product catalogue cards, integrated PDF library link, real aerial factory story and stronger timeline.
- New accessible manufacturing image tabs: material, production and inspection. Arrow/Home/End keyboard controls and reduced-motion support.
- New project map using the existing Remal Natural Earth110m Libya outline; factory at Misurata and documented cities Tripoli/Sabratha. Project focus/hover highlights its corresponding known city. No location assigned to Al-Afiya without evidence.
- More graphic applications, project cards and newsroom; matched inner-page mastheads, cards and footer.
- Richer dark/cyan animated intro; prior skip/session/focus handling preserved.

Actual project photographs were not invented; source-backed names and optional editable images remain. ISO records retain their archival/current statuses. Placeholder production statistics from the original (15+,5000+) were not copied into the new site.

V1 public templates and styling are preserved in reviews/v1-snapshot/. Source reference images remain in reference/.

Verification: all28 backend tests passed after the complete home rewrite. Arabic/English mobile route matrix18pages returned200 without document overflow. Homepage widths320,390,768,1024,1440 in both languages have no document/header overflow; CTAs stay visible in the opening viewport. Manufacturing click and RTL keyboard navigation change the selected tab and visible panel. Known project focus/hover highlights its map city. Intro Skip focus, closing and reduced-motion bypass pass. Header switches to solid below the hero. Browser console reports no errors.

Final browser review identified and fixed a mobile containment issue: header backdrop-filter was containing the fixed menu. Backdrop filtering is disabled below1024px so the open menu fills the viewport beneath the76px header. Menu focus entry waits for the300ms visibility transition, Tab stays within its controls, and Escape restores toggle focus. Updated assets carry a release query to invalidate older browser caches.
