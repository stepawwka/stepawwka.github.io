#!/usr/bin/env python3
"""Генерирует index.html и страницы проектов из projects.json.
Запуск: python3 build.py"""
import json, re, os, html
from urllib.parse import quote, urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, "projects.json"), encoding="utf-8"))
site, cats, projects = data["site"], data["categories"], data["projects"]
cat_by_id = {c["id"]: c for c in cats}
e = lambda s: html.escape(s or "", quote=True)

KANA = "ビデオ編集"
FONTS = "\n".join(
    f'<link rel="preload" href="{{base}}assets/fonts/{f}" as="font" type="font/woff2" crossorigin>'
    for f in ("anton-latin.woff2", "sofia-latin-900.woff2", "sofia-cyrillic-900.woff2", "yuji-kana.woff2"))
FAVICON = ("data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#060709"/>'
    '<text x="32" y="44" font-family="Impact,Arial Narrow,sans-serif" font-size="34" fill="#F7F8FA" text-anchor="middle">SK</text>'
    '<rect x="8" y="34" width="48" height="6" fill="#E10E0E"/></svg>'))


def embed(url):
    """Ссылка на ролик -> src для iframe (или None)."""
    if not url:
        return None
    url = url.strip()
    m = re.search(r'src=["\']([^"\']+)', url)  # вставили целый <iframe> — берём из него src
    if m:
        url = m.group(1)
    u = urlparse(url)
    host = u.netloc.lower().replace("www.", "").replace("m.", "")
    if host == "youtu.be":
        vid = u.path.strip("/")
    elif "youtube.com" in host:
        vid = parse_qs(u.query).get("v", [""])[0] or u.path.rstrip("/").split("/")[-1]
    else:
        vid = None
    if vid:
        return f"https://www.youtube-nocookie.com/embed/{vid}?rel=0&modestbranding=1"
    if "vimeo.com" in host:
        m = re.search(r"(\d+)", u.path)
        return m and f"https://player.vimeo.com/video/{m.group(1)}?dnt=1"
    if "vk.com" in host or "vkvideo.ru" in host:
        m = re.search(r"video(-?\d+)_(\d+)", url)
        return m and f"https://vk.com/video_ext.php?oid={m.group(1)}&id={m.group(2)}&hd=2"
    if "rutube.ru" in host:
        m = re.search(r"/video/([0-9a-f]{32})", u.path)
        return m and f"https://rutube.ru/play/embed/{m.group(1)}"
    if "kinescope" in host:  # kinescope.io/ID, kinescope.io/embed/ID, kinescope.io/watch/ID
        parts = [x for x in u.path.split("/") if x and x not in ("embed", "watch", "w")]
        return parts and f"https://kinescope.io/embed/{parts[-1]}?title=false&dnt=1"
    return None


ALLOW = "autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer; clipboard-write; screen-wake-lock"
LIVE_JS = """<script>
(function () {
  if (!window.matchMedia || !matchMedia('(hover: none)').matches || !('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { e.target.classList.toggle('live', e.isIntersecting); });
  }, { rootMargin: '-46% 0px -46% 0px' });
  document.querySelectorAll('.card.has-cover, .poster, .about-photo').forEach(function (el) { io.observe(el); });
})();
</script>"""
ABOUT_JS = """<script>
(function () {
  document.documentElement.classList.add('js');
  var box = document.getElementById('about'), panel = box.querySelector('.about-panel'), last = null;
  function open(e) {
    if (e) e.preventDefault();
    last = document.activeElement; box.classList.add('open'); document.body.classList.add('noscroll');
    history.replaceState(null, '', '#about'); setTimeout(function () { panel.focus(); }, 50);
  }
  function close(e) {
    if (e) e.preventDefault();
    box.classList.remove('open'); document.body.classList.remove('noscroll');
    history.replaceState(null, '', location.pathname + location.search);
    if (last) last.focus();
  }
  document.querySelectorAll('[data-about-open]').forEach(function (a) { a.addEventListener('click', open); });
  box.querySelectorAll('[data-about-close]').forEach(function (a) { a.addEventListener('click', close); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && box.classList.contains('open')) close(e); });
  if (location.hash === '#about') open();
})();
</script>"""
PLAYER_JS = """<script>
document.querySelectorAll('.player[data-src] .poster').forEach(function (b) {
  b.addEventListener('click', function () {
    var p = b.parentElement, f = document.createElement('iframe');
    f.src = p.dataset.src; f.title = p.dataset.title; f.allow = '%s';
    f.allowFullscreen = true; f.referrerPolicy = 'strict-origin-when-cross-origin';
    p.replaceChildren(f); f.focus();
  });
});
</script>""" % ALLOW


