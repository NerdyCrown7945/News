import fs from 'fs/promises'
import path from 'path'

import ArticleDetailClient from '../../../components/ArticleDetailClient'

export async function generateStaticParams() {
  try {
    const filePath = path.join(process.cwd(), 'public/data/feed.json')
    const raw = await fs.readFile(filePath, 'utf-8')
    const feed = JSON.parse(raw) as Array<{ id: string }>
    return feed.slice(0, 50).map((item) => ({ id: String(item.id) }))
  } catch {
    return []
  }
}

export default function Page({ params }: { params: { id: string } }) {
  return <ArticleDetailClient id={params.id} />
}
