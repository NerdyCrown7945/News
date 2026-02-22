import fs from 'fs/promises'
import path from 'path'
import Link from 'next/link'
import { notFound } from 'next/navigation'

type ArticleDetail = {
  id: string
  title: string
  source: string
  topic: 'ai' | 'scitech'
  published_at: string
  url: string
  one_liner: string
  summary_lines: string[]
  key_points: string[]
  related: Array<{ id: string; title: string; source: string; published_at: string }>
}

const feedPath = path.join(process.cwd(), 'public/data/feed.json')

async function getFeed() {
  const raw = await fs.readFile(feedPath, 'utf-8')
  return JSON.parse(raw) as Array<{ id: string }>
}

async function getArticle(id: string): Promise<ArticleDetail | null> {
  const filePath = path.join(process.cwd(), `public/data/articles/${id}.json`)
  try {
    const raw = await fs.readFile(filePath, 'utf-8')
    return JSON.parse(raw) as ArticleDetail
  } catch {
    return null
  }
}

export async function generateStaticParams() {
  const feed = await getFeed()
  return feed.map((item) => ({ id: String(item.id) }))
}

export default async function ArticleDetailPage({ params }: { params: { id: string } }) {
  const article = await getArticle(params.id)
  if (!article) notFound()

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      <Link href="/news" className="text-sm text-blue-600">← Back to list</Link>
      <h1 className="mt-3 text-3xl font-bold text-gray-900">{article.title}</h1>
      <p className="mt-2 text-sm text-gray-500">
        {article.source} · {new Date(article.published_at).toLocaleString()}
      </p>

      <section className="mt-6 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">One-liner</h2>
        <p className="mt-2 text-base text-gray-800">{article.one_liner}</p>
      </section>

      <section className="mt-4 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Summary</h2>
        <div className="mt-2 space-y-2 text-sm leading-6 text-gray-700">
          {article.summary_lines.map((line, idx) => (
            <p key={idx}>{line}</p>
          ))}
        </div>
      </section>

      <section className="mt-4 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Key points</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
          {article.key_points.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </section>

      <a className="mt-5 inline-block text-blue-600 underline" href={article.url} target="_blank" rel="noreferrer">
        원문 보기
      </a>

      {article.related.length > 0 && (
        <section className="mt-8 rounded-xl border bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">같은 클러스터 기사</h2>
          <div className="mt-3 space-y-2">
            {article.related.map((rel) => (
              <Link key={rel.id} href={`/news/${rel.id}`} className="block rounded border p-3 hover:bg-gray-50">
                <p className="text-sm font-medium text-gray-900">{rel.title}</p>
                <p className="text-xs text-gray-500">
                  {rel.source} · {new Date(rel.published_at).toLocaleString()}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
