import { AlertTriangle, Database, LogIn } from 'lucide-react';
import { useApp } from '../context/AppContext';

export function EmptyState({ title = 'Nenhuma sessão disponível', detail }: { title?: string; detail?: string }) {
  const { error, streamError, demo, setDemo, reloadSessions, publicMode } = useApp();
  const message = detail || error || streamError || 'Inicie uma sessão do Assetto Corsa com a ponte e o agente conectados.';
  return (
    <div className="empty-state" role="status">
      {error || streamError ? <AlertTriangle size={28} /> : <Database size={28} />}
      <strong>{title}</strong>
      <p>{message}</p>
      <div className="actions-row">
        {!demo && <button className="button button-secondary" onClick={reloadSessions}>Tentar novamente</button>}
        <button className="button button-primary" onClick={() => setDemo(!demo)}>
          {demo ? 'Usar dados reais' : 'Abrir demonstração'}
        </button>
        {!demo && !publicMode && <a className="button button-secondary" href="/admin/login/?next=/"><LogIn size={15} /> Entrar no Django</a>}
      </div>
    </div>
  );
}
