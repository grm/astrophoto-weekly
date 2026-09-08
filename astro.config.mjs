import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';

const siteConfig = JSON.parse(
  readFileSync(new URL('./data/site.json', import.meta.url), 'utf8'),
);
const publicUrl = new URL(siteConfig.site_url);
const base = publicUrl.pathname === '/' ? undefined : publicUrl.pathname.replace(/\/$/, '');

export default defineConfig({
  site: publicUrl.origin,
  base,
  output: 'static',
  trailingSlash: 'always',
});
