# GEAI Technologies website

A responsive, static business website for GEAI Technologies. Built with semantic HTML, CSS animations, and vanilla JavaScript; no framework, build step, API key, or paid hosting is required.

## Files
- `index.html` — site structure and copy
- `styles.css` — visual system, responsive layout, and CSS animations
- `script.js` — mobile navigation, scroll reveals, active navigation, and certificate preview modal
- `assets/certificates/` — four supplied certificate images

## Preview locally
Open `index.html` in a browser. For a local server, run `python -m http.server 8080` from this directory and visit `http://localhost:8080`.

## Deploy to GitHub Pages
1. Create a repository for the business website, or use a dedicated `docs/` folder in an existing repository.
2. Upload `index.html`, `styles.css`, `script.js`, and the entire `assets/` directory while preserving paths.
3. In GitHub, open **Settings → Pages**.
4. Select **Deploy from a branch**, choose the branch containing the files, and select `/ (root)` (or `/docs` if these files are placed in that folder).
5. Save and wait for the Pages deployment to finish.

For a dedicated repository named `geai-technologies`, the default Pages address is normally `https://<GitHub-username>.github.io/geai-technologies/` once Pages is enabled.

## Before public launch
- Add the original `Computer Hardware Basics` certificate image if you want its preview to show the document itself. The course is listed accurately, but the uploaded certificate image was not among the supplied files.
- Add a verified certificate link if available. Do not publish private QR codes or personal information unless intended.
- Review the wording about project maturity and confirm every public claim.
- Consider adding a custom domain only when one is available.
- GitHub Pages hosts static files only. Shared/persistent likes, a contact form that sends messages, login, and database-backed features require a backend or external service. This build intentionally uses no fake persistent like counts or nonfunctional form.

## Notes
The certificate preview images are displayed as supplied. The site does not independently validate their authenticity. Google Fonts are loaded remotely; system font fallbacks remain available.
