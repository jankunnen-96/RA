import { format } from 'date-fns'

const FALLBACK_IMG =
  'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'

function formatDate(d) {
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
      `<span style="color:#74C365;font-weight:700">${name}</span>`
    )
  })
  return result
}

export default function EventCard({ image, date, title, location, artists, followed, url }) {
  const card = (
    <div className="flex gap-3 py-3 border-b border-[#2d2d2d] last:border-0 active:bg-[#1a1a1a] transition-colors">
      <img
        src={image || FALLBACK_IMG}
        alt=""
        className="w-20 h-20 object-cover rounded-xl flex-shrink-0"
        onError={(e) => {
          e.target.src = FALLBACK_IMG
        }}
      />
      <div className="flex-1 min-w-0">
        <div className="text-xs text-gray-400 mb-0.5 truncate">
          {formatDate(date)}
          {location ? ` · ${location}` : ''}
        </div>
        <div className="font-semibold text-sm leading-snug mb-1">{title}</div>
        <div
          className="text-xs text-gray-300 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: highlightArtists(artists, followed) }}
        />
      </div>
    </div>
  )

  if (url) {
    const href = url.startsWith('http') ? url : `https://ra.co${url}`
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="block">
        {card}
      </a>
    )
  }
  return card
}
