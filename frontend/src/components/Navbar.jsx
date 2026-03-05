import { NavLink } from 'react-router-dom'
import { Map, Music, MapPin, Sparkles } from 'lucide-react'

const tabs = [
  { to: '/', icon: Map, label: 'Map' },
  { to: '/artist', icon: Music, label: 'Artist' },
  { to: '/city', icon: MapPin, label: 'City' },
  { to: '/new', icon: Sparkles, label: 'New' },
]

export default function Navbar() {
  return (
    <nav className="bg-[#111] border-t border-[#2d2d2d] flex flex-shrink-0">
      {tabs.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center py-2.5 gap-0.5 text-xs font-medium transition-colors ${
              isActive ? 'text-[#74C365]' : 'text-gray-500'
            }`
          }
        >
          <Icon size={22} strokeWidth={1.8} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