def head(title, desc, base, og_url=""):
    og_img = (site.get("url") or "").rstrip("/") + "/assets/img/og.jpg" if site.get("url") else base + "assets/img/og.jpg"
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(og_img)}">
<meta name="theme-color" content="#060709">
<link rel="icon" href="{FAVICON}">
{FONTS.replace("{base}", base)}
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body>"""


def header(base, home=True):
    pre = "" if home else base
    links = "\n".join(
        f'<a href="{pre}#{c["id"]}"><span class="l">{e(c["title"])}</span><span class="s">{e(c["short"])}</span></a>'
        for c in cats)
    return f"""<header class="wrap top">
<a class="mark" href="{base}" aria-label="{e(site['name'])} — на главную">SK</a>
<nav class="nav" aria-label="Разделы">
{links}
<a href="#about" data-about-open><span class="l">Обо мне</span><span class="s">Обо мне</span></a>
<a href="{pre}#contact"><span class="l">Контакты</span><span class="s">Контакты</span></a>
</nav>
<a class="btn small" href="https://t.me/{e(site['telegram'])}" target="_blank" rel="noopener">Telegram ↗</a>
</header>"""


def contacts_buttons():
    b = f'<a class="btn fill" href="https://t.me/{e(site["telegram"])}" target="_blank" rel="noopener">Telegram @{e(site["telegram"]).upper()}</a>'
    if site.get("email"):
        b += f'\n<a class="btn" href="mailto:{e(site["email"])}">{e(site["email"]).upper()}</a>'
    return b


def footer(base=""):
    return f"""<footer id="contact" class="foot">
<div class="foot-h"><h2>Написать</h2><div class="tag" aria-hidden="true"><span class="tag-k" lang="ja"><span>連</span><span>絡</span></span></div></div>
<div class="btns">
{contacts_buttons()}
</div>
</footer>
{about_panel(base)}"""


def about_panel(base):
    a = site.get("about", {})
    if a.get("photo"):
        photo = f'<img src="{base}{e(asset(a["photo"]))}" alt="{e(site["name"])}" loading="lazy" decoding="async">'
        if a.get("photo_hover"):
            photo += f'<img class="alt" src="{base}{e(asset(a["photo_hover"]))}" alt="" loading="lazy" decoding="async">'
    else:
        photo = '<span class="ph" aria-hidden="true"><span class="ph-k">' + "".join(f"<span>{ch}</span>" for ch in KANA) + '</span><span class="ph-m">SK</span></span>'
    paras = "".join(f"<p>{e(t)}</p>" for t in a.get("text", []))
    lead = e(a.get("lead", ""))
    hl = a.get("lead_accent")
    if hl and e(hl) in lead:
        lead = lead.replace(e(hl), f'<b>{e(hl)}</b>', 1)
    chips = "".join(
        f'<li class="{e(c.get("kind", ""))}">{e(c["text"])}</li>' for c in a.get("chips", []))
    return f"""<div id="about" class="about" role="dialog" aria-modal="true" aria-labelledby="about-title">
<a class="about-bg" href="#" data-about-close aria-label="Закрыть"></a>
<aside class="about-panel" tabindex="-1">
<div class="about-top"><span>Обо мне</span><a class="about-x" href="#" data-about-close aria-label="Закрыть">✕</a></div>
<div class="about-photo"><i></i><i></i><i></i><i></i><div class="about-photo-in">{photo}</div></div>
<h2 id="about-title" class="sr">Обо мне — {e(site['name'])}</h2>
<p class="about-lead">{lead}</p>
{paras}
{f'<ul class="about-chips">{chips}</ul>' if chips else ''}
<div class="about-btns">{contacts_buttons()}</div>
</aside>
</div>
{ABOUT_JS}
{LIVE_JS}"""


def asset(path):
    """Путь к картинке с меткой версии, чтобы после замены файла браузер не показывал старый из кэша."""
    import hashlib
    try:
        h = hashlib.md5(open(os.path.join(ROOT, path), "rb").read()).hexdigest()[:8]
        return f"{path}?v={h}"
    except OSError:
        return path


def card(p, base):
    longest = max(len(x) for x in p["card"].split("\n"))
    tone = " red" if (not p.get("cover") and p.get("tone") == "red") else ""
    alt = (f'<img class="alt" src="{base}{e(asset(p["cover_hover"]))}" alt="" loading="lazy" decoding="async">'
           if p.get("cover_hover") else "")
    bg = (f'<img src="{base}{e(asset(p["cover"]))}" alt="" loading="lazy" decoding="async">{alt}<span class="shade" aria-hidden="true"></span>'
          if p.get("cover") else "")
    pos = f" at-{p['text_pos']}" if p.get("text_pos") in ("top", "bottom", "left") else ""
    return f"""<a class="card{tone}{' has-cover' if p.get('cover') else ''}{pos}" href="{base}work/{p['slug']}/">
{bg}<span class="t{" long" if longest > 14 else ""}{" one" if (pos and "\n" not in p["card"] and len(p["card"]) > 16) else ""}" aria-hidden="true">{e(p["card"])}</span>
<span class="sr">{e(p['title'])}</span>
<span class="line" aria-hidden="true"></span>
</a>"""


def build_index():
    base = ""
    secs = []
    for c in cats:
        items = [p for p in projects if p["category"] == c["id"]]
        if not items:
            continue
        cards = "\n".join(card(p, base) for p in items)
        secs.append(f"""<section id="{c['id']}" class="wrap sec">
