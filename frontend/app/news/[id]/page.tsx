const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

async function getArticle(id: string) {
  const res = await fetch(`${API_BASE}/article/${id}`, { cache: 'no-store' })
  if (!res.ok) return null
  return res.json()
}

export default async function ArticleDetail({ params }: { params: { id: string } }) {
  const article = await getArticle(params.id)

  if (!article) {
    return <div className="p-6">Article not found.</div>
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <a href="/news" className="text-blue-600 text-sm">← Back</a>
      <h1 className="text-2xl font-bold mt-2">{article.title}</h1>
      <p className="text-sm text-gray-500 mt-1">{article.source_name} · {article.published_at ? new Date(article.published_at).toLocaleString() : 'No date'}</p>

      <section className="mt-6 bg-white border rounded p-4">
        <h2 className="font-semibold">Summary</h2>
        <p className="mt-2">{article.summary?.one_liner || '요약 없음'}</p>
        <ul className="mt-2 list-disc ml-6 text-sm text-gray-700">
          {(article.summary?.summary_lines || []).map((line: string, idx: number) => <li key={idx}>{line}</li>)}
        </ul>
      </section>

      <section className="mt-4 bg-white border rounded p-4">
        <h2 className="font-semibold">Original Snippet</h2>
        <p className="text-sm mt-2 whitespace-pre-wrap">{article.content_text || article.snippet || 'No content available.'}</p>
      </section>

      <a className="inline-block mt-6 text-blue-600" href={article.url} target="_blank">Read original article ↗</a>
    </div>
  )
}
