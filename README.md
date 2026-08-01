# Bradley Homes & Rentals — Demo Site

Static, no-build HTML/CSS demo for Bill & Brenda Bradley (Evart, MI).
Every page uses **sample content** marked with a "Website preview" banner.

## What's included
- `index.html` — Home (hero, welcome, feature cards)
- `rentals.html` — Sample rental listings
- `sale.html` — Sample homes for sale
- `maintenance.html` — Maintenance request form (demo, not live)
- `contact.html` — Contact info + contact form (demo, not live)
- `about.html` — Bill & Brenda story (sample text)
- `css/styles.css` — Design system (rural Michigan blue/green/gray)
- `assets/` — Logo + sample property illustrations (SVG)

## Deploy to GitHub Pages (free)
1. Create a new repo on GitHub (e.g. `bradley-homes-demo`).
2. Push this folder:
   ```
   git init
   git add .
   git commit -m "Bradley Homes demo"
   git branch -M main
   git remote add origin https://github.com/YOURUSERNAME/bradley-homes-demo.git
   git push -u origin main
   ```
3. In the repo: **Settings → Pages → Source: main / root** → Save.
4. Wait ~1 minute, then visit `https://YOURUSERNAME.github.io/bradley-homes-demo/`.

Share that link with Bill & Brenda to show the concept before negotiating scope/price.

## Before going live (real build)
- Replace sample listings with real properties + photos.
- Write the real About story with Bill & Brenda.
- Wire forms to email (Formspree free tier or Netlify Forms).
- Register a real domain (e.g. bradleyhomesandrentals.com) and point it at the site.
- Swap the placeholder logo for the digitized napkin logo.
- Remove the "Website preview" banner.
