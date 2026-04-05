import { useEffect, useState, useRef } from 'react'
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
].sort(() => Math.random() - 0.5)

export default function App() {
  const [isBooting, setIsBooting] = useState(true)
  const [isFading, setIsFading] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [activeImage, setActiveImage] = useState(0)
  const timerRef = useRef(null)
  const slideshowRef = useRef(null)
  const fadeTimeoutRef = useRef(null)
  const startTimeRef = useRef(Date.now())

  useEffect(() => {
    let cancelled = false

    const stopTimers = () => {
      clearInterval(timerRef.current)
      clearInterval(slideshowRef.current)
    }

    const poll = async () => {
      while (!cancelled) {
        try {
          const res = await fetch(`${API_BASE}/api/events?limit=1`)
          if (res.ok) {
            if (!cancelled) {
              stopTimers()
              const elapsed = Date.now() - startTimeRef.current
              const remaining = Math.max(0, 3000 - elapsed)
              fadeTimeoutRef.current = setTimeout(() => {
                if (!cancelled) {
                  setIsFading(true)
                  fadeTimeoutRef.current = setTimeout(() => {
                    if (!cancelled) setIsBooting(false)
                  }, 700)
                }
              }, remaining)
            }
            return
          }
        } catch {
          // backend not up yet
        }
        await new Promise((resolve) => setTimeout(resolve, 2000))
      }
    }

    timerRef.current = setInterval(() => {
      setElapsedSeconds((s) => s + 1)
    }, 1000)

    slideshowRef.current = setInterval(() => {
      setActiveImage((current) => (current + 1) % STOCK_IMAGES.length)
    }, 3500)

    poll()

    return () => {
      cancelled = true
      stopTimers()
      clearTimeout(fadeTimeoutRef.current)
    }
  }, [])

  return (
    <>
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

      {isBooting && (
        <div
          className={`fixed inset-0 flex items-end overflow-hidden bg-black text-white transition-opacity duration-700 ${isFading ? 'opacity-0' : 'opacity-100'}`}
          style={{ zIndex: 9999 }}
        >
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
            <p className="mt-3 max-w-2xl text-sm text-white/85 sm:text-base"></p>

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
      )}
    </>
  )
}