'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'

type TopicFilter = 'all' | 'ai' | 'scitech'
type RangeFilter = '24h' | '7d' | '30d'
type SortFilter = 'new'

type FeedItem = {
  id: string
  title: string
  title_ko?: string
  source?: string
  topic: 'ai' | 'scitech'
  published_at?: string
  tags: string[]
  url: string
  one_liner: string
}

const API_BASE_ENV = process.env.NEXT_PUBLIC_API_BASE
const API_BASE = API_BASE_ENV || 'http://127.0.0.1:8000'
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || ''
const STATIC_FEED_PATH = `${BASE_PATH}/data/feed.json`

const SECTION_PATHS = ['blog', 'blogs', 'news', 'updates', 'stories', 'research', 'press']

const isLikelyHomeOrSectionUrl = (value: string): boolean => {
  try {
    const parsed = new URL(value)
    const path = parsed.pathname.replace(/^\/+|\/+$/g, '').toLowerCase()
    if (!path) return true

    const segments = path.split('/').filter(Boolean)
    if (!segments.length) return true

    if (segments.length === 1 && SECTION_PATHS.includes(segments[0])) return true

    if (segments.length <= 2) {
      const joined = segments.join('/')
      if (joined === 'discover/blog') return true
      if (segments.length > 0 && SECTION_PATHS.includes(segments[0])) return true
    }

    return false
  } catch {
    return true
  }
}

export default function NewsList() {
  const [topic, setTopic] = useState<TopicFilter>('all')
  const [range, setRange] = useState<RangeFilter>('24h')
  const [sortBy, setSortBy] = useState<SortFilter>('new')
  const [keyword, setKeyword] = useState('')
  const [items, setItems] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(false)
  const [fallbackActive, setFallbackActive] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  const isLocalhost = useMemo(() => {
    if (typeof window === 'undefined') return false
    const host = window.location.hostname
    return host === '127.0.0.1' || host === 'localhost'
  }, [])

  const canUseApi = isLocalhost || Boolean(API_BASE_ENV)

  const loadFeed = useCallback(async () => {
    setLoading(true)
    setNotice(null)

    const params = new URLSearchParams({ topic, range, query: keyword, sort: sortBy })

    try {
      if (!canUseApi) throw new Error('API disabled (Pages mode)')

      const res = await fetch(`${API_BASE}/feed?${params.toString()}`, { cache: 'no-store' })
      if (!res.ok) throw new Error(`API request failed with status ${res.status}`)

      const data = (await res.json()) as FeedItem[]
      setItems(data)
      setFallbackActive(false)
      return
    } catch {
      try {
        const fallbackRes = await fetch(STATIC_FEED_PATH, { cache: 'no-store' })
        if (!fallbackRes.ok) throw new Error(`Fallback request failed with status ${fallbackRes.status}`)

        const fallbackData = (await fallbackRes.json()) as FeedItem[]
        setItems(fallbackData)
        setFallbackActive(true)
        setNotice(
          canUseApi
            ? '백엔드 연결에 실패하여 정적 데이터(샘플/캐시)를 표시 중입니다.'
            : 'GitHub Pages 환경에서 정적 데이터(샘플/캐시)를 표시 중입니다.'
        )
      } catch {
        setItems([])
        setFallbackActive(true)
        setNotice('백엔드와 정적 데이터를 모두 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
      }
    } finally {
      setLoading(false)
    }
  }, [canUseApi, keyword, range, sortBy, topic])

  useEffect(() => {
    loadFeed()
  }, [loadFeed])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return items
    return items.filter((item) => {
      const text = `${item.title} ${item.title_ko || ''} ${item.one_liner}`.toLowerCase()
      return text.includes(q)
    })
  }, [items, keyword])

  const runIngest = async () => {
    if (!isLocalhost) {
      setNotice('수집 실행은 로컬(127.0.0.1/localhost) 환경에서만 사용할 수 있습니다.')
      return
    }

    setNotice(null)
    await fetch(`${API_BASE}/ingest/run`, { method: 'POST' })
    await loadFeed()
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:py-10">
      <h1 className="mb-2 text-3xl font-bold">News</h1>
      <p className="mb-6 text-sm leading-6 text-gray-600">AI · ScienceTech 한국어 요약 브리핑</p>

      <div className="mb-7 space-y-4 rounded-2xl border bg-white p-4 shadow-sm md:p-5">
        {notice && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">{notice}</p>
        )}

        <div className="flex flex-wrap gap-2">
          {[
            ['ai', 'AI'],
            ['scitech', 'ScienceTech'],
            ['all', 'All'],
          ].map(([value, label]) => (
            <button
              key={value}
              onClick={() => setTopic(value as TopicFilter)}
              className={`rounded-full border px-4 py-2 text-sm ${
                topic === value ? 'border-gray-900 bg-gray-900 text-white' : 'bg-white text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {(['24h', '7d', '30d'] as RangeFilter[]).map((value) => (
            <button
              key={value}
              onClick={() => setRange(value)}
              className={`rounded-full border px-4 py-2 text-sm ${
                range === value ? 'border-blue-600 bg-blue-600 text-white' : 'bg-white text-gray-700'
              }`}
            >
              {value}
            </button>
          ))}
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <input
            className="rounded-lg border px-3 py-2 text-sm leading-6 md:col-span-2"
            placeholder="제목/요약 키워드 검색"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <select
            className="rounded-lg border px-3 py-2 text-sm"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortFilter)}
          >
            <option value="new">최신순</option>
          </select>
          <button
            onClick={runIngest}
            disabled={!isLocalhost}
            title={!isLocalhost ? '수집 실행은 로컬 환경에서만 가능합니다.' : undefined}
            className="rounded-lg border bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-emerald-300"
          >
            수집 실행
          </button>
        </div>
      </div>

      {loading && <p className="mb-4 text-sm text-gray-500">불러오는 중...</p>}

      <div className="space-y-4">
        {filtered.map((item) => (
          <Link
            key={item.id}
            href={`/news/${item.id}`}
            className="block rounded-2xl border bg-white p-5 shadow-sm transition hover:-translate-y-0.5"
          >
            <h2 className="text-xl font-semibold leading-8 text-gray-900">{item.title_ko || item.title}</h2>
            <p className="mt-2 text-sm text-gray-500">
              {item.source || '출처 미상'}
              {' · '}
              {item.published_at ? new Date(item.published_at).toLocaleString() : '발행일 미상'}
            </p>
            <p className="mt-3 text-sm leading-7 text-gray-700">{item.one_liner}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {item.tags?.map((tag) => (
                <span key={tag} className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                  #{tag}
                </span>
              ))}
              {(!item.url || isLikelyHomeOrSectionUrl(item.url)) && (
                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-700">원문 링크 없음</span>
              )}
            </div>
          </Link>
        ))}

        {!loading && !filtered.length && (
          <p className="rounded-xl border bg-white p-4 text-sm text-gray-500">조건에 맞는 기사가 없습니다.</p>
        )}
      </div>

      {fallbackActive && (
        <p className="mt-6 inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
          현재는 정적 데이터(샘플/캐시)를 표시 중
        </p>
      )}
    </div>
  )
}