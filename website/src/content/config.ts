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

export const collections = {
  docs: docsCollection
};
