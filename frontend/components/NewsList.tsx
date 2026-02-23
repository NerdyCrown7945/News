'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

type TopicFilter = 'all' | 'ai' | 'scitech'
type RangeFilter = '24h' | '7d' | '30d'
type SortFilter = 'new'

type FeedItem = {
  id: string
  title: string
  title_ko?: string
  source: string
  topic: 'ai' | 'scitech'
  published_at: string
  tags: string[]
  url: string
  one_liner: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || ''

const isLocalHost = () => {
  if (typeof window === 'undefined') return false
  return ['localhost', '127.0.0.1'].includes(window.location.hostname)
}

const normalizeStaticFeed = (rows: Array<Record<string, unknown>>): FeedItem[] => {
  return rows.map((row) => ({
    id: String(row.id ?? ''),
    title: String(row.title ?? ''),
    title_ko: typeof row.title_ko === 'string' ? row.title_ko : undefined,
    source: String(row.source ?? ''),
    topic: (row.topic === 'ai' ? 'ai' : 'scitech') as 'ai' | 'scitech',
    published_at: String(row.published_at ?? new Date().toISOString()),
    tags: Array.isArray(row.tags) ? (row.tags as string[]) : [],
    url: String(row.url ?? '#'),
    one_liner: String(row.one_liner ?? row.title ?? ''),
  }))
}

export default function NewsList() {
  const [topic, setTopic] = useState<TopicFilter>('all')
  const [range, setRange] = useState<RangeFilter>('24h')
  const [sortBy, setSortBy] = useState<SortFilter>('new')
  const [keyword, setKeyword] = useState('')
  const [items, setItems] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(false)
  const [usingStaticFallback, setUsingStaticFallback] = useState(false)
  const [notice, setNotice] = useState('')

  const loadFallbackFeed = async () => {
    const fallbackRes = await fetch(`${BASE_PATH}/data/feed.json`, { cache: 'no-store' })
    if (!fallbackRes.ok) throw new Error('fallback feed fetch failed')
    const fallbackData = (await fallbackRes.json()) as Array<Record<string, unknown>>
    setItems(normalizeStaticFeed(fallbackData))
    setUsingStaticFallback(true)
  }

  const loadFeed = async () => {
    setLoading(true)
    setNotice('')
    try {
      const params = new URLSearchParams({ topic, range, query: keyword, sort: sortBy })
      const res = await fetch(`${API_BASE}/feed?${params.toString()}`, { cache: 'no-store' })
      if (!res.ok) {
        throw new Error(`api status ${res.status}`)
      }
      const data = (await res.json()) as FeedItem[]
      setItems(data)
      setUsingStaticFallback(false)
    } catch {
      await loadFallbackFeed()
      setNotice('백엔드 연결에 실패하여 정적 데이터(샘플/캐시)를 표시 중입니다.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFeed()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, range, sortBy])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return items
    return items.filter((item) => {
      const text = `${item.title} ${item.title_ko || ''} ${item.one_liner}`.toLowerCase()
      return text.includes(q)
    })
  }, [items, keyword])

  const runIngest = async () => {
    if (!isLocalHost()) {
      setNotice('수집 실행은 로컬 환경에서만 동작합니다. (백엔드 필요)')
      return
    }
    try {
      const res = await fetch(`${API_BASE}/ingest/run`, { method: 'POST' })
      if (!res.ok) throw new Error('ingest failed')
      await loadFeed()
    } catch {
      setNotice('수집 실행에 실패했습니다. 로컬 백엔드(127.0.0.1:8000)가 실행 중인지 확인해 주세요.')
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:py-10">
      <h1 className="mb-2 text-3xl font-bold">News</h1>
      <p className="mb-6 text-sm leading-6 text-gray-600">AI · ScienceTech 한국어 요약 브리핑</p>

      <div className="mb-7 space-y-4 rounded-2xl border bg-white p-4 shadow-sm md:p-5">
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
          <select className="rounded-lg border px-3 py-2 text-sm" value={sortBy} onChange={(e) => setSortBy(e.target.value as SortFilter)}>
            <option value="new">최신순</option>
          </select>
          <button
            onClick={runIngest}
            disabled={!isLocalHost()}
            className="rounded-lg border bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-gray-400"
            title={!isLocalHost() ? 'GitHub Pages에서는 사용할 수 없습니다.' : '로컬 백엔드에서 수집 실행'}
          >
            수집 실행
          </button>
        </div>
      </div>

      {notice && <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">{notice}</p>}
      {loading && <p className="mb-4 text-sm text-gray-500">불러오는 중...</p>}

      <div className="space-y-4">
        {filtered.map((item) => (
          <Link key={item.id} href={`/news/${item.id}`} className="block rounded-2xl border bg-white p-5 shadow-sm transition hover:-translate-y-0.5">
            <h2 className="text-xl font-semibold leading-8 text-gray-900">{item.title_ko || item.title}</h2>
            <p className="mt-2 text-sm text-gray-500">{item.source} · {new Date(item.published_at).toLocaleString()}</p>
            <p className="mt-3 text-sm leading-7 text-gray-700">{item.one_liner}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {item.tags?.map((tag) => (
                <span key={tag} className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">#{tag}</span>
              ))}
            </div>
          </Link>
        ))}

        {!filtered.length && <p className="rounded-xl border bg-white p-4 text-sm text-gray-500">조건에 맞는 기사가 없습니다.</p>}
      </div>

      {usingStaticFallback && (
        <div className="mt-6 inline-flex rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700">
          현재는 정적 데이터(샘플/캐시)를 표시 중
        </div>
      )}
    </div>
  )
}
