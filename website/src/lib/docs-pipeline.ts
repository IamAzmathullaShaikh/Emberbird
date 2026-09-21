import { getCollection, type CollectionEntry } from 'astro:content';

export interface CategoryGroup {
  id: string;
  title: string;
  order: number;
  articles: Array<{
    slug: string;
    title: string;
    description: string;
  }>;
}

const CATEGORY_DEFINITIONS: Record<string, { title: string; order: number }> = {
  'getting-started': { title: 'Getting Started', order: 1 },
  'configuration': { title: 'Configuration & Root', order: 2 },
  'troubleshooting': { title: 'Troubleshooting & Errors', order: 3 },
  'community': { title: 'Community & Governance', order: 4 }
};

export async function getOrderedDocCategories(): Promise<CategoryGroup[]> {
  const allDocs = await getCollection('docs');

  const groups: Record<string, CategoryGroup> = {};

  for (const [catKey, meta] of Object.entries(CATEGORY_DEFINITIONS)) {
    groups[catKey] = {
      id: catKey,
      title: meta.title,
      order: meta.order,
      articles: []
    };
  }

  for (const doc of allDocs) {
    const category = doc.data.category || 'getting-started';
    if (!groups[category]) {
      groups[category] = {
        id: category,
        title: category.replace('-', ' ').toUpperCase(),
        order: 10,
        articles: []
      };
    }
    groups[category].articles.push({
      // Content Layer entries expose `id` (path relative to the loader base);
      // it is the same URL segment the legacy `slug` used to carry.
      slug: doc.id,
      title: doc.data.title,
      description: doc.data.description
    });
  }

  return Object.values(groups)
    .filter((g) => g.articles.length > 0)
    .sort((a, b) => a.order - b.order);
}

export async function getAdjacentArticles(currentSlug: string): Promise<{
  prev: { slug: string; title: string } | null;
  next: { slug: string; title: string } | null;
}> {
  const allDocs = await getCollection('docs');
  const sorted = allDocs.sort((a, b) => (a.data.order || 0) - (b.data.order || 0));

  const index = sorted.findIndex((doc) => doc.id === currentSlug);
  if (index === -1) {
    return { prev: null, next: null };
  }

  const prevDoc = index > 0 ? sorted[index - 1] : null;
  const nextDoc = index < sorted.length - 1 ? sorted[index + 1] : null;

  return {
    prev: prevDoc ? { slug: prevDoc.id, title: prevDoc.data.title } : null,
    next: nextDoc ? { slug: nextDoc.id, title: nextDoc.data.title } : null
  };
}
