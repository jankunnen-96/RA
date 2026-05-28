import { useState, useEffect } from 'react'
import EventCard from '../components/EventCard'
import { API_BASE } from '../lib/api'

export default function WhatsNew() {
  const [events, setEvents] = useState([])
  const [followed, setFollowed] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/events/new`).then((r) => r.json()),
      fetch(`${API_BASE}/api/followed-artists`).then((r) => r.json()),
    ]).then(([evs, fol]) => {
      setEvents(evs)
      setFollowed(fol)
      setLoading(false)
    })
  }, [])

  return (
    <div className="h-full overflow-y-auto bg-[#0f0f0f]">
      <div className="p-4 sticky top-0 bg-[#0f0f0f] z-10 border-b border-[#2d2d2d]">
        <h1 className="text-xl font-bold">What's New</h1>
      </div>
      <div className="px-4">
        {loading && (
          <div className="text-center text-gray-400 py-12">Loading...</div>
        )}
        {!loading && events.length === 0 && (
          <div className="text-center text-gray-400 py-12">No new events yet</div>
        )}
        {events.map((event, i) => (
          <EventCard
            key={i}
            image={event.image}
            date={event.date}
            title={event.title}
            location={event.location}
            artists={event.artists}
            followed={followed}
            url={event.eventUrl}
          />
        ))}
      </div>
    </div>
  )
}
