'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

type ArticleDetail = {
  id: string
  title: string
  title_ko?: string
  url: string
  source: string
  published_at: string
  summary_lines_ko: string[]
  key_points_ko: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

export default function ArticleDetailClient({ id }: { id: string }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/article/${id}`)
      .then((res) => res.json())
      .then((data: ArticleDetail) => setArticle(data))
      .catch(() => setArticle(null))
  }, [id])

  if (!article) return <div className="mx-auto max-w-4xl px-4 py-8">불러오는 중...</div>

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 md:py-10">
      <Link href="/news" className="text-sm text-blue-600">← 목록으로</Link>
      <h1 className="mt-3 text-3xl font-bold leading-[1.4] text-gray-900">{article.title_ko || article.title}</h1>
      <p className="mt-2 text-sm text-gray-500">{article.source} · {new Date(article.published_at).toLocaleString()}</p>
      <section className="mt-8 rounded-2xl border bg-white p-5 shadow-sm md:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">요약</h2>
        <div className="mt-3 space-y-3 text-sm leading-7 text-gray-700">
          {article.summary_lines_ko.map((line, idx) => <p key={idx}>{line}</p>)}
        </div>
      </section>
      <section className="mt-4 rounded-2xl border bg-white p-5 shadow-sm md:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">핵심 포인트</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-7 text-gray-700">
          {article.key_points_ko.map((point, idx) => <li key={idx}>{point}</li>)}
        </ul>
      </section>
      <a className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2 text-white" href={article.url} target="_blank" rel="noreferrer">원문 링크 열기</a>
    </div>
  )
}
