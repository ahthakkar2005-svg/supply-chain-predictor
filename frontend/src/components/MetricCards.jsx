import React from 'react';
import { RiskBadge, TrendIndicator } from './RiskGauge';

/**
 * Metric Card Component
 */
export function MetricCard({ label, value, sublabel, trend, changePercent, riskLevel, icon }) {
    const getRiskClass = () => {
        const level = riskLevel?.toLowerCase();
        if (level === 'critical') return 'risk-critical';
        if (level === 'high') return 'risk-high';
        if (level === 'medium') return 'risk-medium';
        if (level === 'low') return 'risk-low';
        return '';
    };

    const cardClass = riskLevel?.toLowerCase() || '';

    return (
        <div className={`metric-card ${cardClass} animate-fadeIn`}>
            <div className="metric-label">{label}</div>
            <div className={`metric-value ${getRiskClass()}`}>
                {typeof value === 'number' ?
                    (value <= 1 ? `${Math.round(value * 100)}%` : value) :
                    value
                }
            </div>
            {sublabel && (
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>
                    {sublabel}
                </div>
            )}
            {(trend || changePercent !== undefined) && (
                <TrendIndicator trend={trend} value={changePercent} />
            )}
        </div>
    );
}

/**
 * Metrics Grid Component
 * Displays key metrics in a responsive grid
 */
export function MetricsGrid({ summary }) {
    if (!summary) {
        return (
            <div className="metrics-grid">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="metric-card">
                        <div className="skeleton" style={{ height: 16, width: 100, marginBottom: 8 }} />
                        <div className="skeleton" style={{ height: 48, width: 80, marginBottom: 8 }} />
                        <div className="skeleton" style={{ height: 14, width: 60 }} />
                    </div>
                ))}
            </div>
        );
    }

    return (
        <div className="metrics-grid">
            <MetricCard
                label="Overall Risk Score"
                value={summary.overall_risk_score}
                sublabel={summary.overall_risk_level?.toUpperCase()}
                trend={summary.risk_trend}
                riskLevel={summary.overall_risk_level}
            />
            <MetricCard
                label="Active Alerts"
                value={summary.total_active_alerts}
                sublabel={`${summary.critical_alerts} Critical, ${summary.high_alerts} High`}
                riskLevel={summary.critical_alerts > 0 ? 'critical' : summary.high_alerts > 0 ? 'high' : 'medium'}
            />
            <MetricCard
                label="Regions at Risk"
                value={summary.regions_at_risk}
                sublabel="of 5 regions"
                riskLevel={summary.regions_at_risk > 3 ? 'high' : summary.regions_at_risk > 1 ? 'medium' : 'low'}
            />
            <MetricCard
                label="Prediction Accuracy"
                value={summary.predictions_accuracy}
                sublabel="30-day rolling average"
                riskLevel="low"
            />
        </div>
    );
}

/**
 * Category Risk Table Component
 */
export function CategoryRiskTable({ metrics = [] }) {
    if (metrics.length === 0) {
        return (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                Loading metrics...
            </div>
        );
    }

    const getRiskLevel = (score) => {
        if (score >= 0.7) return 'high';
        if (score >= 0.4) return 'medium';
        return 'low';
    };

    return (
        <table className="data-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Risk Score</th>
                    <th>Trend</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {metrics.map((metric, index) => (
                    <tr key={index} className="animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                        <td style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>
                            {metric.category}
                        </td>
                        <td>{Math.round(metric.current_score * 100)}%</td>
                        <td>
                            <TrendIndicator trend={metric.trend} value={metric.change_percent} />
                        </td>
                        <td>
                            <RiskBadge level={getRiskLevel(metric.current_score)} />
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

/**
 * Supplier Risk Table Component
 */
export function SupplierTable({ suppliers = [] }) {
    if (suppliers.length === 0) {
        return (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                Loading suppliers...
            </div>
        );
    }

    const getRiskLevel = (score) => {
        if (score >= 0.7) return 'high';
        if (score >= 0.4) return 'medium';
        return 'low';
    };

    return (
        <table className="data-table">
            <thead>
                <tr>
                    <th>Supplier</th>
                    <th>Region</th>
                    <th>Tier</th>
                    <th>Risk</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {suppliers.slice(0, 8).map((supplier, index) => (
                    <tr key={supplier.id || index} className="animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                        <td style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>
                            {supplier.name}
                            {supplier.is_critical && (
                                <span style={{ marginLeft: 'var(--space-2)', color: 'var(--color-risk-critical)', fontSize: 'var(--font-size-xs)' }}>
                                    ★ Critical
                                </span>
                            )}
                        </td>
                        <td>{supplier.region}</td>
                        <td>Tier {supplier.tier}</td>
                        <td>{Math.round(supplier.risk_score * 100)}%</td>
                        <td>
                            <RiskBadge level={getRiskLevel(supplier.risk_score)} />
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export default MetricsGrid;
