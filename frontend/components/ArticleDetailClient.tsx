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

const API_BASE_ENV = process.env.NEXT_PUBLIC_API_BASE
const API_BASE = API_BASE_ENV || 'http://127.0.0.1:8000'
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || ''

const normalizeArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

const normalizeArticle = (value: Partial<ArticleDetail> & { id: string; title: string; url: string }): ArticleDetail => ({
  id: value.id,
  title: value.title,
  title_ko: value.title_ko,
  url: value.url,
  source: value.source,
  published_at: value.published_at,
  summary_lines_ko: normalizeArray(value.summary_lines_ko),
  key_points_ko: normalizeArray(value.key_points_ko),
})

export default function ArticleDetailClient({ id }: { id: string }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [fallbackActive, setFallbackActive] = useState(false)
  const [canUseApi, setCanUseApi] = useState(false)

  useEffect(() => {
    const host = window.location.hostname
    const isLocalhost = host === '127.0.0.1' || host === 'localhost'
    setCanUseApi(isLocalhost || Boolean(API_BASE_ENV))
  }, [])

  useEffect(() => {
    const loadArticle = async () => {
      try {
        if (!canUseApi) {
          throw new Error('API is disabled in GitHub Pages mode')
        }

        const res = await fetch(`${API_BASE}/article/${id}`, { cache: 'no-store' })
        if (!res.ok) {
          throw new Error(`API request failed with status ${res.status}`)
        }

        const data = (await res.json()) as ArticleDetail
        setArticle(normalizeArticle(data))
        setFallbackActive(false)
        return
      } catch {
        try {
          const fallbackRes = await fetch(`${BASE_PATH}/data/articles/${id}.json`, { cache: 'no-store' })
          if (!fallbackRes.ok) {
            throw new Error(`Fallback request failed with status ${fallbackRes.status}`)
          }

          const fallbackData = (await fallbackRes.json()) as ArticleDetail
          setArticle(normalizeArticle(fallbackData))
          setFallbackActive(true)
        } catch {
          setArticle(null)
        }
      }
    }

    loadArticle()
  }, [canUseApi, id])

  if (!article) return <div className="mx-auto max-w-4xl px-4 py-8">불러오는 중...</div>

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 md:py-10">
      <Link href="/news" className="text-sm text-blue-600">
        ← 목록으로
      </Link>
      <h1 className="mt-3 text-3xl font-bold leading-[1.4] text-gray-900">{article.title_ko || article.title}</h1>
      <p className="mt-2 text-sm text-gray-500">
        {article.source || '출처 미상'}
        {' · '}
        {article.published_at ? new Date(article.published_at).toLocaleString() : '발행일 미상'}
      </p>

      {fallbackActive && (
        <p className="mt-3 inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
          현재는 정적 데이터(샘플/캐시)를 표시 중
        </p>
      )}

      <section className="mt-8 rounded-2xl border bg-white p-5 shadow-sm md:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">요약</h2>
        <div className="mt-3 space-y-3 text-sm leading-7 text-gray-700">
          {article.summary_lines_ko.map((line, idx) => (
            <p key={idx}>{line}</p>
          ))}
        </div>
      </section>
      <section className="mt-4 rounded-2xl border bg-white p-5 shadow-sm md:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">핵심 포인트</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-7 text-gray-700">
          {article.key_points_ko.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </section>
      <a className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2 text-white" href={article.url} target="_blank" rel="noreferrer">
        원문 링크 열기
      </a>
    </div>
  )
}
