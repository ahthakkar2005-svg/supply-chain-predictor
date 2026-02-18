import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { MetricsGrid, CategoryRiskTable, SupplierTable } from './components/MetricCards';
import { RiskGauge } from './components/RiskGauge';
import { AlertList } from './components/AlertCard';
import { RiskTrendChart, ForecastChart } from './components/Charts';
import { NewsFeed } from './components/NewsFeed';
import { RegionMap } from './components/RegionMap';
import { PortMonitor } from './components/PortMonitor';
import { ConnectionStatus } from './components/ConnectionStatus';
import { RealtimeToast } from './components/RealtimeToast';
import { useWebSocket } from './hooks/useWebSocket';
import { useDashboardData, useForecast } from './hooks/useDashboard';
import { formatDate, formatTime } from './utils/formatters';

/**
 * Main Application Component
 * Supply Chain Disruption Prediction Dashboard
 */
function App() {
    const [activeView, setActiveView] = useState('dashboard');
    const webSocket = useWebSocket();
    const {
        summary,
        regions,
        alerts,
        news,
        timeSeries,
        metrics,
        suppliers,
        loading,
        refresh
    } = useDashboardData(webSocket);
    const { forecast } = useForecast(14);

    const renderDashboard = () => (
        <>
            {/* Header */}
            <div className="dashboard-header">
                <div className="dashboard-title">
                    <h1>Supply Chain Intelligence</h1>
                    <p>
                        AI-powered disruption prediction and risk monitoring •
                        Last updated: {summary ? `${formatDate(summary.last_updated)} ${formatTime(summary.last_updated)}` : 'Loading...'}
                    </p>
                    <ConnectionStatus connectionState={webSocket.connectionState} apiStatus={webSocket.apiStatus} />
                </div>
                <div className="dashboard-actions">
                    <button className="btn btn-secondary" onClick={refresh}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M23 4v6h-6" />
                            <path d="M1 20v-6h6" />
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                        </svg>
                        Refresh
                    </button>
                    <button className="btn btn-primary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Export Report
                    </button>
                </div>
            </div>

            {/* Key Metrics */}
            <MetricsGrid summary={summary} />

            {/* Main Grid */}
            <div className="dashboard-grid">
                {/* Risk Trend Chart */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                            </svg>
                            Risk Trend Analysis
                        </h3>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                            Last 30 days
                        </span>
                    </div>
                    <RiskTrendChart data={timeSeries} height={280} />
                </div>

                {/* Active Alerts */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                            </svg>
                            Active Alerts
                        </h3>
                        <span className="badge critical">{alerts.filter(a => !a.is_read).length} New</span>
                    </div>
                    <AlertList alerts={alerts} />
                </div>
            </div>

            {/* Geographic Risk Map */}
            <div className="card full-width" style={{ marginBottom: 'var(--space-6)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="2" y1="12" x2="22" y2="12" />
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                        </svg>
                        Global Risk Overview
                    </h3>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        Real-time regional monitoring
                    </span>
                </div>
                <RegionMap regions={regions} />
            </div>

            {/* Secondary Grid */}
            <div className="dashboard-grid">
                {/* AI Forecast */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                            </svg>
                            AI Risk Forecast
                        </h3>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                            Next 14 days prediction
                        </span>
                    </div>
                    <ForecastChart data={forecast} height={250} />
                </div>

                {/* Risk Gauge */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div className="card-header" style={{ width: '100%' }}>
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M12 6v6l4 2" />
                            </svg>
                            Current Risk Level
                        </h3>
                    </div>
                    <RiskGauge
                        score={summary?.overall_risk_score || 0}
                        label="Overall Supply Chain Risk"
                    />
                    <div style={{
                        marginTop: 'var(--space-4)',
                        padding: 'var(--space-3)',
                        background: 'var(--color-bg-tertiary)',
                        borderRadius: 'var(--radius-md)',
                        width: '100%',
                        fontSize: 'var(--font-size-sm)',
                        color: 'var(--color-text-secondary)'
                    }}>
                        <strong style={{ color: 'var(--color-text-primary)' }}>AI Assessment:</strong>
                        {' '}Elevated risk due to geopolitical tensions and seasonal shipping constraints.
                    </div>
                </div>
            </div>

            {/* Bottom Grid */}
            <div className="dashboard-grid" style={{ marginTop: 'var(--space-6)' }}>
                {/* News Feed */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1M19 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2M5 4h10" />
                                <line x1="8" y1="10" x2="12" y2="10" />
                                <line x1="8" y1="14" x2="14" y2="14" />
                            </svg>
                            Supply Chain News
                        </h3>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                            AI-analyzed sentiment
                        </span>
                    </div>
                    <NewsFeed news={news} />
                </div>

                {/* Category Risk Table */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="20" x2="18" y2="10" />
                                <line x1="12" y1="20" x2="12" y2="4" />
                                <line x1="6" y1="20" x2="6" y2="14" />
                            </svg>
                            Risk by Category
                        </h3>
                    </div>
                    <CategoryRiskTable metrics={metrics} />
                </div>
            </div>

            {/* Suppliers Table */}
            <div className="card full-width" style={{ marginTop: 'var(--space-6)' }}>
                <div className="card-header">
                    <h3 className="card-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                            <circle cx="9" cy="7" r="4" />
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                        </svg>
                        Top Supplier Risks
                    </h3>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        Sorted by risk score
                    </span>
                </div>
                <SupplierTable suppliers={suppliers} />
            </div>
        </>
    );

    const renderPredictions = () => (
        <div className="card">
            <h2 style={{ marginBottom: 'var(--space-6)' }}>AI Predictions</h2>
            <p style={{ color: 'var(--color-text-muted)' }}>
                Detailed prediction analysis coming soon. The AI models are continuously learning from real-time data.
            </p>
            <div style={{ marginTop: 'var(--space-6)' }}>
                <ForecastChart data={forecast} height={400} />
            </div>
        </div>
    );

    const renderAlerts = () => (
        <div className="card">
            <h2 style={{ marginBottom: 'var(--space-6)' }}>All Alerts</h2>
            <AlertList alerts={alerts} />
        </div>
    );

    const renderSuppliers = () => (
        <div className="card">
            <h2 style={{ marginBottom: 'var(--space-6)' }}>Supplier Risk Management</h2>
            <SupplierTable suppliers={suppliers} />
        </div>
    );

    const renderAnalytics = () => (
        <>
            <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
                <h2 style={{ marginBottom: 'var(--space-6)' }}>Analytics Dashboard</h2>
                <RiskTrendChart data={timeSeries} height={400} />
            </div>
            <div className="dashboard-grid">
                <div className="card">
                    <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>Category Breakdown</h3>
                    <CategoryRiskTable metrics={metrics} />
                </div>
                <div className="card" style={{ display: 'flex', justifyContent: 'center' }}>
                    <RiskGauge score={summary?.overall_risk_score || 0} size={200} />
                </div>
            </div>
        </>
    );

    const renderSettings = () => (
        <div className="card">
            <h2 style={{ marginBottom: 'var(--space-6)' }}>Settings</h2>
            <p style={{ color: 'var(--color-text-muted)' }}>
                Configuration options and preferences will be available here.
            </p>
            <div style={{ marginTop: 'var(--space-6)', padding: 'var(--space-4)', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                <h4 style={{ marginBottom: 'var(--space-3)' }}>API Configuration</h4>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                    Connect your NewsAPI, Twitter, and other data sources to enable live data ingestion.
                </p>
            </div>
        </div>
    );

    const renderContent = () => {
        switch (activeView) {
            case 'predictions': return renderPredictions();
            case 'alerts': return renderAlerts();
            case 'suppliers': return renderSuppliers();
            case 'ports': return <PortMonitor />;
            case 'analytics': return renderAnalytics();
            case 'settings': return renderSettings();
            default: return renderDashboard();
        }
    };

    return (
        <div className="app-container">
            <Sidebar activeView={activeView} onViewChange={setActiveView} />
            <main className="main-content">
                {loading ? (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '50vh',
                        flexDirection: 'column',
                        gap: 'var(--space-4)'
                    }}>
                        <div style={{
                            width: 48,
                            height: 48,
                            border: '3px solid var(--color-border)',
                            borderTopColor: 'var(--color-primary)',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite'
                        }} />
                        <p style={{ color: 'var(--color-text-muted)' }}>Loading AI predictions...</p>
                        <style>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
                    </div>
                ) : (
                    renderContent()
                )}
            </main>
            <RealtimeToast webSocket={webSocket} />
        </div>
    );
}

export default App;
