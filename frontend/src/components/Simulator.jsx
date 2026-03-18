import React, { useState } from 'react';

const API_BASE_URL = 'http://localhost:8000/api';

const PORTS = [
    "Shanghai", "Singapore", "Rotterdam", "Los Angeles", "Hamburg",
    "Shenzhen", "Dubai", "New York", "Mumbai (JNPT)", "Chennai",
    "Delhi NCR", "Kolkata", "Mundra (Gujarat)", "Visakhapatnam",
    "Bandar Abbas", "Jeddah", "Busan", "Kaohsiung"
];

export const Simulator = () => {
    const [activeTab, setActiveTab] = useState('route');
    
    // Route State
    const [originPort, setOriginPort] = useState('Mundra (Gujarat)');
    const [destinationPort, setDestinationPort] = useState('Dubai');
    const [cargoValue, setCargoValue] = useState(100000);
    const [routeResult, setRouteResult] = useState(null);
    const [routeLoading, setRouteLoading] = useState(false);
    
    // Scenario State
    const [scenarioInput, setScenarioInput] = useState({
        news_sentiment: 0.5,
        news_volume: 0.5,
        historical_pattern: 0.5,
        supplier_concentration: 0.5,
        geopolitical_index: 0.5,
        market_volatility: 0.5
    });
    const [scenarioResult, setScenarioResult] = useState(null);
    const [scenarioLoading, setScenarioLoading] = useState(false);

    const handleRouteSubmit = async (e) => {
        e.preventDefault();
        setRouteLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/predictions/route-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    origin_port: originPort,
                    destination_port: destinationPort,
                    cargo_value: Number(cargoValue)
                })
            });
            const data = await res.json();
            setRouteResult(data);
        } catch (error) {
            console.error('Failed to calculate route:', error);
        } finally {
            setRouteLoading(false);
        }
    };

    const handleScenarioChange = (e) => {
        const { name, value } = e.target;
        setScenarioInput(prev => ({
            ...prev,
            [name]: parseFloat(value)
        }));
    };

    const handleScenarioSubmit = async (e) => {
        e.preventDefault();
        setScenarioLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/predictions/scenario`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(scenarioInput)
            });
            const data = await res.json();
            setScenarioResult(data);
        } catch (error) {
            console.error('Failed to simulate scenario:', error);
        } finally {
            setScenarioLoading(false);
        }
    };

    return (
        <div className="card full-width">
            <div className="card-header">
                <h3 className="card-title">Interactive AI Simulators</h3>
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <button 
                        className={`btn ${activeTab === 'route' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('route')}
                    >
                        Route & Logistics
                    </button>
                    <button 
                        className={`btn ${activeTab === 'scenario' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('scenario')}
                    >
                        "What-If" Scenarios
                    </button>
                </div>
            </div>
            
            <div style={{ padding: 'var(--space-4)' }}>
                {activeTab === 'route' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: 'var(--space-6)' }}>
                        <form onSubmit={handleRouteSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Origin Port</label>
                                <select 
                                    value={originPort}
                                    onChange={e => setOriginPort(e.target.value)}
                                    style={{ width: '100%', padding: 'var(--space-2)', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', color: 'white', borderRadius: 'var(--radius-sm)' }}
                                >
                                    {PORTS.map(p => <option key={`orig-${p}`} value={p}>{p}</option>)}
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Destination Port</label>
                                <select 
                                    value={destinationPort}
                                    onChange={e => setDestinationPort(e.target.value)}
                                    style={{ width: '100%', padding: 'var(--space-2)', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', color: 'white', borderRadius: 'var(--radius-sm)' }}
                                >
                                    {PORTS.map(p => <option key={`dest-${p}`} value={p}>{p}</option>)}
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Estimated Cargo Value (USD)</label>
                                <input 
                                    type="number" 
                                    value={cargoValue}
                                    onChange={e => setCargoValue(e.target.value)}
                                    style={{ width: '100%', padding: 'var(--space-2)', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', color: 'white', borderRadius: 'var(--radius-sm)' }}
                                />
                            </div>
                            <button type="submit" className="btn btn-primary" disabled={routeLoading} style={{ marginTop: 'var(--space-2)' }}>
                                {routeLoading ? 'Calculating...' : 'Calculate Logistics'}
                            </button>
                        </form>
                        
                        <div style={{ background: 'var(--color-bg-secondary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                            <h4 style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-primary)' }}>Route Analysis Results</h4>
                            {routeResult ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                                        <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Distance</div>
                                            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'bold' }}>{routeResult.distance_km.toLocaleString()} km</div>
                                        </div>
                                        <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Final ETA</div>
                                            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'bold', color: routeResult.predicted_delay_days > 0 ? 'var(--color-warning)' : 'var(--color-success)' }}>
                                                {routeResult.final_eta_days} Days
                                            </div>
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                                                Base: {routeResult.base_transit_days}d + {routeResult.predicted_delay_days}d delay
                                            </div>
                                        </div>
                                        <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Total Cost Expected</div>
                                            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'bold' }}>${routeResult.final_cost_usd.toLocaleString()}</div>
                                        </div>
                                        <div style={{ background: 'var(--color-bg-tertiary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Risk Level</div>
                                            <span className={`badge ${routeResult.risk_level}`}>{routeResult.risk_level.toUpperCase()}</span>
                                        </div>
                                    </div>
                                    {routeResult.delay_factors.length > 0 && (
                                        <div>
                                            <h5 style={{ marginBottom: 'var(--space-2)', color: 'var(--color-warning)' }}>Identified Disruption Factors</h5>
                                            <ul style={{ paddingLeft: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                                                {routeResult.delay_factors.map((df, i) => <li key={i}>{df}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                    {routeResult.recommendations.length > 0 && (
                                        <div style={{ marginTop: 'var(--space-2)' }}>
                                            <h5 style={{ marginBottom: 'var(--space-2)', color: 'var(--color-info)' }}>AI Recommendations</h5>
                                            <ul style={{ paddingLeft: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                                                {routeResult.recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: 'var(--space-8) 0' }}>
                                    Enter origin and destination ports to calculate route mechanics.
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: 'var(--space-6)' }}>
                        <form onSubmit={handleScenarioSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                            {Object.entries(scenarioInput).map(([key, val]) => (
                                <div key={key}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                                        <label style={{ fontSize: 'var(--font-size-sm)', textTransform: 'capitalize' }}>
                                            {key.replace(/_/g, ' ')}
                                        </label>
                                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{val}</span>
                                    </div>
                                    <input 
                                        type="range" 
                                        name={key}
                                        min="0" max="1" step="0.1"
                                        value={val}
                                        onChange={handleScenarioChange}
                                        style={{ width: '100%', accentColor: 'var(--color-primary)' }}
                                    />
                                </div>
                            ))}
                            <button type="submit" className="btn btn-primary" disabled={scenarioLoading} style={{ marginTop: 'var(--space-2)' }}>
                                {scenarioLoading ? 'Simulating...' : 'Run Scenario'}
                            </button>
                        </form>

                        <div style={{ background: 'var(--color-bg-secondary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                            <h4 style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-primary)' }}>Simulation Outcome</h4>
                            {scenarioResult ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--color-bg-tertiary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)' }}>
                                        <div>
                                            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>Simulated Risk Score</div>
                                            <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'bold' }}>{(scenarioResult.risk_score * 100).toFixed(1)}%</div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>Outcome Level</div>
                                            <span className={`badge ${scenarioResult.risk_level}`} style={{ fontSize: 'var(--font-size-lg)' }}>
                                                {scenarioResult.risk_level.toUpperCase()}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    {scenarioResult.recommendations && scenarioResult.recommendations.length > 0 && (
                                        <div style={{ marginTop: 'var(--space-2)' }}>
                                            <h5 style={{ marginBottom: 'var(--space-2)', color: 'var(--color-info)' }}>AI Mitigation Recommendations</h5>
                                            <ul style={{ paddingLeft: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                                                {scenarioResult.recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: 'var(--space-8) 0' }}>
                                    Adjust hypothetical risk parameters to simulate multi-variable disruptions.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
