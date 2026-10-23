import type { PropsWithChildren, ReactNode } from 'react';

export function Panel({ children, title, subtitle, action, className = '' }: PropsWithChildren<{
  title?: string; subtitle?: string; action?: ReactNode; className?: string;
}>) {
  return (
    <section className={`panel ${className}`}>
      {(title || action) && (
        <div className="panel-head">
          <div>
            {title && <h3>{title}</h3>}
            {subtitle && <p className="panel-subtitle">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
