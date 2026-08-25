#!/usr/bin/env python3
"""
Bradley Homes & Rentals - static site generator.

Edit listings.csv (open in Excel/Sheets, then export as CSV), then run:
    python build.py

Generates: index.html, rentals.html, sale.html, listing-<id>.html
Other pages (maintenance, contact, about) are hand-written static files.

NOTE: all JavaScript lives in the *_JS constants below as plain (non-f)
strings so curly braces never conflict with f-string formatting.
"""
import csv
import html
import os
import re
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT, "listings.csv")
EMAIL = "wbradley58@sbcglobal.net"
PHONE_DISPLAY = "(231) 920-6168"
PHONE_TEL = "+12319206168"
FORMSPREE = "https://formspree.io/f/REPLACE_ME"

PREVIEW_BANNER = ''

def header(active=""):
    links = [
        ("rentals.html", "Rentals"),
        ("sale.html", "Homes for Sale"),
        ("we-buy-houses.html", "We Buy Houses"),
        ("apply.html", "Apply"),
        ("about.html", "About"),
        ("contact.html", "Contact"),
    ]
    nav_items = []
    for href, label in links:
        classes = []
        if active == href:
            classes.append("nav-active")
        if href == "contact.html":
            classes.append("nav-contact")
        cls = ' class="{}"'.format(" ".join(classes)) if classes else ""
        nav_items.append('<a{cls} href="{href}">{label}</a>'.format(cls=cls, href=href, label=label))
    return '''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="index.html">
      <img src="assets/logo.svg" alt="Bradley Homes & Rentals logo">
      <span>Bradley Homes &amp; Rentals</span>
    </a>
    <nav class="nav-links">{nav}</nav>
    <a class="header-phone" href="tel:{tel}">{phone}</a>
  </div>
</header>'''.format(nav="".join(nav_items), tel=PHONE_TEL, phone=PHONE_DISPLAY)

FB_ICON = '<svg class="soc-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5 3.66 9.15 8.44 9.94v-7.03H7.9v-2.91h2.54V9.85c0-2.52 1.5-3.91 3.78-3.91 1.1 0 2.24.2 2.24.2v2.47h-1.26c-1.24 0-1.63.78-1.63 1.57v1.88h2.78l-.44 2.91h-2.34V22c4.78-.79 8.44-4.94 8.44-9.94Z"/></svg>'

FOOTER = '''
<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-col footer-brand">
      <p class="footer-name"><strong>Bradley Homes &amp; Rentals</strong></p>
      <p>Local, family-owned. Serving Evart and the surrounding Central Michigan communities.</p>
      <p class="footer-phone"><a href="tel:{tel}">{phone}</a></p>
      <p class="footer-email"><a href="mailto:{email}">{email}</a></p>
    </div>
    <div class="footer-col">
      <p class="footer-h">Explore</p>
      <ul class="footer-nav">
        <li><a href="rentals.html">Rentals</a></li>
        <li><a href="sale.html">Homes for Sale</a></li>
        <li><a href="we-buy-houses.html">We Buy Houses</a></li>
        <li><a href="apply.html">Apply</a></li>
        <li><a href="about.html">About</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <p class="footer-h">Connect</p>
      <p class="footer-social">
        <a href="https://facebook.com/" target="_blank" rel="noopener" class="soc-link">{fb}Facebook</a>
      </p>
      <p class="footer-fair">Committed to fair housing. We do not discriminate on the basis of race, color, religion, sex, national origin, familial status, disability, or any other protected class.</p>
    </div>
  </div>
  <p class="footer-copy">&copy; {year} Bradley Homes &amp; Rentals. All rights reserved.</p>
</footer>'''.format(tel=PHONE_TEL, phone=PHONE_DISPLAY, email=EMAIL, year=2026, fb=FB_ICON)

CONTACT_CTA = '''
<section class="cta-strip">
  <div class="container cta-strip-inner">
    <div class="cta-strip-text">
      <h3>Can't find what you're looking for?</h3>
      <p>Call or text Bill &amp; Brenda &mdash; we'll help you find the right home.</p>
    </div>
    <div class="cta-strip-actions">
      <a class="btn btn-light" href="tel:{tel}">{phone}</a>
      <a class="btn btn-outline-light" href="apply.html">Apply for a Rental</a>
      <a class="btn btn-outline-light" href="contact.html">Contact Us</a>
    </div>
  </div>
</section>'''.format(tel=PHONE_TEL, phone=PHONE_DISPLAY)

