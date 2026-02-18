import React from 'react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';

/**
 * Custom Tooltip for Charts
 */
function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;

    return (
        <div style={{
            background: 'var(--gradient-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3)',
            backdropFilter: 'blur(10px)',
        }}>
            <p style={{ color: 'var(--color-text-primary)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                {label}
            </p>
            {payload.map((entry, index) => (
                <p key={index} style={{ color: entry.color, fontSize: 'var(--font-size-sm)' }}>
                    {entry.name}: {(entry.value * 100).toFixed(1)}%
                </p>
            ))}
        </div>
    );
}

/**
 * Risk Trend Chart Component
 * Displays historical risk data over time
 */
export function RiskTrendChart({ data = [], height = 300 }) {
    if (data.length === 0) {
        return (
            <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <p style={{ color: 'var(--color-text-muted)' }}>Loading chart data...</p>
            </div>
        );
    }

    return (
        <div className="chart-container" style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="overallRiskGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="logisticsGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="supplierGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f472b6" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#f472b6" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis
                        dataKey="date"
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        tickFormatter={(value) => value.split('-').slice(1).join('/')}
                    />
                    <YAxis
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        domain={[0, 1]}
                        tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        wrapperStyle={{ paddingTop: '10px' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="overall_risk"
                        name="Overall Risk"
                        stroke="#6366f1"
                        strokeWidth={2}
                        fill="url(#overallRiskGradient)"
                    />
                    <Area
                        type="monotone"
                        dataKey="logistics_risk"
                        name="Logistics"
                        stroke="#22d3ee"
                        strokeWidth={2}
                        fill="url(#logisticsGradient)"
                    />
                    <Area
                        type="monotone"
                        dataKey="supplier_risk"
                        name="Suppliers"
                        stroke="#f472b6"
                        strokeWidth={2}
                        fill="url(#supplierGradient)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}

/**
 * Forecast Chart Component
 * Displays future risk predictions
 */
export function ForecastChart({ data = [], height = 250 }) {
    if (data.length === 0) {
        return (
            <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <p style={{ color: 'var(--color-text-muted)' }}>Loading forecast...</p>
            </div>
        );
    }

    return (
        <div className="chart-container" style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis
                        dataKey="date"
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        tickFormatter={(value) => value.split('-').slice(1).join('/')}
                    />
                    <YAxis
                        stroke="var(--color-text-muted)"
                        fontSize={12}
                        domain={[0, 1]}
                        tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                        type="monotone"
                        dataKey="risk_score"
                        name="Predicted Risk"
                        stroke="#ffa502"
                        strokeWidth={2}
                        dot={{ fill: '#ffa502', strokeWidth: 2 }}
                        activeDot={{ r: 6, stroke: '#ffa502', strokeWidth: 2 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="confidence"
                        name="Confidence"
                        stroke="#26de81"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

export default RiskTrendChart;
