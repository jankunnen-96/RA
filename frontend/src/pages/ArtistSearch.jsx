import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import EventCard from '../components/EventCard'
import { API_BASE } from '../lib/api'

const FALLBACK_IMG =
  'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'

export default function ArtistSearch() {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState({})
  const [events, setEvents] = useState([])
  const [selectedArtist, setSelectedArtist] = useState('')
  const [followed, setFollowed] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/api/followed-artists`).then((r) => r.json()).then(setFollowed)
  }, [])

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions({})
      return
    }
    const t = setTimeout(() => {
      fetch(`${API_BASE}/api/search/artist?q=${encodeURIComponent(query)}`)
        .then((r) => r.json())
        .then(setSuggestions)
    }, 300)
    return () => clearTimeout(t)
  }, [query])

  const selectArtist = async (name, id) => {
    setSelectedArtist(name)
    setSuggestions({})
    setQuery(name)
    setLoading(true)
    const data = await fetch(
      `${API_BASE}/api/artist/${id}/events?name=${encodeURIComponent(name)}`
    ).then((r) => r.json())
    setEvents(data)
    setLoading(false)
  }

  return (
    <div className="h-full overflow-y-auto bg-[#0f0f0f]">
      <div className="p-4 sticky top-0 bg-[#0f0f0f] z-10 border-b border-[#2d2d2d]">
        <h1 className="text-xl font-bold mb-3">Search by Artist</h1>
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedArtist('')
            }}
            placeholder="Artist name..."
            className="w-full bg-[#1a1a1a] text-white border border-[#2d2d2d] rounded-xl pl-9 pr-4 py-3 text-sm"
          />
        </div>
        {Object.keys(suggestions).length > 0 && (
          <div className="mt-2 bg-[#1a1a1a] rounded-xl border border-[#2d2d2d] overflow-hidden">
            {Object.entries(suggestions).map(([name, id]) => (
              <button
                key={id}
                onClick={() => selectArtist(name, id)}
                className="w-full text-left px-4 py-3 text-sm border-b border-[#2d2d2d] last:border-0 active:bg-[#252525]"
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="px-4">
        {loading && (
          <div className="text-center text-gray-400 py-12">Loading events...</div>
        )}
        {!loading && selectedArtist && events.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            No upcoming events for {selectedArtist}
          </div>
        )}
        {!loading &&
          events.map((event, i) => {
            const image = event.images?.[0]?.filename || FALLBACK_IMG
            const location = [
              event.venue?.name,
              event.venue?.area?.name,
              event.venue?.area?.country?.name,
            ]
              .filter(Boolean)
              .join(', ')
            const artists = event.artists?.map((a) => a.name).join(' | ') || ''
            return (
              <EventCard
                key={i}
                image={image}
                date={event.date}
                title={event.title}
                location={location}
                artists={artists}
                followed={followed}
                url={event.contentUrl}
              />
            )
          })}
      </div>
    </div>
  )
}