SHARED_JS = '''
<script>
(function(){
  function wireCarousel(cc){
    var track = cc.querySelector('.cc-track, .rc-track');
    if(!track) return;
    var slides = track.children;
    var n = slides.length, i = 0;
    function show(){
      if(!slides.length) return;
      var slide = slides[i];
      var w = slide.offsetLeft;
      track.style.transform = 'translateX(' + (-w) + 'px)';
    }
    cc.querySelector('.cc-prev, .rc-prev').addEventListener('click', function(e){ e.preventDefault(); i=(i-1+n)%n; show(); });
    cc.querySelector('.cc-next, .rc-next').addEventListener('click', function(e){ e.preventDefault(); i=(i+1+n)%n; show(); });
    show();
    window.addEventListener('resize', show);
  }
  document.querySelectorAll('.card-carousel, .rc-carousel').forEach(wireCarousel);
  document.querySelectorAll('.scroll-row').forEach(function(row){
    var wrap = row.closest('.container');
    var prev = wrap.querySelector('.feat-prev');
    var next = wrap.querySelector('.feat-next');
    if(prev) prev.addEventListener('click', function(){ row.scrollBy({left:-340,behavior:'smooth'}); });
    if(next) next.addEventListener('click', function(){ row.scrollBy({left:340,behavior:'smooth'}); });
  });
})();
</script>'''

DETAIL_JS = '''
<script>
(function(){
  var track = document.getElementById('track');
  var slides = Array.prototype.slice.call(track.children);
  var dotsWrap = document.getElementById('dots');
  var n = slides.length, idx = 0;
  slides.forEach(function(_, i){
    var d = document.createElement('button');
    d.className = 'car-dot';
    d.setAttribute('aria-label', 'Go to photo ' + (i+1));
    d.addEventListener('click', function(){ go(i); });
    dotsWrap.appendChild(d);
  });
  var dots = Array.prototype.slice.call(dotsWrap.children);
  function setActive(){
    slides.forEach(function(s, i){ s.classList.toggle('is-active', i === idx); });
    dots.forEach(function(d, i){ d.classList.toggle('is-active', i === idx); });
  }
  function go(to){
    idx = (to + n) % n;
    var slide = slides[idx];
    var offset = slide.offsetLeft - (track.parentElement.clientWidth - slide.clientWidth) / 2;
    track.style.transform = 'translateX(' + (-offset) + 'px)';
    setActive();
  }
  window.carGo = function(dir){ go(idx + dir); };
  go(0);
  window.addEventListener('resize', function(){ go(idx); });
})();
</script>'''

