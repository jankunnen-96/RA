import { Routes, Route } from 'react-router-dom'
import MapView from './pages/MapView'
import ArtistSearch from './pages/ArtistSearch'
import CitySearch from './pages/CitySearch'
import WhatsNew from './pages/WhatsNew'
import Navbar from './components/Navbar'

export default function App() {
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
