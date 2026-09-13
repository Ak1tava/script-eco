import { NavLink, Route, Routes } from 'react-router-dom'
import { AlertsPage } from './pages/AlertsPage'
import { DashboardPage } from './pages/DashboardPage'
import { StationPage } from './pages/StationPage'

export function App() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink className="brand" to="/" aria-label="EcoWatch Karaganda — главная">
          <span className="brand-mark"><i /><i /><i /></span><span>eco<span>watch</span></span>
        </NavLink>
        <nav><NavLink to="/" end>Обзор</NavLink><NavLink to="/alerts">Предупреждения</NavLink></nav>
        <span className="header-place">Караганда, KZ <i /></span>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/stations/:id" element={<StationPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="*" element={<DashboardPage />} />
        </Routes>
      </main>
      <footer><span>EcoWatch Karaganda · учебный MVP</span><span>Синтетические данные · не использовать для решений о здоровье</span></footer>
    </div>
  )
}