GRID_JS = '''
<script>
(function(){
  document.querySelectorAll('.card-carousel').forEach(function(cc){
    var track = cc.querySelector('.cc-track');
    var slides = track.children;
    var n = slides.length, i = 0;
    function show(){ if(!slides.length) return; var w = slides[i].offsetLeft; track.style.transform = 'translateX(' + (-w) + 'px)'; }
    cc.querySelector('.cc-prev').addEventListener('click', function(){ i=(i-1+n)%n; show(); });
    cc.querySelector('.cc-next').addEventListener('click', function(){ i=(i+1+n)%n; show(); });
    show();
    window.addEventListener('resize', show);
  });
  document.querySelectorAll('.scroll-row').forEach(function(row){
    var wrap = row.closest('.container');
    var prev = wrap.querySelector('.feat-prev');
    var next = wrap.querySelector('.feat-next');
    if(prev) prev.addEventListener('click', function(){ row.scrollBy({left:-340,behavior:'smooth'}); });
    if(next) next.addEventListener('click', function(){ row.scrollBy({left:340,behavior:'smooth'}); });
  });
  var grid = document.getElementById('listings-grid');
  var pills = document.querySelectorAll('.filter-pill');
  var selBeds = 'any', selBaths = 'any', sort = 'featured';
  pills.forEach(function(p){
    p.addEventListener('click', function(){
      var group = p.dataset.beds!==undefined ? 'beds'
                : p.dataset.baths!==undefined ? 'baths' : 'sort';
      pills.forEach(function(x){
        if((group==='beds' && x.dataset.beds!==undefined) ||
           (group==='baths' && x.dataset.baths!==undefined) ||
           (group==='sort' && x.dataset.sort!==undefined)) x.classList.remove('is-active');
      });
      p.classList.add('is-active');
      if(group==='beds') selBeds = p.dataset.beds;
      if(group==='baths') selBaths = p.dataset.baths;
      if(group==='sort') sort = p.dataset.sort;
      applyFilters();
    });
  });
  function applyFilters(){
    var cards = Array.prototype.slice.call(grid.children);
    var vis = [];
    cards.forEach(function(c){
      var ok = true;
      if(selBeds!=='any' && (+c.dataset.beds) < (+selBeds)) ok = false;
      if(selBaths!=='any' && (+c.dataset.baths) < (+selBaths)) ok = false;
      c.style.display = ok ? '' : 'none';
      if(ok) vis.push(c);
    });
    vis.sort(function(a,b){
      if(sort==='featured'){
        var fa = a.dataset.featured==='yes' ? 0 : 1;
        var fb = b.dataset.featured==='yes' ? 0 : 1;
        if(fa !== fb) return fa - fb;
        return (+a.dataset.price)-(+b.dataset.price);
      }
      if(sort==='price-asc') return (+a.dataset.price)-(+b.dataset.price);
      if(sort==='price-desc') return (+b.dataset.price)-(+a.dataset.price);
      return 0;
    });
    vis.forEach(function(c){ grid.appendChild(c); });
    document.getElementById('no-results').style.display = vis.length ? 'none' : 'block';
  }
})();
</script>'''


def esc(x):
    return html.escape(str(x).strip())


