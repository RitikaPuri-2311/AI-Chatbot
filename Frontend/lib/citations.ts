import type { Source } from '@/types'

/** Remove backend- or model-appended References/Sources blocks when rendering SourcePanel separately. */
export function stripEmbeddedCitations(content: string): string {
  const cleaned = content.trim()
  const refHeading = /\n{1,2}(\*\*)?(References|Sources):(\*\*)?/i
  const match = refHeading.exec(cleaned)
  if (match?.index != null) {
    return cleaned.slice(0, match.index).trim()
  }
  return cleaned
}

export interface GroupedSource {
  name: string
  pages: number[]
}

/** Group citation rows by document name with sorted unique pages. */
export function groupSourcesByDocument(sources: Source[]): GroupedSource[] {
  const byName = new Map<string, Set<number>>()

  for (const source of sources) {
    const name = source.source?.trim() || 'document'
    const page = source.page
    if (!byName.has(name)) {
      byName.set(name, new Set())
    }
    if (page > 0) {
      byName.get(name)!.add(page)
    }
  }

  return Array.from(byName.entries()).map(([name, pages]) => ({
    name,
    pages: Array.from(pages).sort((a, b) => a - b),
  }))
}

export function formatPageLabel(pages: number[]): string {
  if (pages.length === 0) return 'Page ?'
  if (pages.length === 1) return `Page ${pages[0]}`
  return `Pages ${pages.join(', ')}`
}
