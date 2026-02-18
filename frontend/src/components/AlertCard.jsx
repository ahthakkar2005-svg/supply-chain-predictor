import React from 'react';
import { formatDistanceToNow } from '../utils/formatters';

/**
 * Alert Card Component
 * Displays a single alert with severity styling
 */
export function AlertCard({ alert, onClick }) {
    const { title, message, risk_level, region, is_read, created_at } = alert;
    const level = risk_level?.toLowerCase() || 'medium';

    const getIcon = () => {
        switch (level) {
            case 'critical':
                return (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polygon points="12,2 22,22 2,22" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <circle cx="12" cy="17" r="1" fill="currentColor" />
                    </svg>
                );
            case 'high':
                return (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <circle cx="12" cy="16" r="1" fill="currentColor" />
                    </svg>
                );
            default:
                return (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <circle cx="12" cy="8" r="1" fill="currentColor" />
                    </svg>
                );
        }
    };

    const timeAgo = formatDistanceToNow(created_at);

    return (
        <div
            className={`alert-item ${level} animate-fadeIn`}
            onClick={() => onClick?.(alert)}
            role="button"
            tabIndex={0}
        >
            <div className="alert-icon">
                {getIcon()}
            </div>
            <div className="alert-content">
                <div className="alert-title">
                    {!is_read && <span className="unread-badge" />}
                    {title}
                </div>
                <div className="alert-message">{message}</div>
                <div className="alert-meta">
                    {region} • {timeAgo}
                </div>
            </div>
        </div>
    );
}

/**
 * Alert List Component
 */
export function AlertList({ alerts = [], onAlertClick }) {
    if (alerts.length === 0) {
        return (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No active alerts
            </div>
        );
    }

    return (
        <div className="alerts-list">
            {alerts.map((alert, index) => (
                <AlertCard
                    key={alert.id || index}
                    alert={alert}
                    onClick={onAlertClick}
                />
            ))}
        </div>
    );
}

export default AlertCard;
