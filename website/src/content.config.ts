import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Task 5.2 (single source of truth): the compatibility collection loads the
// authoritative repository records directly from compatibility/data/ so the
// Compatibility Hub can never drift from the validated source of record.

// Content Layer loader (the legacy `type: 'content'` collection API is gone in
// Astro 6+). The prebuild importer writes the .md mirror into src/content/docs/,
// so the entry id remains the path relative to that directory — URLs are
// unchanged.
const docsCollection = defineCollection({
  loader: glob({
    pattern: '**/*.md',
    base: new URL('./content/docs', import.meta.url)
  }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum(['getting-started', 'configuration', 'troubleshooting', 'community']),
    order: z.number().default(0)
  })
});

const compatibilityCollection = defineCollection({
  loader: glob({
    pattern: '**/*.json',
    base: new URL('../../compatibility/data', import.meta.url)
  }),
  schema: z.object({
    app_name: z.string(),
    package_id: z.string(),
    category: z.string(),
    compatibility_status: z.enum(['Working', 'Workaround Required', 'Broken']),
    play_integrity_required: z.boolean(),
    tested_wsa_version: z.string(),
    tested_root_flavor: z.string(),
    last_tested_date: z.string().optional(),
    workaround_steps: z.array(z.string()).default([]),
    known_issues: z.string().default('None'),
    verification_status: z.enum(['verified', 'unverified', 'community_submitted']).default('unverified')
  })
});

export const collections = {
  docs: docsCollection,
  compatibility: compatibilityCollection
};
