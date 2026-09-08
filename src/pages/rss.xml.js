import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import siteConfig from '../../data/site.json';

export async function GET(context) {
  const issues = (await getCollection('issues')).sort((a, b) => b.data.number - a.data.number);
  const baseSite = new URL(import.meta.env.BASE_URL, context.site);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: baseSite,
    items: issues.map((issue) => ({
      title: issue.data.title,
      description: issue.data.description,
      pubDate: issue.data.date,
      link: `issues/${issue.id}/`,
    })),
  });
}
