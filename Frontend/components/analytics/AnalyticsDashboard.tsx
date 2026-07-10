'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  getConversationAnalytics,
  getTopicAnalytics,
  getSentimentAnalytics,
} from '@/lib/api'
import type {
  ConversationOverview,
  TopicAnalytics,
  SentimentAnalytics,
} from '@/types'
import SummaryCards from '@/components/analytics/SummaryCards'
import TopicsChart from '@/components/analytics/TopicsChart'
import SentimentPanel from '@/components/analytics/SentimentPanel'

interface AnalyticsData {
  overview: ConversationOverview
  topics: TopicAnalytics
  sentiment: SentimentAnalytics
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAnalytics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [overview, topics, sentiment] = await Promise.all([
        getConversationAnalytics(),
        getTopicAnalytics(),
        getSentimentAnalytics(),
      ])
      setData({ overview, topics, sentiment })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load analytics'
      setError(message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAnalytics()
  }, [loadAnalytics])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-600
            border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Loading analytics...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center rounded-xl border
          border-rose-200 dark:border-rose-900/50 bg-rose-50
          dark:bg-rose-950/30 p-6">
          <p className="text-sm font-medium text-rose-700
            dark:text-rose-300 mb-1">
            Could not load analytics
          </p>
          <p className="text-xs text-rose-600/80 dark:text-rose-400/80 mb-4">
            {error}
          </p>
          <button
            type="button"
            onClick={loadAnalytics}
            className="px-4 py-2 text-xs font-medium rounded-lg
              bg-indigo-600 text-white hover:bg-indigo-700
              transition-colors"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-white dark:bg-gray-900">
      <div className="max-w-5xl mx-auto space-y-6">
        <SummaryCards data={data.overview} />

        <div className="grid lg:grid-cols-2 gap-6">
          <TopicsChart topics={data.topics.topics} />
          <SentimentPanel data={data.sentiment} />
        </div>
      </div>
    </div>
  )
}
