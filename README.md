# GEAI Technologies website

A responsive static website for GEAI Technologies, built with semantic HTML, CSS, and vanilla JavaScript. It is hosted with GitHub Pages.

## Active files

- `index.html` — page structure and content
- `css/style.css` — layout, responsive styling, hero video overlay, and section visuals
- `assets/images/` — image assets used by the service, About, Contact, and video poster sections
- `assets/logos/` — platform logos used in the Technology section
- `assets/videos/hero-server-room.mp4` — muted looping hero background video
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

- The hero video is muted and loops; `assets/images/server-room.jpg` is its poster and is also used as the Contact section background.
- The Contact button uses a `mailto:` link. It opens the visitor's configured email application; it is not a server-side contact form.
- GitHub Pages serves static files. Persistent forms, logins, shared likes, and database-backed features require a backend or external service.
- Google Fonts are loaded remotely; system font fallbacks are provided.
