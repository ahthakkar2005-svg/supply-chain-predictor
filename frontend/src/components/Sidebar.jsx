import React from 'react';

/**
 * Sidebar Navigation Component
 * Premium dark-themed sidebar with navigation and branding
 */
export function Sidebar({ activeView, onViewChange }) {
    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: DashboardIcon },
        { id: 'predictions', label: 'Predictions', icon: PredictionsIcon },
        { id: 'alerts', label: 'Alerts', icon: AlertsIcon },
        { id: 'suppliers', label: 'Suppliers', icon: SuppliersIcon },
        { id: 'ports', label: 'Ports', icon: PortsIcon },
        { id: 'analytics', label: 'Analytics', icon: AnalyticsIcon },
        { id: 'settings', label: 'Settings', icon: SettingsIcon },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <svg viewBox="0 0 40 40" fill="none">
                    <defs>
                        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#6366f1" />
                            <stop offset="100%" stopColor="#8b5cf6" />
                        </linearGradient>
                    </defs>
                    <circle cx="20" cy="12" r="6" fill="url(#logoGrad)" />
                    <circle cx="10" cy="28" r="5" fill="url(#logoGrad)" />
                    <circle cx="30" cy="28" r="5" fill="url(#logoGrad)" />
                    <line x1="20" y1="18" x2="12" y2="24" stroke="url(#logoGrad)" strokeWidth="2" />
                    <line x1="20" y1="18" x2="28" y2="24" stroke="url(#logoGrad)" strokeWidth="2" />
                    <line x1="15" y1="28" x2="25" y2="28" stroke="url(#logoGrad)" strokeWidth="2" />
                </svg>
                <h2>ChainGuard AI</h2>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                        onClick={() => onViewChange(item.id)}
                    >
                        <item.icon />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            <div style={{
                marginTop: 'auto',
                padding: 'var(--space-4)',
                background: 'var(--color-bg-tertiary)',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)'
            }}>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 'var(--space-1)' }}>
                    AI Model Status
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <span style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: 'var(--color-risk-low)',
                        display: 'inline-block'
                    }} />
                    Active & Learning
                </div>
                <div style={{ marginTop: 'var(--space-2)' }}>
                    Version 1.0.0
                </div>
            </div>
        </aside>
    );
}

// Icon Components
function DashboardIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
    );
}

function PredictionsIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
    );
}

function AlertsIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
    );
}

function SuppliersIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
    );
}

function AnalyticsIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
    );
}

function PortsIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M2 21l1-4.5M22 21l-1-4.5M12 3v10" />
            <path d="M4 13l8 4 8-4" />
            <circle cx="12" cy="3" r="1" />
        </svg>
    );
}

function SettingsIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
    );
}

export default Sidebar;
