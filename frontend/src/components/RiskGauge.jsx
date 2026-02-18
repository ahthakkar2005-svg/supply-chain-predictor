import React from 'react';

/**
 * Animated Risk Gauge Component
 * Displays overall risk level with circular progress indicator
 */
export function RiskGauge({ score = 0, size = 180, label = "Risk Score" }) {
    // Ensure score is between 0 and 1
    const normalizedScore = Math.max(0, Math.min(1, score));
    const percentage = Math.round(normalizedScore * 100);

    // Determine color based on risk level
    const getColor = () => {
        if (normalizedScore >= 0.85) return 'var(--color-risk-critical)';
        if (normalizedScore >= 0.7) return 'var(--color-risk-high)';
        if (normalizedScore >= 0.4) return 'var(--color-risk-medium)';
        return 'var(--color-risk-low)';
    };

    const getRiskLevel = () => {
        if (normalizedScore >= 0.85) return 'CRITICAL';
        if (normalizedScore >= 0.7) return 'HIGH';
        if (normalizedScore >= 0.4) return 'MEDIUM';
        return 'LOW';
    };

    const color = getColor();
    const riskLevel = getRiskLevel();

    return (
        <div className="risk-gauge">
            <div
                className="gauge-circle"
                style={{
                    '--gauge-value': percentage,
                    '--gauge-color': color,
                    width: size,
                    height: size,
                }}
            >
                <div style={{ textAlign: 'center' }}>
                    <div className="gauge-value" style={{ color }}>{percentage}%</div>
                    <div className="gauge-label" style={{ color }}>{riskLevel}</div>
                </div>
            </div>
            <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                {label}
            </p>
        </div>
    );
}

/**
 * Risk Badge Component
 */
export function RiskBadge({ level }) {
    const normalizedLevel = level?.toLowerCase() || 'low';
    return (
        <span className={`badge ${normalizedLevel}`}>
            {normalizedLevel}
        </span>
    );
}

/**
 * Trend Indicator Component
 */
export function TrendIndicator({ trend, value }) {
    const isUp = trend === 'up';
    const isDown = trend === 'down';

    return (
        <span className={`metric-change ${trend}`}>
            {isUp && '↑'}
            {isDown && '↓'}
            {!isUp && !isDown && '→'}
            {value !== undefined && ` ${Math.abs(value).toFixed(1)}%`}
        </span>
    );
}

export default RiskGauge;
