# Client-Side Search Integration Plan (Pagefind)

This document specifies the technical architecture, build pipeline, and client component implementation for full-text search across the WSABuilds documentation portal.

---

## 1. Architectural Choice: Pagefind

We select **Pagefind** as our static search engine based on these technical constraints:

- **Zero Server Infrastructure**: Operates entirely client-side on Cloudflare Pages.
- **Bandwidth Efficient**: Indexes are split into small chunks and loaded on-demand as the user types.
- **WebAssembly Engine**: High-performance querying executed locally in the browser.
- **Privacy First**: Zero search query logging or telemetry transmission.

---

## 2. Build Pipeline Integration

Pagefind executes as a post-build step in the static site generation lifecycle:

1. `npm run build`: Astro compiles static HTML files to `dist/`.
2. `npx pagefind --site dist`: Pagefind parses all HTML outputs in `dist/`, indexes `<article>` contents, and generates binary indexes inside `dist/pagefind/`.
3. Deployment step publishes `dist/` directly to Cloudflare Pages.

---

## 3. Client Component Specification

The client modal component (`SearchModal.astro`):
- Listens for global keyboard shortcut `Ctrl + K` or `Cmd + K`.
- Dynamically lazy-loads the `/pagefind/pagefind.js` script only when the search modal is opened to keep initial page bundle under 15 KB.
- Displays instant live results with highlighted snippets, title, and direct document link.
