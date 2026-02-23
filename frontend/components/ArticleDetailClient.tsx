'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

type ArticleDetail = {
  id: string
  title: string
  title_ko?: string
  url: string
  source?: string
  published_at?: string
  summary_lines_ko: string[]
  key_points_ko: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || ''

const normalizeStaticArticle = (row: Record<string, unknown>): ArticleDetail => ({
  id: String(row.id ?? ''),
  title: String(row.title ?? ''),
  title_ko: typeof row.title_ko === 'string' ? row.title_ko : undefined,
  url: String(row.url ?? '#'),
  source: typeof row.source === 'string' ? row.source : 'Static seed',
  published_at: typeof row.published_at === 'string' ? row.published_at : undefined,
  summary_lines_ko: Array.isArray(row.summary_lines_ko)
    ? (row.summary_lines_ko as string[])
    : Array.isArray(row.summary_lines)
      ? (row.summary_lines as string[])
      : [],
  key_points_ko: Array.isArray(row.key_points_ko)
    ? (row.key_points_ko as string[])
    : Array.isArray(row.key_points)
      ? (row.key_points as string[])
      : [],
})

export default function ArticleDetailClient({ id }: { id: string }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [usingStaticFallback, setUsingStaticFallback] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const staticRes = await fetch(`${BASE_PATH}/data/articles/${id}.json`, { cache: 'no-store' })
        if (staticRes.ok) {
          const staticData = (await staticRes.json()) as Record<string, unknown>
          setArticle(normalizeStaticArticle(staticData))
          setUsingStaticFallback(true)
          setNotice('현재는 정적 데이터(샘플/캐시)를 표시 중입니다.')
          return
        }
        throw new Error('static article missing')
      } catch {
        try {
          const apiRes = await fetch(`${API_BASE}/article/${id}`)
          if (!apiRes.ok) throw new Error('api article fetch failed')
          const apiData = (await apiRes.json()) as ArticleDetail
          setArticle(apiData)
          setUsingStaticFallback(false)
          setNotice('')
        } catch {
          setArticle(null)
          setNotice('기사 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
        }
      }
    }

    load()
  }, [id])

  if (!article) {
    return <div className="mx-auto max-w-4xl px-4 py-8 text-sm text-gray-600">{notice || '불러오는 중...'}</div>
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 md:py-10">
      <Link href="/news" className="text-sm text-blue-600">← 목록으로</Link>
      <h1 className="mt-3 text-3xl font-bold leading-[1.4] text-gray-900">{article.title_ko || article.title}</h1>
      <p className="mt-2 text-sm text-gray-500">
        {article.source || 'Unknown source'}
        {article.published_at ? ` · ${new Date(article.published_at).toLocaleString()}` : ''}
      </p>
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

      {usingStaticFallback && (
        <div className="mt-6 inline-flex rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700">
          현재는 정적 데이터(샘플/캐시)를 표시 중
        </div>
      )}
    </div>
  )
}
