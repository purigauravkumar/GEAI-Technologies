# GEAI Technologies website

A responsive static website for GEAI Technologies, built with semantic HTML, CSS, and vanilla JavaScript. It is hosted with GitHub Pages.

## Active files

- `index.html` — page structure and content
- `css/style.css` — layout, responsive styling, hero video overlay, and section visuals
- `assets/images/` — image assets used by the service, About, and Contact sections, plus the favicon (`favicon.png` is a placeholder monogram; replace it with the real brand mark)
- `assets/logos/` — platform logos used in the Technology section
- `assets/videos/hero-server-room.mp4` — muted looping hero background video (1080p, desktop)
- `assets/videos/hero-server-room-mobile.mp4` — lighter 720p encode used on screens up to 900px wide
- `assets/certificates/` — retained certificate image assets for possible future use

The root-level legacy `styles.css` and `script.js` files have been removed because the active page does not use them. The empty `js/script.js` placeholder has also been removed.

## Preview locally

Open `index.html` in a browser. To serve it locally with Python, run the following from the repository root:

```bash
python -m http.server 8080
```

Then visit `http://localhost:8080`.

## GitHub Pages

This repository uses relative asset paths so the site can be served from the repository's GitHub Pages project URL. In GitHub, check **Settings → Pages** to confirm the deployment branch and publishing source.

After changes are merged into the configured publishing branch, check **Actions** or the Pages deployment status before validating the live site.

## Notes

- The hero video is muted and loops without a poster image. Its file is chosen by the small script directly after the `<video>` element (`data-src` for desktop, `data-src-small` for screens up to 900px wide) and **not** with a `<source>` element: a `<source>` in the markup starts downloading before the script can run, so the reduced-motion check and the small-screen choice would be a race. Do not move the URLs back into `<source>` tags (a test guards this).
- When a visitor enables reduced motion, the script never assigns a video file (nothing is downloaded), the video element is hidden by CSS, and `assets/images/server-room.jpg` is used as a still hero background. Visitors with JavaScript disabled get the same still image through a `<noscript>` rule. The same image is also used as the Contact section background.
- Keep images web-sized: photos no wider than about 2400px (backgrounds) or 1600px (cards and panels), logos no larger than 512px. A single 48-megapixel photo decodes to roughly 190 MB of memory and freezes scrolling on phones. `tests/test_site.py` fails if an image exceeds the size budget.
- The Contact button uses a `mailto:` link. It opens the visitor's configured email application; it is not a server-side contact form.
- GitHub Pages serves static files. Persistent forms, logins, shared likes, and database-backed features require a backend or external service.
- Google Fonts are loaded remotely; system font fallbacks are provided.
