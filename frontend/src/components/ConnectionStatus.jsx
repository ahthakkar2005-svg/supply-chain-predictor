import React from 'react';
import { WS_STATE } from '../hooks/useWebSocket';

/**
 * Connection Status Indicator
 * Shows live connection status with animated indicator
 */
export function ConnectionStatus({ connectionState, apiStatus }) {
    const statusConfig = {
        [WS_STATE.CONNECTED]: {
            label: 'Live',
            className: 'status-connected',
            icon: '⚡',
        },
        [WS_STATE.CONNECTING]: {
            label: 'Connecting...',
            className: 'status-connecting',
            icon: '🔄',
        },
        [WS_STATE.RECONNECTING]: {
            label: 'Reconnecting...',
            className: 'status-reconnecting',
            icon: '🔄',
        },
        [WS_STATE.DISCONNECTED]: {
            label: 'Offline',
            className: 'status-disconnected',
            icon: '⚠️',
        },
    };

    const config = statusConfig[connectionState] || statusConfig[WS_STATE.DISCONNECTED];

    return (
        <div className={`connection-status ${config.className}`}>
            <span className="connection-dot"></span>
            <span className="connection-label">
                {config.icon} {config.label}
            </span>
            {apiStatus && connectionState === WS_STATE.CONNECTED && (
                <div className="api-badges">
                    {apiStatus.news_api && (
                        <span className="api-badge api-badge-active" title="NewsAPI Connected">
                            📰 News
                        </span>
                    )}
                    {apiStatus.weather_api && (
                        <span className="api-badge api-badge-active" title="Weather API Connected">
                            🌦️ Weather
                        </span>
                    )}
                    {!apiStatus.news_api && !apiStatus.weather_api && (
                        <span className="api-badge api-badge-sim" title="Using simulated data">
                            🔮 Simulated
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}
