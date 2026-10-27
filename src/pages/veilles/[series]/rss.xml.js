import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import config from '../../../../data/specialists/series.json';

export function getStaticPaths() {
  return Object.entries(config).map(([series, publication]) => ({ params: { series }, props: { publication } }));
}

export async function GET(context) {
  const { publication } = context.props;
  const issues = (await getCollection('specialists', ({ data }) => data.series === context.params.series)).sort((a, b) => b.data.number - a.data.number);
  return rss({
    title: publication.title,
    description: publication.description,
    site: new URL(import.meta.env.BASE_URL, context.site),
    items: issues.map((issue) => ({ title: issue.data.title, description: issue.data.description, pubDate: issue.data.date, link: `veilles/${issue.id}/` })),
  });
}
