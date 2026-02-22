'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

type TopicFilter = 'all' | 'ai' | 'scitech'
type RangeFilter = '24h' | '7d' | '30d'
type SortFilter = 'latest'

type FeedItem = {
  id: string
  title: string
  source: string
  topic: 'ai' | 'scitech'
  published_at: string
  tags: string[]
  url: string
  cluster_id: string
  one_liner: string
}

const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || '/News'

export default function NewsList() {
  const [topic, setTopic] = useState<TopicFilter>('all')
  const [range, setRange] = useState<RangeFilter>('24h')
  const [sortBy, setSortBy] = useState<SortFilter>('latest')
  const [keyword, setKeyword] = useState('')
  const [items, setItems] = useState<FeedItem[]>([])

  useEffect(() => {
    fetch(`${BASE_PATH}/data/feed.json`)
      .then((res) => res.json())
      .then((data: FeedItem[]) => setItems(data))
      .catch(() => setItems([]))
  }, [])

  const filtered = useMemo(() => {
    const now = Date.now()
    const rangeMs = {
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    }[range]

    const q = keyword.trim().toLowerCase()

    return items
      .filter((item) => topic === 'all' || item.topic === topic)
      .filter((item) => now - new Date(item.published_at).getTime() <= rangeMs)
      .filter((item) => {
        if (!q) return true
        return item.title.toLowerCase().includes(q) || item.one_liner.toLowerCase().includes(q)
      })
      .sort((a, b) => {
        return new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      })
  }, [items, keyword, range, sortBy, topic])

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <h1 className="mb-2 text-2xl font-bold">News</h1>
      <p className="mb-6 text-sm text-gray-600">AI · ScienceTech 브리핑</p>

      <div className="mb-6 rounded-xl border bg-white p-4 shadow-sm space-y-4">
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
                topic === value ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-700'
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
                range === value ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700'
              }`}
            >
              {value}
            </button>
          ))}
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <input
            className="rounded-lg border px-3 py-2 text-sm md:col-span-2"
            placeholder="제목/요약 키워드 검색"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <select
            className="rounded-lg border px-3 py-2 text-sm"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortFilter)}
          >
            <option value="latest">최신순</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {filtered.map((item) => (
          <Link
            key={item.id}
            href={`/news/${item.id}`}
            className="block rounded-xl border bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow"
          >
            <h2 className="text-lg font-semibold text-gray-900">{item.title}</h2>
            <p className="mt-1 text-xs uppercase tracking-wide text-gray-500">
              {item.topic === 'ai' ? 'AI' : 'ScienceTech'}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              {item.source} · {new Date(item.published_at).toLocaleString()}
            </p>
            <p className="mt-3 text-sm text-gray-700">{item.one_liner}</p>
          </Link>
        ))}

        {!filtered.length && <p className="rounded-xl border bg-white p-4 text-sm text-gray-500">조건에 맞는 기사가 없습니다.</p>}
      </div>
    </div>
  )
}
