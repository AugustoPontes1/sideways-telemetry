import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Activity, BarChart3, BookOpen, Boxes, CircleHelp, Gauge, GitBranch, LogIn, Menu, Radio, RefreshCw, X } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Timeline } from './Timeline';

const links = [
  { to: '/', label: 'Visão geral', icon: Gauge, end: true },
  { to: '/telemetry', label: 'Telemetria', icon: Activity },
  { to: '/cartesian', label: 'Plano cartesiano 2D', icon: BarChart3 },
  { to: '/trajectory', label: 'Replay 3D', icon: Boxes },
  { to: '/math', label: 'Laboratório matemático', icon: BookOpen },
];

export function Layout() {
  const { demo, setDemo, sessions, activeSession, selectSession, loading, liveStatus, reloadSessions } = useApp();
  const [open, setOpen] = useState(false);
  const statusLabel = demo ? 'Dados simulados' : liveStatus === 'connected' ? 'Ao vivo' : liveStatus === 'connecting' ? 'Conectando' : 'Desconectado';
  return <div className="app-shell">
    {open && <div className="sidebar-overlay" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="brand">
        <div className="brand-icon"><GitBranch size={24}/></div>
        <div><strong>DRIFT<span>LAB</span></strong><small>TELEMETRY STUDIO</small></div>
        <button className="mobile-only icon-btn" aria-label="Fechar menu" onClick={() => setOpen(false)}><X size={20}/></button>
      </div>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Navegação principal">
        {links.map(({ to, label, icon: Icon, end }) => <NavLink
          key={to} to={to} end={end} onClick={() => setOpen(false)}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Icon size={18} strokeWidth={1.8}/>{label}
        </NavLink>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-guide"><CircleHelp size={18}/><div><strong>Modo de aprendizagem</strong><p>Calcule no papel e revele a solução quando quiser.</p></div></div>
        <div className="sidebar-footer">Assetto Corsa 2014 · G29<br/>Windows → WSL → Homelab</div>
      </div>
    </aside>
    <div className="main-shell">
      <header className="topbar">
        <button className="mobile-only icon-btn" aria-label="Abrir menu" onClick={() => setOpen(true)}><Menu size={22}/></button>
        <div className="session-switcher">
          <span className="field-label">SESSÃO ATIVA</span>
          <div className="session-controls">
            <select aria-label="Selecionar sessão" value={activeSession?.stream_id || ''}
              onChange={(e) => selectSession(e.target.value)} disabled={sessions.length === 0}>
              {sessions.length ? sessions.map((s) => <option key={s.stream_id} value={s.stream_id}>{s.car} • {s.track} ({s.stream_id.slice(0, 8)})</option>) : <option value="">Nenhuma captura</option>}
            </select>
            {!demo && <button className="icon-btn" title="Atualizar sessões" onClick={reloadSessions} disabled={loading}><RefreshCw size={16}/></button>}
          </div>
        </div>
        <div className="topbar-right">
          <span className={`status-pill ${demo ? 'demo' : liveStatus === 'connected' ? 'good' : 'off'}`}>
            <span className="status-dot"/>{statusLabel}
          </span>
          <label className="demo-toggle" title="Exibir dados de demonstração ou integrar com o Django">
            <input type="checkbox" checked={demo} onChange={(e) => setDemo(e.target.checked)} />
            <span>DEMO</span>
          </label>
          {!demo && <a href="/admin/login/?next=/" className="icon-btn login-icon" title="Entrar no Django"><LogIn size={18}/></a>}
        </div>
      </header>
      {demo && <div className="demo-banner"><Radio size={14}/> Demonstração com dados fictícios — ative dados reais no topo para conectar ao homelab.</div>}
      <main className="content"><Outlet/></main>
      <div className="bottom-timeline"><Timeline/></div>
    </div>
  </div>;
}
