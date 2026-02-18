import React, { useState, useEffect, useCallback } from 'react';

/**
 * Port Monitor Component
 * Searchable, filterable view of all monitored supply chain ports & hubs
 */
export function PortMonitor() {
    const [ports, setPorts] = useState([]);
    const [search, setSearch] = useState('');
    const [regionFilter, setRegionFilter] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchPorts = useCallback(async () => {
        try {
            const params = new URLSearchParams();
            if (search) params.set('search', search);
            if (regionFilter) params.set('region', regionFilter);
            const url = `/api/dashboard/ports${params.toString() ? '?' + params.toString() : ''}`;
            const res = await fetch(url);
            const data = await res.json();
            setPorts(data);
        } catch (err) {
            console.error('Failed to fetch ports:', err);
        } finally {
            setLoading(false);
        }
    }, [search, regionFilter]);

    useEffect(() => {
        setLoading(true);
        const timer = setTimeout(() => fetchPorts(), 300); // debounce search
        return () => clearTimeout(timer);
    }, [fetchPorts]);

    const regionButtons = [
        { label: '🌍 All', value: '' },
        { label: '🇮🇳 India', value: 'India' },
        { label: '🌏 Asia Pacific', value: 'Asia Pacific' },
        { label: '🇪🇺 Europe', value: 'Europe' },
        { label: '🌎 Americas', value: 'America' },
        { label: '🌍 Middle East', value: 'Middle East' },
    ];

    const getTypeIcon = (type) => {
        switch (type) {
            case 'port': return '🚢';
            case 'manufacturing': return '🏭';
            case 'hub': return '📦';
            default: return '📍';
        }
    };

    const getTypeBadgeClass = (type) => {
        switch (type) {
            case 'port': return 'port-type-badge port-type-port';
            case 'manufacturing': return 'port-type-badge port-type-manufacturing';
            case 'hub': return 'port-type-badge port-type-hub';
            default: return 'port-type-badge';
        }
    };

    return (
        <>
            {/* Header */}
            <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
                    <div>
                        <h2 style={{ margin: 0 }}>🚢 Port & Hub Monitor</h2>
                        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', margin: 'var(--space-1) 0 0' }}>
                            Search and monitor supply chain ports, hubs & manufacturing centers worldwide
                        </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                        <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{ports.length}</span> ports found
                    </div>
                </div>
            </div>

            {/* Search & Filters */}
            <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
                {/* Search Input */}
                <div className="port-search-container">
                    <svg className="port-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <input
                        type="text"
                        className="port-search-input"
                        placeholder="Search ports by name, region, or type... (e.g. Mumbai, India, port)"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    {search && (
                        <button className="port-search-clear" onClick={() => setSearch('')}>✕</button>
                    )}
                </div>

                {/* Region Filter Buttons */}
                <div className="port-filter-row">
                    {regionButtons.map(btn => (
                        <button
                            key={btn.value}
                            className={`port-filter-btn ${regionFilter === btn.value ? 'active' : ''}`}
                            onClick={() => setRegionFilter(btn.value)}
                        >
                            {btn.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Port Cards Grid */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-muted)' }}>
                    Loading ports...
                </div>
            ) : ports.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
                    <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🔍</div>
                    <h3 style={{ color: 'var(--color-text-secondary)' }}>No ports found</h3>
                    <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                        Try a different search term or clear the filters
                    </p>
                </div>
            ) : (
                <div className="port-cards-grid">
                    {ports.map((port, idx) => (
                        <div className="port-card" key={idx}>
                            <div className="port-card-header">
                                <div>
                                    <h3 className="port-card-name">
                                        {getTypeIcon(port.type)} {port.name}
                                    </h3>
                                    <p className="port-card-region">{port.region}</p>
                                </div>
                                <span className={getTypeBadgeClass(port.type)}>
                                    {port.type}
                                </span>
                            </div>

                            <div className="port-card-coords">
                                <span>📍 {port.lat.toFixed(2)}°, {port.lon.toFixed(2)}°</span>
                            </div>

                            {port.weather ? (
                                <div className="port-weather-section">
                                    <div className="port-weather-main">
                                        <span className="port-weather-temp">
                                            🌡️ {port.weather.temp_c ? `${port.weather.temp_c}°C` : 'N/A'}
                                        </span>
                                        <span className="port-weather-desc">
                                            {port.weather.description || port.weather.condition || 'Clear'}
                                        </span>
                                    </div>
                                    {port.weather.wind_speed && (
                                        <div className="port-weather-detail">
                                            💨 Wind: {port.weather.wind_speed} m/s
                                        </div>
                                    )}
                                    {port.weather.humidity && (
                                        <div className="port-weather-detail">
                                            💧 Humidity: {port.weather.humidity}%
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="port-weather-section">
                                    <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                        ⏳ Weather data loading...
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}

export default PortMonitor;
