# Emberbird Web Portal & Documentation Platform

The `website/` directory contains the official web platform for **Emberbird**, built with **Astro**, **Tailwind CSS**, and **Pagefind**. It delivers release discovery, interactive troubleshooting, an application compatibility database, and transparency metrics.

---

## 1. Purpose & Features

- **Release Discovery Portal (`/downloads`)**: Dynamic GitHub Releases parsing, architecture-specific package filtering (`x64`, `arm64`), file size formatting, and copyable SHA-256 checksum modals.
- **Interactive Diagnostic Wizard (`/troubleshoot/wizard`)**: Step-by-step diagnostic decision tree supporting 6 problem categories, 8 canonical WSA error codes, and copyable PowerShell remediation commands.
- **Application Compatibility Directory (`/compatibility`)**: Community-tested compatibility database tracking banking, enterprise, streaming, and gaming applications with Play Integrity indicators.
- **Documentation Hub (`/docs/[...slug]`)**: Versioned documentation hub powered by Astro content collections, automated sidebar navigation, and local search.
- **Privacy-First Analytics Dashboard (`/analytics`)**: Public transparency dashboard displaying aggregated platform metrics with Zero-PII guarantees.
- **Client-Side Search**: Instant full-text static search powered by Pagefind (`Ctrl+K` modal).

---

## 2. Directory Architecture

```text
website/
├── docs/                     # Technical specifications (e.g. SEARCH_INTEGRATION.md)
├── public/                   # Static assets, Cloudflare headers (_headers, _routes.json)
├── scripts/                  # Prebuild content synchronization scripts
│   ├── import-docs.mjs       # Imports repository root docs/ into content collections
│   ├── import-compatibility.mjs # Imports compatibility/data/ into content collections
│   └── import-analytics.mjs  # Imports services/analytics/metrics.json into content collections
├── src/
│   ├── components/           # Reusable Astro and React UI components
│   ├── content/              # Astro content collections (docs, compatibility, analytics)
│   ├── layouts/              # Master layout (Layout.astro) with navigation and SEO
│   ├── lib/                  # Business logic (release service, compatibility, wizard engine, env)
│   ├── pages/                # Route endpoints (index, downloads, compatibility, wizard, analytics)
│   └── styles/               # Tailwind CSS entrypoint (global.css)
├── tests/                    # 22 Node unit test suites (node --test)
├── astro.config.mjs          # Astro build configuration
└── package.json              # Scripts and dependencies
```

---

## 3. Local Development Setup

### Prerequisites
- **Node.js**: Version 20.0 or higher.
- **npm**: Version 9.0 or higher.

### Installation
```powershell
cd website
npm install
```

---

## 4. Development & Build Commands

> **Important**: You must run `npm run prebuild` before launching the development server or building the site. `prebuild` synchronizes repository markdown documentation, compatibility records, and analytics metrics into the Astro content collection directory.

```powershell
# 1. Synchronize documentation and data into content collections (MANDATORY)
npm run prebuild

# 2. Start local development server (localhost:4321)
npm run dev

# 3. Build production static site and generate Pagefind search index
npm run build

# 4. Preview production build locally
npm run preview
```

---

## 5. Testing & Quality Commands

```powershell
# Run all 22 unit test suites (parser, environment, compatibility, wizard, analytics)
npm test

# Run TypeScript typechecker
npm run typecheck
```

---

## 6. Environment Configuration

Copy `.env.example` to `.env` for local development:
```ini
SITE_URL=http://localhost:4321
PUBLIC_GITHUB_REPO=IamAzmathullaShaikh/Emberbird
PUBLIC_GITHUB_REPO_URL=https://github.com/IamAzmathullaShaikh/Emberbird
PUBLIC_RELEASES_URL=https://github.com/IamAzmathullaShaikh/Emberbird/releases
```

Missing environment variables trigger explicit startup exceptions in `src/lib/env.ts` to ensure fail-fast configuration governance.

---

## 7. CI/CD Deployment

Governed by `.github/workflows/website-deploy.yml`:
- Validates dependencies and executes npm security audit.
- Executes unit test suites (`npm test`) and typechecks (`npm run typecheck`).
- Runs `npm run prebuild` and `npm run build`.
- Deploys static output (`dist/`) directly to **Cloudflare Pages**.
