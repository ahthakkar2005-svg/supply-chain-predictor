import React from 'react';

/**
 * Region Map Component
 * Interactive map showing global supply chain risks
 * Uses a simplified SVG world map for the MVP
 */
export function RegionMap({ regions = [] }) {
    // Region coordinates for the simplified map
    const regionPositions = {
        'NA': { x: 120, y: 120, name: 'North America' },
        'EU': { x: 340, y: 100, name: 'Europe' },
        'APAC': { x: 500, y: 150, name: 'Asia Pacific' },
        'SA': { x: 430, y: 170, name: 'South Asia (India)' },
        'LATAM': { x: 180, y: 250, name: 'Latin America' },
        'MEA': { x: 380, y: 200, name: 'Middle East & Africa' },
    };

    const getRiskColor = (score) => {
        if (score >= 0.85) return 'var(--color-risk-critical)';
        if (score >= 0.7) return 'var(--color-risk-high)';
        if (score >= 0.4) return 'var(--color-risk-medium)';
        return 'var(--color-risk-low)';
    };

    const getMarkerSize = (score) => {
        return 20 + score * 25;
    };

    return (
        <div className="map-container" style={{ background: 'linear-gradient(180deg, #0a1628 0%, #1a2744 100%)' }}>
            <svg
                viewBox="0 0 600 350"
                style={{ width: '100%', height: '100%' }}
            >
                {/* Simplified world map background */}
                <defs>
                    <radialGradient id="glowGradient" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stopColor="rgba(99, 102, 241, 0.3)" />
                        <stop offset="100%" stopColor="transparent" />
                    </radialGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Grid lines for tech feel */}
                {[...Array(12)].map((_, i) => (
                    <line
                        key={`h-${i}`}
                        x1="0" y1={i * 30} x2="600" y2={i * 30}
                        stroke="rgba(99, 102, 241, 0.1)"
                        strokeWidth="0.5"
                    />
                ))}
                {[...Array(20)].map((_, i) => (
                    <line
                        key={`v-${i}`}
                        x1={i * 30} y1="0" x2={i * 30} y2="350"
                        stroke="rgba(99, 102, 241, 0.1)"
                        strokeWidth="0.5"
                    />
                ))}

                {/* Continents simplified shapes */}
                <path
                    d="M80,80 L160,70 L180,100 L170,150 L130,160 L100,140 L80,100 Z"
                    fill="rgba(99, 102, 241, 0.15)"
                    stroke="rgba(99, 102, 241, 0.3)"
                    strokeWidth="1"
                />
                <path
                    d="M140,180 L200,160 L220,200 L200,280 L160,290 L130,250 L140,200 Z"
                    fill="rgba(99, 102, 241, 0.15)"
                    stroke="rgba(99, 102, 241, 0.3)"
                    strokeWidth="1"
                />
                <path
                    d="M300,70 L400,60 L420,100 L400,150 L350,160 L300,140 L290,100 Z"
                    fill="rgba(99, 102, 241, 0.15)"
                    stroke="rgba(99, 102, 241, 0.3)"
                    strokeWidth="1"
                />
                <path
                    d="M340,160 L420,150 L440,200 L400,280 L350,270 L330,220 Z"
                    fill="rgba(99, 102, 241, 0.15)"
                    stroke="rgba(99, 102, 241, 0.3)"
                    strokeWidth="1"
                />
                <path
                    d="M440,80 L560,60 L580,120 L560,200 L480,210 L450,160 L440,100 Z"
                    fill="rgba(99, 102, 241, 0.15)"
                    stroke="rgba(99, 102, 241, 0.3)"
                    strokeWidth="1"
                />
                {/* Indian subcontinent */}
                <path
                    d="M420,140 L445,130 L455,150 L450,180 L435,195 L425,175 L420,155 Z"
                    fill="rgba(255, 165, 2, 0.2)"
                    stroke="rgba(255, 165, 2, 0.4)"
                    strokeWidth="1"
                />

                {/* Region markers */}
                {regions.map((region) => {
                    const pos = regionPositions[region.region_code];
                    if (!pos) return null;

                    const color = getRiskColor(region.risk_score);
                    const size = getMarkerSize(region.risk_score);

                    return (
                        <g key={region.region_code} style={{ cursor: 'pointer' }}>
                            {/* Glow effect */}
                            <circle
                                cx={pos.x}
                                cy={pos.y}
                                r={size + 10}
                                fill={color}
                                opacity={0.2}
                                filter="url(#glow)"
                            />

                            {/* Pulse animation ring */}
                            <circle
                                cx={pos.x}
                                cy={pos.y}
                                r={size}
                                fill="none"
                                stroke={color}
                                strokeWidth="2"
                                opacity="0.5"
                            >
                                <animate
                                    attributeName="r"
                                    from={size}
                                    to={size + 20}
                                    dur="2s"
                                    repeatCount="indefinite"
                                />
                                <animate
                                    attributeName="opacity"
                                    from="0.5"
                                    to="0"
                                    dur="2s"
                                    repeatCount="indefinite"
                                />
                            </circle>

                            {/* Main marker */}
                            <circle
                                cx={pos.x}
                                cy={pos.y}
                                r={size}
                                fill={color}
                                opacity={0.9}
                                stroke="white"
                                strokeWidth="2"
                            />

                            {/* Risk percentage */}
                            <text
                                x={pos.x}
                                y={pos.y + 4}
                                textAnchor="middle"
                                fill="white"
                                fontSize="12"
                                fontWeight="bold"
                            >
                                {Math.round(region.risk_score * 100)}%
                            </text>

                            {/* Region label */}
                            <text
                                x={pos.x}
                                y={pos.y + size + 18}
                                textAnchor="middle"
                                fill="var(--color-text-secondary)"
                                fontSize="11"
                                fontWeight="500"
                            >
                                {pos.name}
                            </text>

                            {/* Active alerts indicator */}
                            {region.active_alerts > 0 && (
                                <>
                                    <circle
                                        cx={pos.x + size - 5}
                                        cy={pos.y - size + 5}
                                        r="10"
                                        fill="var(--color-risk-critical)"
                                    />
                                    <text
                                        x={pos.x + size - 5}
                                        y={pos.y - size + 9}
                                        textAnchor="middle"
                                        fill="white"
                                        fontSize="10"
                                        fontWeight="bold"
                                    >
                                        {region.active_alerts}
                                    </text>
                                </>
                            )}
                        </g>
                    );
                })}

                {/* Legend */}
                <g transform="translate(20, 290)">
                    <text fill="var(--color-text-muted)" fontSize="10" y="0">Risk Levels:</text>
                    {[
                        { label: 'Critical', color: 'var(--color-risk-critical)' },
                        { label: 'High', color: 'var(--color-risk-high)' },
                        { label: 'Medium', color: 'var(--color-risk-medium)' },
                        { label: 'Low', color: 'var(--color-risk-low)' },
                    ].map((item, i) => (
                        <g key={item.label} transform={`translate(${i * 70}, 15)`}>
                            <circle cx="6" cy="6" r="6" fill={item.color} />
                            <text x="16" y="10" fill="var(--color-text-muted)" fontSize="10">{item.label}</text>
                        </g>
                    ))}
                </g>
            </svg>
        </div>
    );
}

export default RegionMap;