def load_listings():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def photo_list(row):
    raw = row.get("photos", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def feature_list(row):
    raw = row.get("features", "")
    return [f.strip() for f in raw.split(";") if f.strip()]


def num_price(s):
    digits = re.sub(r"[^0-9.]", "", str(s))
    try:
        return float(digits)
    except ValueError:
        return 0.0


def listing_type(row):
    return row["type"].strip().lower()


def detail_theme(row):
    t = listing_type(row)
    if t == "rent":
        return "listing-rent"
    if t == "sale":
        return "listing-sale"
    if "land" in t:
        return "listing-lc"
    return "listing"


def is_new(row):
    return row.get("new", "").strip().lower() == "yes"


def is_featured(row):
    return row.get("featured", "").strip().lower() == "yes"


def map_embed_url(row):
    q = urllib.parse.quote(esc(row.get("address", "")) + ", Evart, MI")
    return "https://www.google.com/maps?q={0}&z=13&output=embed".format(q)


# ---------------- listing card (horizontal, Zillow-style) ----------------
def listing_card(row, horizontal=True):
    lid = esc(row["id"])
    t = esc(row["title"])
    price = esc(row.get("price", ""))
    beds = esc(row.get("beds", ""))
    baths = esc(row.get("baths", ""))
    addr = esc(row.get("address", ""))
    avail = esc(row.get("available", ""))
    pnum = num_price(row.get("price", ""))
    feats = feature_list(row)
    highlights = "; ".join(feats[:3]) if feats else ""

    new_badge = '<span class="badge-new">New</span>' if is_new(row) else ""
    feat_ribbon = '<span class="badge-featured">Featured</span>' if is_featured(row) else ""
    feat_class = " card-featured" if is_featured(row) else ""

    # first photo as the card thumbnail
    first = photo_list(row)[0] if photo_list(row) else "property1.svg"
    slides = []
    for i, p in enumerate(photo_list(row)):
        slides.append('<div class="cc-slide"><img src="assets/photos/{0}" alt="{1} photo {2}"></div>'.format(esc(p), t, i + 1))
    slides_html = "\n".join(slides)

    avail_line = '<span class="row-avail">Available: {0}</span>'.format(avail) if avail else ""

    if horizontal:
        return '''      <div class="row-card{cf}" data-price="{pnum}" data-beds="{beds}" data-baths="{baths}" data-featured="{featv}">
        <div class="row-photo">
          <div class="rc-carousel">
            {new}{feat}
            <button class="rc-btn rc-prev" aria-label="Previous photo">&#8249;</button>
            <div class="rc-track">{slides}</div>
            <button class="rc-btn rc-next" aria-label="Next photo">&#8250;</button>
          </div>
        </div>
        <div class="row-body">
          <div class="row-main">
            <span class="tag">{status}</span>
            <h3><a href="listing-{lid}.html">{t}</a></h3>
            <p class="row-addr">{addr}</p>
            <p class="row-specs">{beds} bed &middot; {baths} bath</p>
            <p class="row-hl">{hl}</p>
            <p class="row-meta">{avail_line}</p>
          </div>
          <div class="row-side">
            <p class="row-price">{price}</p>
            <a class="btn btn-primary" href="listing-{lid}.html">View Details</a>
          </div>
        </div>
      </div>'''.format(
            cf=feat_class, pnum=pnum, beds=beds, baths=baths, featv="yes" if is_featured(row) else "no",
            new=new_badge, feat=feat_ribbon, slides=slides_html, status=esc(row.get("status", "")),
            lid=lid, addr=addr, hl=highlights, avail_line=avail_line, price=price, t=t)
    # fallback: vertical card (used inside related/featured strips)
    return '''      <div class="card{cf}" data-price="{pnum}" data-beds="{beds}" data-baths="{baths}">
        <div class="card-carousel">
          {new}{feat}
          <button class="cc-btn cc-prev" aria-label="Previous photo">&#8249;</button>
          <div class="cc-track">{slides}</div>
          <button class="cc-btn cc-next" aria-label="Next photo">&#8250;</button>
        </div>
        <div class="card-body">
          <span class="tag">{status}</span>
          <h3>{t}</h3>
          <p class="card-meta">{beds} bed &middot; {baths} bath &middot; {price}<br>{addr}</p>
          <a class="btn btn-primary" href="listing-{lid}.html">View Details</a>
        </div>
      </div>'''.format(
            cf=feat_class, pnum=pnum, beds=beds, baths=baths, new=new_badge, feat=feat_ribbon,
            slides=slides_html, status=esc(row.get("status", "")), t=t, price=price, addr=addr, lid=lid)


def featured_strip(listings, heading):
    cards = "\n".join(listing_card(r, horizontal=False) for r in listings)
    return '''<section class="section" style="padding-top:24px;padding-bottom:24px;">
  <div class="container">
    <div class="featured-head">
      <h2 style="text-align:left;margin:0;">{heading}</h2>
      <div class="featured-nav">
        <button class="feat-btn feat-prev" aria-label="Scroll left">&#8249;</button>
        <button class="feat-btn feat-next" aria-label="Scroll right">&#8250;</button>
      </div>
    </div>
    <div class="scroll-row featured-row">
{cards}
    </div>
  </div>
</section>'''.format(heading=heading, cards=cards)


# ---------------- detail page ----------------
def detail_page(row, all_listings):
    lid = esc(row["id"])
    title = esc(row["title"])
    address = esc(row["address"])
    beds = esc(row.get("beds", ""))
    baths = esc(row.get("baths", ""))
    price = esc(row.get("price", ""))
    status = esc(row.get("status", ""))
    desc = esc(row.get("description", ""))
    avail = esc(row.get("available", ""))
    new_badge = '<span class="badge-new badge-detail">New</span>' if is_new(row) else ""
    feat_ribbon = '<span class="badge-featured badge-detail">Featured</span>' if is_featured(row) else ""

    feats = feature_list(row)
    feat_items = "\n".join("<li>{0}</li>".format(f) for f in feats) if feats else "<li>Details available on request</li>"

    slides = []
    for i, p in enumerate(photo_list(row)):
        slides.append('      <div class="slide"><img src="assets/photos/{0}" alt="{1} photo {2}"></div>'.format(esc(p), title, i + 1))
    slides_html = "\n".join(slides)

    related = [r for r in all_listings if listing_type(r) == listing_type(row) and r["id"] != row["id"]]
    related_html = "\n".join(listing_card(r, horizontal=False) for r in related)
    related_section = ""
    if related_html:
        related_section = '''<section class="section" style="padding-top:8px;">
  <div class="container">
    <div class="featured-head">
      <h2 style="text-align:left;margin:0;">More {type} Listings</h2>
      <div class="featured-nav">
        <button class="feat-btn feat-prev" aria-label="Scroll left">&#8249;</button>
        <button class="feat-btn feat-next" aria-label="Scroll right">&#8250;</button>
      </div>
    </div>
    <div class="scroll-row related-row">
{related}
    </div>
  </div>
</section>'''.format(type="Rental" if listing_type(row) == "rent" else "For-Sale", related=related_html)

    map_url = map_embed_url(row)

    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Bradley Homes &amp; Rentals</title>
<meta name="description" content="{title} in {address}. {price}.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
<link rel="icon" href="assets/logo.svg">
</head>
<body class="theme-{theme}">
{nav}
<section class="detail-hero">
  <div class="container">
    <h1 class="detail-title">{title}</h1>
    <p class="detail-sub">{address}</p>
  </div>
  <div class="carousel">
    <button class="car-btn car-prev" aria-label="Previous photo" onclick="carGo(-1)">&#8249;</button>
    <div class="carousel-viewport">
      <div class="carousel-track" id="track">
{slides}
      </div>
    </div>
    <button class="car-btn car-next" aria-label="Next photo" onclick="carGo(1)">&#8250;</button>
  </div>
  <div class="car-dots" id="dots"></div>
</section>
<section class="section" style="padding-top:8px;">
  <div class="detail-info">
    <span class="tag">{status}</span> {new} {feat}
    <div class="detail-specs">
      <div class="spec">{price}<span>Price</span></div>
      <div class="spec">{beds}<span>Bedrooms</span></div>
      <div class="spec">{baths}<span>Bathrooms</span></div>
      <div class="spec">{addr}<span>Location</span></div>
      <div class="spec">{avail}<span>Available</span></div>
    </div>
    <h3 style="margin:18px 0 8px;">Features</h3>
    <ul class="features-list">{feats}</ul>
    <div class="detail-desc-box">
      <p class="detail-desc">{desc}</p>
    </div>
    <h3 style="margin:22px 0 8px;">Location</h3>
    <div class="map-box">
      <iframe src="{mapurl}" title="Map of {title}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      <p class="map-note"><a href="https://www.google.com/maps/search/?api=1&query={mapq}" target="_blank" rel="noopener">Open in Google Maps</a></p>
    </div>
    <div class="email-box">
      <p>Interested in this home? Send Bill &amp; Brenda a message right here.</p>
      <form action="{formspree}" method="POST" onsubmit="this.querySelector('.send-btn').textContent='Sending...';">
        <input type="hidden" name="listing" value="{title} - {address}">
        <div class="field">
          <label for="i-name">Your name</label>
          <input id="i-name" type="text" name="name" placeholder="Full name" required>
        </div>
        <div class="field">
          <label for="i-email">Email</label>
          <input id="i-email" type="email" name="_replyto" placeholder="you@example.com" required>
        </div>
        <div class="field">
          <label for="i-msg">Message</label>
          <textarea id="i-msg" name="message" placeholder="I'd like to ask about this home..." required></textarea>
        </div>
        <button class="btn btn-block send-btn" type="submit">Send Message</button>
      </form>
      <p class="detail-call">Prefer to talk? Call Bill &amp; Brenda at <a href="tel:{tel}">{phone}</a>.</p>
    </div>
  </div>
</section>
{related}
{cta}
{footer}
{detail_js}
</body>
</html>'''.format(
        title=title, address=address, price=price, theme=detail_theme(row),
        nav=header(""), slides=slides_html, status=status, new=new_badge,
        feat=feat_ribbon, beds=beds, baths=baths, avail=avail, addr=address, feats=feat_items,
        desc=desc, mapurl=map_url, mapq=urllib.parse.quote(address + ", Evart, MI"),
        formspree=FORMSPREE, tel=PHONE_TEL, phone=PHONE_DISPLAY,
        related=related_section, cta=CONTACT_CTA, footer=FOOTER, detail_js=DETAIL_JS)


# ---------------- filterable grid page (horizontal rows in a bordered container) ----------------
def grid_page(title, lead, listings, theme, active=""):
    cards_html = "\n".join(listing_card(r, horizontal=True) for r in listings)
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Bradley Homes &amp; Rentals</title>
<meta name="description" content="{lead}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
<link rel="icon" href="assets/logo.svg">
</head>
<body class="theme-{theme}">
{nav}
<section class="section" style="padding-top:24px;">
  <div class="container">
    <h2>{title}</h2>
    <p class="lead">{lead}</p>
    <div class="filter-panel">
      <span class="filter-panel-title">Filter &amp; Sort</span>
      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">Sort</span>
          <button class="filter-pill is-active" data-sort="featured">Featured</button>
          <button class="filter-pill" data-sort="price-asc">Price: Low to High</button>
          <button class="filter-pill" data-sort="price-desc">Price: High to Low</button>
        </div>
        <div class="filter-group">
          <span class="filter-label">Beds</span>
          <button class="filter-pill is-active" data-beds="any">Any</button>
          <button class="filter-pill" data-beds="1">1+</button>
          <button class="filter-pill" data-beds="2">2+</button>
          <button class="filter-pill" data-beds="3">3+</button>
          <button class="filter-pill" data-beds="4">4+</button>
          <button class="filter-pill" data-beds="5">5+</button>
        </div>
        <div class="filter-group">
          <span class="filter-label">Baths</span>
          <button class="filter-pill is-active" data-baths="any">Any</button>
          <button class="filter-pill" data-baths="1">1+</button>
          <button class="filter-pill" data-baths="2">2+</button>
          <button class="filter-pill" data-baths="3">3+</button>
          <button class="filter-pill" data-baths="4">4+</button>
        </div>
      </div>
    </div>
    <div class="listing-container">
      <div class="row-cards" id="listings-grid">
{cards}
      </div>
      <p class="lead" id="no-results" style="display:none;margin-top:24px;">No listings match those filters.</p>
    </div>
  </div>
</section>
{cta}
{footer}
{grid_js}
{shared_js}
</body>
</html>'''.format(
        title=title, lead=lead, theme=theme, nav=header(active),
        cards=cards_html, cta=CONTACT_CTA, footer=FOOTER, grid_js=GRID_JS, shared_js=SHARED_JS)


# ---------------- home page ----------------
def home_page(all_listings):
    meet = '''
<section class="section meet">
  <div class="container meet-inner">
    <div class="meet-photo">
      <img src="assets/bill-brenda.svg" alt="Bill and Brenda Bradley">
    </div>
    <div class="meet-text">
      <h2>Meet Bill &amp; Brenda</h2>
      <p>When you rent or buy through Bradley Homes &amp; Rentals, you're not calling a call center. You're talking to Bill and Brenda &mdash; the folks who own the homes, live in this area, and have helped local families find places to live for years.</p>
      <p>They started this business the old-fashioned way: do right by people, keep your word, and take care of what's yours. That hasn't changed.</p>
      <a class="btn btn-primary" href="about.html">Our Story</a>
    </div>
  </div>
</section>'''

    why = '''
<section class="section why-rent">
  <div class="container">
    <h2>Why Rent From Us?</h2>
    <div class="why-grid">
      <div class="why-item">
        <span class="why-icon">&#127969;</span>
        <h3>Local &amp; Family-Owned</h3>
        <p>We live here, work here, and care about the people who rent from us. You're a neighbor, not a number.</p>
      </div>
      <div class="why-item">
        <span class="why-icon">&#128176;</span>
        <h3>We Buy Houses</h3>
        <p>Thinking of selling? Get a fair, no-pressure cash offer &mdash; no listings, no waiting.</p>
      </div>
      <div class="why-item">
        <span class="why-icon">&#128176;</span>
        <h3>Honest Pricing</h3>
        <p>Clear rent, no surprise fees. What we agree on is what you pay.</p>
      </div>
      <div class="why-item">
        <span class="why-icon">&#128241;</span>
        <h3>Real People, Real Answers</h3>
        <p>Call or text Bill &amp; Brenda directly. We'll help you find the right home.</p>
      </div>
    </div>
  </div>
</section>'''

    community = '''
<section class="community-strip">
  <div class="container">
    <p>Proud to call Evart and the surrounding Central Michigan communities home. We're invested in this town &mdash; not just the houses in it.</p>
  </div>
</section>'''

    testimonials = '''
<section class="section testimonials">
  <div class="container">
    <h2>What Our Tenants Say</h2>
    <div class="testi-grid">
      <blockquote class="testi">
        <p>"Bill had the furnace fixed the same day I called. You don't get that from a big company."</p>
        <cite>&mdash; Long-time tenant, Evart</cite>
      </blockquote>
      <blockquote class="testi">
        <p>"They treated us like family when we were looking for our first place. Made it easy."</p>
        <cite>&mdash; Renter, Hersey</cite>
      </blockquote>
      <blockquote class="testi">
        <p>"Straight shooters. What they say is what they do."</p>
        <cite>&mdash; Home buyer, Osceola County</cite>
      </blockquote>
    </div>
  </div>
</section>'''

    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bradley Homes &amp; Rentals</title>
<meta name="description" content="Bradley Homes &amp; Rentals - local family-owned homes for rent and for sale across Evart and surrounding Central Michigan communities. Bill &amp; Brenda Bradley.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
<link rel="icon" href="assets/logo.svg">
</head>
<body class="theme-home">
{nav}
<section class="hero">
  <div class="container">
    <h1>Find Your Next Home &mdash; From Neighbors You Know</h1>
    <p>Local, family-owned rentals and homes for sale across Evart and the surrounding Central Michigan communities. No corporate runaround &mdash; just a real place to call home.</p>
    <div class="actions">
      <a class="btn btn-light" href="tel:{tel}">{phone}</a>
      <a class="btn btn-outline-light" href="contact.html">Contact Bill &amp; Brenda</a>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <h2>How can we help?</h2>
    <p class="lead">Pick a path &mdash; we'll take you there.</p>
    <div class="cta-grid">
      <a class="cta-banner" href="rentals.html">
        <span class="cta-icon">&#127968;</span>
        <span class="cta-text"><h3>Find a Rental</h3><p>Browse homes available to rent.</p></span>
        <span class="cta-arrow">&#8594;</span>
      </a>
      <a class="cta-banner alt" href="sale.html">
        <span class="cta-icon">&#127968;</span>
        <span class="cta-text"><h3>Buy a Home</h3><p>See houses for sale near you.</p></span>
        <span class="cta-arrow">&#8594;</span>
      </a>
      <a class="cta-banner alt2" href="we-buy-houses.html">
        <span class="cta-icon">&#128176;</span>
        <span class="cta-text"><h3>We Buy Houses</h3><p>Get a fair cash offer on your home.</p></span>
        <span class="cta-arrow">&#8594;</span>
      </a>
    </div>
  </div>
</section>
{meet}
{why}
{community}
{featured}
{testimonials}
{cta}
{footer}
{shared_js}
</body>
</html>'''.format(
        nav=header(""), tel=PHONE_TEL, phone=PHONE_DISPLAY,
        meet=meet, why=why, community=community,
        featured=featured_strip(all_listings, "Featured Homes"),
        testimonials=testimonials, cta=CONTACT_CTA, footer=FOOTER, shared_js=SHARED_JS)


def main():
    listings = load_listings()
    rentals = [r for r in listings if listing_type(r) == "rent"]
    sales = [r for r in listings if listing_type(r) == "sale"]

    written = []
    for row in listings:
        fn = os.path.join(ROOT, "listing-{0}.html".format(row["id"]))
        with open(fn, "w", encoding="utf-8") as f:
            f.write(detail_page(row, listings))
        written.append(fn)

    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(home_page(listings))
    with open(os.path.join(ROOT, "rentals.html"), "w", encoding="utf-8") as f:
        f.write(grid_page("Homes for Rent",
                          "Homes available to rent across Evart and the surrounding Central Michigan communities.",
                          rentals, "rentals", "rentals.html"))
    with open(os.path.join(ROOT, "sale.html"), "w", encoding="utf-8") as f:
        f.write(grid_page("Homes for Sale",
                          "Houses for sale across Evart and the surrounding Central Michigan communities.",
                          sales, "sale", "sale.html"))

    print("Generated {0} detail pages + index.html + rentals.html + sale.html".format(len(written)))
    print("Rentals:", [r["id"] for r in rentals])
    print("Sales:", [s["id"] for s in sales])


if __name__ == "__main__":
    main()
