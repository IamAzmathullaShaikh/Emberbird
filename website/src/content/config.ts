import { defineCollection, z } from 'astro:content';

const docsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum(['getting-started', 'configuration', 'troubleshooting', 'community']),
    order: z.number().default(0)
  })
});

const compatibilityCollection = defineCollection({
  type: 'data',
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