<div class="sec-head"><span class="num" aria-hidden="true">{c['num']}</span><h2>{e(c['title'])}</h2></div>
<div class="grid">
{cards}
</div>
</section>""")
    kana = "".join(f"<span>{ch}</span>" for ch in KANA)
    out = head(f"{site['name']} — {site['role'].lower()}",
               f"{site['name']}, {site['role'].lower()}. Реклама и имиджевые ролики, музыкальные видео, YouTube.", base)
    out += f"""
{header(base)}
<main>
<section class="hero" aria-label="Обложка">
<div class="name">
<h1>Stepan<br>Korovkin</h1>
<div class="tag" aria-hidden="true"><span class="tag-k" lang="ja">{kana}</span></div>
</div>
<div class="bbox"><i></i><i></i><i></i><i></i><i></i><i></i><p class="role">Режиссер монтажа</p></div>
</section>
{chr(10).join(secs)}
</main>
{footer(base)}
</body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)


def build_project(i, p):
    base = "../../"
    c = cat_by_id[p["category"]]
    src = embed(p.get("video"))
    player_attrs = ""
    if src:
        # своя обложка с кнопкой Play; плеер грузится только после клика
        play_src = src + ("&" if "?" in src else "?") + "autoplay=1"
        player_attrs = f' data-src="{e(play_src)}" data-title="{e(p["title"])}"'
        poster = p.get("poster") or p.get("cover")
        if poster:
            inner = f'<img src="{base}{e(asset(poster))}" alt="" decoding="async">'
            if p.get("cover_hover") and not p.get("poster"):
                inner += f'<img class="alt" src="{base}{e(asset(p["cover_hover"]))}" alt="" decoding="async">'
            tone = ""
        else:
            inner = f'<b aria-hidden="true">{e(p["card"])}</b>'
            tone = " red" if p.get("tone") == "red" else ""
        player = (f'<button class="poster{tone}" type="button" aria-label="Смотреть: {e(p["title"])}">{inner}'
                  '<span class="play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l11-6.5z"/></svg></span></button>'
                  f'<noscript><iframe src="{e(src)}" title="{e(p["title"])}" allow="{ALLOW}" allowfullscreen></iframe></noscript>')
    elif p.get("video"):
        bg = f'<img src="{base}{e(p["cover"])}" alt="">' if p.get("cover") else ""
        player = f'{bg}<div class="soon"><b>{e(p["card"])}</b><a class="btn fill" href="{e(p["video"])}" target="_blank" rel="noopener">Смотреть ↗</a></div>'
    else:
        bg = f'<img src="{base}{e(p["cover"])}" alt="">' if p.get("cover") else ""
        title = "" if p.get("cover") else f'<b>{e(p["card"])}</b>'
        player = f'{bg}<div class="soon">{title}<span>Видео скоро</span></div>'
    facts = [(k, p.get(f)) for k, f in (("Клиент", "client"), ("Роль", "role"), ("Год", "year")) if p.get(f)]
    facts_html = "".join(f"<div><span>{k}</span><strong>{e(v)}</strong></div>" for k, v in facts)
    if p.get("text"):
        facts_html += f"<p>{e(p['text'])}</p>"
    prev_p, next_p = projects[i - 1], projects[(i + 1) % len(projects)]
    out = head(f"{p['title']} — {site['name']}", f"{p['title']}. {c['title']}. Монтаж — {site['name']}.", base)
    out += f"""
{header(base, home=False)}
<main>
<section class="wrap p-head">
<p class="cat">{c['num']} · {e(c['title'])}</p>
<h1>{e(p['title'])}</h1>
</section>
<div class="wrap"><div class="player"{player_attrs}>{player}</div></div>
<section class="wrap">
{f'<div class="facts">{facts_html}</div>' if facts_html else ''}
<nav class="pn" aria-label="Соседние проекты">
<a href="{base}work/{prev_p['slug']}/"><span>← Предыдущий</span><strong>{e(prev_p['title'])}</strong></a>
<a class="next" href="{base}work/{next_p['slug']}/"><span>Следующий →</span><strong>{e(next_p['title'])}</strong></a>
</nav>
</section>
</main>
{footer(base)}
{PLAYER_JS if src else ""}
</body>
</html>
"""
    d = os.path.join(ROOT, "work", p["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(out)


build_index()
for i, p in enumerate(projects):
    build_project(i, p)
print(f"OK: index + {len(projects)} страниц проектов")
