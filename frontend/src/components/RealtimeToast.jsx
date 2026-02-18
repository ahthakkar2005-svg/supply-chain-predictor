import React, { useState, useEffect, useCallback } from 'react';

/**
 * Real-time Toast Notifications
 * Displays temporary notifications for new alerts, news, and weather updates
 */
export function RealtimeToast({ webSocket }) {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((toast) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev.slice(-4), { ...toast, id }]); // Keep max 5

        // Auto-remove after 8 seconds
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 8000);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    useEffect(() => {
        if (!webSocket) return;

        // Listen for weather alerts
        const unsubWeather = webSocket.on('weather_alert', (data) => {
            if (data?.alerts) {
                data.alerts.forEach(alert => {
                    addToast({
                        type: alert.risk_level === 'critical' ? 'critical' : 'warning',
                        title: alert.title,
                        message: alert.message?.substring(0, 100),
                        icon: '🌦️',
                    });
                });
            }
        });

        // Listen for new news
        const unsubNews = webSocket.on('new_news', (data) => {
            if (data?.articles?.length > 0) {
                const article = data.articles[0];
                addToast({
                    type: article.sentiment_score < -0.3 ? 'warning' : 'info',
                    title: '📰 Breaking News',
                    message: article.title?.substring(0, 120),
                    icon: '📰',
                });
            }
        });

        // Listen for critical risk changes
        const unsubRisk = webSocket.on('risk_update', (data) => {
            if (data?.overall_risk_level === 'critical' && data?.risk_trend === 'up') {
                addToast({
                    type: 'critical',
                    title: '🚨 Risk Level Critical',
                    message: `Overall risk score: ${(data.overall_risk_score * 100).toFixed(1)}% — Trending UP`,
                    icon: '🚨',
                });
            }
        });

        return () => {
            unsubWeather();
            unsubNews();
            unsubRisk();
        };
    }, [webSocket, addToast]);

    if (toasts.length === 0) return null;

    return (
        <div className="toast-container">
            {toasts.map(toast => (
                <div
                    key={toast.id}
                    className={`toast toast-${toast.type}`}
                    onClick={() => removeToast(toast.id)}
                >
                    <div className="toast-header">
                        <span className="toast-icon">{toast.icon}</span>
                        <span className="toast-title">{toast.title}</span>
                        <button className="toast-close" onClick={(e) => { e.stopPropagation(); removeToast(toast.id); }}>
                            ✕
                        </button>
                    </div>
                    {toast.message && (
                        <div className="toast-message">{toast.message}</div>
                    )}
                    <div className="toast-progress"></div>
                </div>
            ))}
        </div>
    );
}
