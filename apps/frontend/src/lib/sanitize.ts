/**
 * HTML sanitization for student-facing content_body render.
 *
 * Allow-list kept consistent with RichTextEditor.vue (the admin editor that
 * produces this HTML) — anything the editor can't produce shouldn't survive
 * sanitization on the read side either.
 *
 * All links are forced to open in a new tab with rel="noopener noreferrer"
 * regardless of what the stored HTML says, closing off tabnabbing / referrer
 * leaks even if a malicious payload somehow made it into content_body.
 */
import DOMPurify from 'dompurify';

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

export function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return '';
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'h2', 'h3', 'ul', 'ol', 'li', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
  });
}
