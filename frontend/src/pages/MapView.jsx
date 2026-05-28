import { useState, useEffect, useMemo, useCallback } from 'react'
import { API_BASE } from '../lib/api'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import L from 'leaflet'
import { format, addMonths } from 'date-fns'
import { SlidersHorizontal, X } from 'lucide-react'

const FALLBACK_IMG =
  'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'

// Non-linear size scale: min 24px at 1 event, 4x (96px) at 50+ events
const MIN_SIZE = 40
const MAX_SIZE = 72
const SCALE_REF = 100 // event count that reaches max size

function calcSize(count) {
  if (count <= 1) return MIN_SIZE
  const t = Math.min(Math.log(count) / Math.log(SCALE_REF), 1)
  return Math.round(MIN_SIZE + (MAX_SIZE - MIN_SIZE) * t)
}

function makeIcon(count, isCluster = false) {
  const size = calcSize(count)
  const fontSize = Math.max(9, Math.round(size * 0.38))
  const border = isCluster ? '3px' : '2px'
  return L.divIcon({
    html: `<div class="${isCluster ? 'custom-cluster' : 'custom-marker'}" data-count="${count}" style="width:${size}px;height:${size}px;font-size:${fontSize}px;border-width:${border}">${count}</div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
  })
}

function fmtDate(d) {
  try {
    return format(new Date(d), 'EEE d MMM yyyy')
  } catch {
    return d
  }
}

function highlightArtists(text, followed) {
  if (!text || !followed?.length) return text || ''
  let result = text
  followed.forEach((name) => {
    const esc = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    result = result.replace(
      new RegExp(esc, 'gi'),
      `<b style="color:#74C365">${name}</b>`
    )
  })
  return result
}

export default function MapView() {
  const today = format(new Date(), 'yyyy-MM-dd')
  const sixMonths = format(addMonths(new Date(), 6), 'yyyy-MM-dd')

  const [events, setEvents] = useState([])
  const [allArtists, setAllArtists] = useState([])
  const [followed, setFollowed] = useState([])
  const [startDate, setStartDate] = useState(today)
  const [endDate, setEndDate] = useState(sixMonths)
  const [selectedArtists, setSelectedArtists] = useState([])
  const [newOnly, setNewOnly] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [artistSearch, setArtistSearch] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/api/artists`).then((r) => r.json()).then(setAllArtists)
    fetch(`${API_BASE}/api/followed-artists`).then((r) => r.json()).then(setFollowed)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      new_only: newOnly,
    })
    if (selectedArtists.length) params.set('artists', selectedArtists.join(','))
    fetch(`${API_BASE}/api/events?${params}`)
      .then((r) => r.json())
      .then(setEvents)
  }, [startDate, endDate, selectedArtists, newOnly])

  const grouped = useMemo(() => {
    const map = {}
    events.forEach((e) => {
      if (!e.latitude || !e.longitude) return
      const key = `${e.latitude},${e.longitude}`
      if (!map[key]) {
        map[key] = { lat: e.latitude, lon: e.longitude, location: e.location, events: [] }
      }
      map[key].events.push(e)
    })
    return Object.values(map)
  }, [events])

  const filteredArtistSuggestions = allArtists.filter(
    (a) =>
      a.toLowerCase().includes(artistSearch.toLowerCase()) &&
      !selectedArtists.includes(a)
  )

  const toggleArtist = (artist) => {
    setSelectedArtists((prev) =>
      prev.includes(artist) ? prev.filter((a) => a !== artist) : [...prev, artist]
    )
  }

  const activeFilterCount = selectedArtists.length + (newOnly ? 1 : 0)

  // Sum event counts from all child markers by reading the data-count attribute
  const clusterIcon = useCallback((cluster) => {
    const total = cluster.getAllChildMarkers().reduce((sum, marker) => {
      const html = marker.options.icon?.options?.html || ''
      const match = html.match(/data-count="(\d+)"/)
      return sum + (match ? parseInt(match[1], 10) : 1)
    }, 0)
    return makeIcon(total, true)
  }, [])

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[48.8566, 2.3522]}
        zoom={4}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        <MarkerClusterGroup chunkedLoading iconCreateFunction={clusterIcon}>
          {grouped.map(({ lat, lon, location, events: locEvents }) => (
            <Marker
              key={`${lat},${lon}`}
              position={[lat, lon]}
              icon={makeIcon(locEvents.length)}
            >
              <Popup
                maxWidth={Math.min(window.innerWidth * 0.85, 1200)}
                autoPanPadding={[20, 20]}
              >
                {(() => {
                  const popupW = Math.min(window.innerWidth * 0.85, 1200)
                  return (
                    <div style={{ width: popupW, display: 'flex', flexDirection: 'column', maxHeight: '65vh' }}>
                      {/* Sticky header */}
                      <div style={{
                        flexShrink: 0,
                        padding: '14px 16px',
                        borderBottom: '1px solid #2d2d2d',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        background: '#1a1a1a',
                      }}>
                        <div style={{ fontWeight: 700, fontSize: popupW < 400 ? '14px' : '25px', color: '#74C365', marginRight: '10px' }}>
                          {location}
                        </div>
                        <div style={{
                          flexShrink: 0,
                          background: '#74C365',
                          color: '#000',
                          borderRadius: '20px',
                          padding: '3px 11px',
                          fontSize: popupW < 400 ? '12px' : '20px',
                          fontWeight: 700,
                        }}>
                          {locEvents.length} event{locEvents.length !== 1 ? 's' : ''}
                        </div>
                      </div>

                      {/* Scrollable event list */}
                      <div style={{ overflowY: 'auto', flex: 1 }}>
                        {locEvents.map((ev, i) => {
                          const href = ev.eventUrl
                            ? (ev.eventUrl.startsWith('http') ? ev.eventUrl : `https://ra.co${ev.eventUrl}`)
                            : null
                          const imgSize = popupW < 400 ? 100 : 200
                          const card = (
                            <div style={{
                              display: 'flex',
                              gap: '16px',
                              padding: '16px 18px',
                              borderBottom: i < locEvents.length - 1 ? '1px solid #2d2d2d' : 'none',
                              background: '#1a1a1a',
                              transition: 'background 0.15s',
                            }}
                              onMouseEnter={e => e.currentTarget.style.background = '#222'}
                              onMouseLeave={e => e.currentTarget.style.background = '#1a1a1a'}
                            >
                              <img
                                src={ev.image || FALLBACK_IMG}
                                alt=""
                                style={{
                                  width: imgSize,
                                  height: imgSize,
                                  objectFit: 'cover',
                                  borderRadius: '12px',
                                  flexShrink: 0,
                                }}
                                onError={(e) => { e.target.src = FALLBACK_IMG }}
                              />
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                  display: 'inline-block',
                                  background: '#252525',
                                  color: '#9ca3af',
                                  fontSize: popupW < 400 ? '12px' : '17px',
                                  fontWeight: 600,
                                  padding: '3px 10px',
                                  borderRadius: '6px',
                                  marginBottom: '8px',
                                  letterSpacing: '0.02em',
                                }}>
                                  {fmtDate(ev.date)}
                                </div>
                                <div style={{
                                  fontWeight: 700,
                                  fontSize: popupW < 400 ? '14px' : '20px',
                                  lineHeight: 1.25,
                                  marginBottom: '7px',
                                  color: '#fff',
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                }}>
                                  {ev.title}
                                </div>
                                <div
                                  style={{ fontSize: popupW < 400 ? '11px' : '17px', color: '#9ca3af', lineHeight: 1.5 }}
                                  dangerouslySetInnerHTML={{ __html: highlightArtists(ev.artists, followed) }}
                                />
                              </div>
                            </div>
                          )
                          return href
                            ? <a key={i} href={href} target="_blank" rel="noopener noreferrer" style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}>{card}</a>
                            : <div key={i}>{card}</div>
                        })}
                      </div>
                    </div>
                  )
                })()}
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
      </MapContainer>

      {/* Filter button */}
      <div className="absolute top-4 left-4 z-[1000] flex items-center gap-2">
        <button
          onClick={() => setShowFilters(true)}
          className="bg-[#74C365] text-black p-3 rounded-full shadow-lg active:scale-95 transition-transform"
        >
          <SlidersHorizontal size={20} strokeWidth={2.5} />
        </button>
        {activeFilterCount > 0 && (
          <div className="bg-black text-[#74C365] text-xs px-2.5 py-1 rounded-full border border-[#74C365] font-semibold">
            {activeFilterCount} active
          </div>
        )}
      </div>

      {/* Filter drawer */}
      {showFilters && (
        <div className="absolute inset-0 z-[1001] flex flex-col justify-end">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setShowFilters(false)}
          />
          <div className="relative bg-[#1a1a1a] rounded-t-2xl p-5 max-h-[85vh] overflow-y-auto w-full max-w-2xl mx-auto">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-lg font-bold">Filters</h2>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-400 p-1"
              >
                <X size={22} />
              </button>
            </div>

            {/* Date range */}
            <div className="mb-5">
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
                Date Range
              </label>
              <div className="flex gap-3">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="flex-1 bg-[#252525] text-white border border-[#3d3d3d] rounded-xl px-3 py-2.5 text-sm"
                />
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="flex-1 bg-[#252525] text-white border border-[#3d3d3d] rounded-xl px-3 py-2.5 text-sm"
                />
              </div>
            </div>

            {/* New only toggle */}
            <div className="mb-5 flex items-center justify-between">
              <span className="text-sm font-medium">Only show new</span>
              <button
                onClick={() => setNewOnly(!newOnly)}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  newOnly ? 'bg-[#74C365]' : 'bg-[#3d3d3d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all ${
                    newOnly ? 'left-6' : 'left-0.5'
                  }`}
                />
              </button>
            </div>

            {/* Artist filter */}
            <div className="mb-4">
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
                Filter Artist
              </label>

              {selectedArtists.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {selectedArtists.map((a) => (
                    <button
                      key={a}
                      onClick={() => toggleArtist(a)}
                      className="flex items-center gap-1 bg-[#74C365] text-black text-xs px-3 py-1 rounded-full font-semibold"
                    >
                      {a} <X size={11} />
                    </button>
                  ))}
                </div>
              )}

              <input
                type="text"
                placeholder="Search artists..."
                value={artistSearch}
                onChange={(e) => setArtistSearch(e.target.value)}
                className="w-full bg-[#252525] text-white border border-[#3d3d3d] rounded-xl px-3 py-2.5 text-sm mb-2"
              />

              <div className="bg-[#252525] rounded-xl overflow-hidden max-h-52 overflow-y-auto border border-[#3d3d3d]">
                {filteredArtistSuggestions.map((a) => (
                  <button
                    key={a}
                    onClick={() => {
                      toggleArtist(a)
                      setArtistSearch('')
                    }}
                    className="w-full text-left px-4 py-2.5 text-sm border-b border-[#333] last:border-0 active:bg-[#333]"
                  >
                    {a}
                  </button>
                ))}
                {filteredArtistSuggestions.length === 0 && (
                  <div className="px-4 py-3 text-sm text-gray-500">No artists found</div>
                )}
              </div>
            </div>

            <button
              onClick={() => setShowFilters(false)}
              className="w-full bg-[#74C365] text-black font-bold py-3.5 rounded-xl mt-2 text-sm"
            >
              Show {grouped.length} location{grouped.length !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
