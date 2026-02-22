'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

type Topic = 'ai' | 'scitech'
type Range = '24h' | '7d'

type FeedItem = {
  id: number
  title: string
  url: string
  source_name: string
  topic: Topic
  published_at: string | null
  summary: { one_liner: string } | null
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function NewsList() {
  const [topic, setTopic] = useState<Topic>('ai')
  const [range, setRange] = useState<Range>('24h')
  const [items, setItems] = useState<FeedItem[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/feed?topic=${topic}&range=${range}`)
      .then((r) => r.json())
      .then(setItems)
      .catch(() => setItems([]))
  }, [topic, range])

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-bold mb-4">AI & Science/Tech News Digest</h1>
      <div className="flex gap-3 mb-6">
        <select className="rounded border p-2" value={topic} onChange={(e) => setTopic(e.target.value as Topic)}>
          <option value="ai">AI</option>
          <option value="scitech">ScienceTech</option>
        </select>
        <select className="rounded border p-2" value={range} onChange={(e) => setRange(e.target.value as Range)}>
          <option value="24h">24h</option>
          <option value="7d">7d</option>
        </select>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <Link key={item.id} href={`/news/${item.id}`} className="block rounded-lg border bg-white p-4 hover:shadow">
            <div className="text-lg font-semibold">{item.title}</div>
            <div className="text-sm text-gray-500 mt-1">
              {item.source_name} · {item.published_at ? new Date(item.published_at).toLocaleString() : 'No date'}
            </div>
            <div className="mt-2 text-sm text-gray-700">{item.summary?.one_liner || '요약 없음'}</div>
          </Link>
        ))}
        {!items.length && <p className="text-sm text-gray-500">No articles found.</p>}
      </div>
    </div>
  )
}
