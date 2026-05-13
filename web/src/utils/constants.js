export const API_BASE = import.meta.env.VITE_API_URL || ''

export const DEFAULT_TOOLS = [
  { name: 'web_search', description: 'Search the web for current information, news, facts' },
  { name: 'fetch_url', description: 'Fetch content from a URL' },
  { name: 'analyze_image', description: 'Extract text from an image via URL or base64' },
]
