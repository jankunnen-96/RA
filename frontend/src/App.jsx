import { useEffect, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import MapView from './pages/MapView'
import ArtistSearch from './pages/ArtistSearch'
import CitySearch from './pages/CitySearch'
import WhatsNew from './pages/WhatsNew'
import Navbar from './components/Navbar'
import { API_BASE } from './lib/api'

const STOCK_IMAGES = [
  '/images/2.jpeg',
  '/images/6.jfif',
  '/images/6.jpeg',
  '/images/8.jpg',
  '/images/9.jpg',
  '/images/10.jpg', 
  '/images/11.jpg',
  '/images/4.jfif',
]

export default function App() {
  const [isBooting, setIsBooting] = useState(true)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [activeImage, setActiveImage] = useState(0)

  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      while (!cancelled) {
        try {
          const res = await fetch(`${API_BASE}/api/events?limit=1`)
          if (res.ok) {
            if (!cancelled) setIsBooting(false)
            return
          }
        } catch {
          // backend not up yet
        }
        await new Promise((resolve) => setTimeout(resolve, 2000))
      }
    }

    const timer = setInterval(() => {
      setElapsedSeconds((s) => s + 1)
    }, 1000)

    poll()

    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    const slideshowInterval = setInterval(() => {
      setActiveImage((current) => (current + 1) % STOCK_IMAGES.length)
    }, 3000)

    return () => clearInterval(slideshowInterval)
  }, [])

  if (isBooting) {
    return (
      <div className="relative flex h-[100dvh] items-end overflow-hidden bg-black text-white">
        {STOCK_IMAGES.map((image, index) => (
          <div
            key={image}
            className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ${index === activeImage ? 'opacity-100' : 'opacity-0'}`}
            style={{ backgroundImage: `url(${image})` }}
          />
        ))}

        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/45 to-black/20" />

        <div className="relative z-10 w-full p-6 sm:p-10">
          <p className="text-xs uppercase tracking-[0.35em] text-white/70">Starting server</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-5xl">Loading events</h1>
          <p className="mt-3 max-w-2xl text-sm text-white/85 sm:text-base">
          </p>

          <div className="mt-6 flex items-center gap-3">
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-2 w-2 rounded-full bg-[#74C365] animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <p className="text-sm font-semibold text-[#74C365]">{elapsedSeconds}s elapsed</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col bg-[#0f0f0f]" style={{ height: '100dvh' }}>
      <Navbar />
      <div className="flex-1 overflow-hidden min-h-0">
        <Routes>
          <Route path="/" element={<MapView />} />
          <Route path="/artist" element={<ArtistSearch />} />
          <Route path="/city" element={<CitySearch />} />
          <Route path="/new" element={<WhatsNew />} />
        </Routes>
      </div>
    </div>
  )
}
