# altantutar.me

Plain HTML. No build step, no dependencies, no JavaScript.

```
index.html         home — photo, bio, social icons. Ends there.
blog.html          writing published elsewhere
research.html      papers
podcasts.html      podcast and video appearances
press.html         coverage
sports.html        sports and interests
style.css          all styling, shared by every page
portrait.jpg       your photo (640×640)
og.jpg             1200×630 sharing card
favicon.svg        monogram tab icon
thumbs/            video and paper thumbnails, stored locally
newsreader.woff2   the typeface, self-hosted
```

Styling lives only in `style.css`, so a colour or spacing change applies to
all six pages at once. The nav, though, is copied into each page — **if you
add or rename a tab, update it in all six files.** That's the one real cost of
having no build step.

## Links — what's verified and what isn't

**Verified working:** GitHub (`altanapps` — 33 followers, active; the `altantutar`
account is stale), all three YouTube interviews, CoinDesk, The Block ×2, NEAR
blog, Coinpaper, Block by Block.

**Needs your eye:**

- **LinkedIn** — two profiles exist under your name:
  `linkedin.com/in/altan-tutar-494b61122` (used on the page) and
  `ae.linkedin.com/in/tutaraltan`. Pick one, delete or redirect the other.
- **X** — set to `x.com/mraltantutar`, confirmed via two indexed pages. X returns
  404 to logged-out requests, so it can't be checked automatically. Open it once.
- **YouTube, Instagram, TikTok** — not found. Dotted until you fill them in.
- **Research** — the two papers are still empty rows.
- **Writing** — three titles with no URLs found anywhere.

## Editing

Open `index.html` in any text editor.

- **Bullets** — the `<ul class="bullets">` block. Add, cut or reorder `<li>` items.
- **Writing / Research / Press** — each is a `<ul class="entries">` block, with a
  comment above it explaining what goes in. Copy an `<li>` to add a row, delete
  one to remove it.
- **Links** — the `<ul class="links">` block. Five of the six are guesses; see the
  comment above them.

Unfilled links (`href="#"`) render grey with a dotted underline, so a
placeholder can't ship by accident. Give one a real URL and it styles itself
like every other link.
- **Photo** — replace `portrait.jpg`. Square works best.
- **Colours and sizes** — the `<style>` block at the top, starting with `:root`.

Double-click the file to preview it in a browser. No server needed.

## Deploying

Any static host serves this as-is, with no build step and no configuration.
Railway, Vercel, Netlify, GitHub Pages and Cloudflare Pages all work.

After the domain is live, update the two `og:url` / `og:image` lines in the
`<head>` so link previews point at the real address.
