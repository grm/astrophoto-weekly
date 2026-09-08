import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const issues = defineCollection({
  loader: glob({
    pattern: '*.md',
    base: './content/issues',
    generateId: ({ entry }) => entry.replace(/\.md$/, ''),
  }),
  schema: z.object({
    number: z.number().int().positive(),
    date: z.coerce.date(),
    title: z.string(),
    description: z.string(),
    tags: z.array(z.string()).optional().default([]),
    featured: z.boolean().optional().default(false),
  }),
});

export const collections = { issues };
