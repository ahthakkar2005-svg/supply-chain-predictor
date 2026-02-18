import { useState, useEffect, useCallback } from 'react';
import { dashboardAPI, predictionsAPI, mockData } from '../services/api';

/**
 * Custom hook for fetching dashboard data with WebSocket real-time updates
 * Falls back to HTTP polling if WebSocket is unavailable
 */
export function useDashboardData(webSocket = null) {
    const [data, setData] = useState({
        summary: null,
        regions: [],
        alerts: [],
        news: [],
        timeSeries: [],
        metrics: [],
        suppliers: [],
        loading: true,
        error: null,
    });

    const fetchAllData = useCallback(async () => {
        setData(prev => ({ ...prev, loading: true, error: null }));

        try {
            // Try to fetch from API, fall back to mock data
            const [summary, regions, alerts, news, timeSeries, metrics, suppliers] = await Promise.all([
                dashboardAPI.getSummary().catch(() => mockData.summary),
                dashboardAPI.getRegions().catch(() => mockData.regions),
                dashboardAPI.getAlerts().catch(() => mockData.alerts),
                dashboardAPI.getNews().catch(() => mockData.news),
                dashboardAPI.getTimeSeries().catch(() => mockData.timeSeries),
                dashboardAPI.getMetrics().catch(() => mockData.metrics),
                dashboardAPI.getSuppliers().catch(() => mockData.suppliers),
            ]);

            setData({
                summary,
                regions,
                alerts,
                news,
                timeSeries,
                metrics,
                suppliers,
                loading: false,
                error: null,
            });
        } catch (error) {
            // Use mock data on complete failure
            setData({
                summary: mockData.summary,
                regions: mockData.regions,
                alerts: mockData.alerts,
                news: mockData.news,
                timeSeries: mockData.timeSeries,
                metrics: mockData.metrics,
                suppliers: mockData.suppliers,
                loading: false,
                error: null,
            });
        }
    }, []);

    // Subscribe to WebSocket real-time updates
    useEffect(() => {
        if (!webSocket) return;

        const unsubs = [];

        // Handle full snapshot from WebSocket
        unsubs.push(webSocket.on('snapshot', (snapshot) => {
            if (!snapshot) return;
            setData(prev => ({
                ...prev,
                summary: snapshot.summary || prev.summary,
                regions: snapshot.regions || prev.regions,
                alerts: snapshot.alerts || prev.alerts,
                news: snapshot.news || prev.news,
                metrics: snapshot.metrics || prev.metrics,
                suppliers: snapshot.suppliers || prev.suppliers,
                loading: false,
            }));
        }));

        // Handle incremental risk updates
        unsubs.push(webSocket.on('risk_update', (update) => {
            if (!update) return;
            setData(prev => ({
                ...prev,
                summary: prev.summary ? { ...prev.summary, ...update } : update,
            }));
        }));

        // Handle metrics updates
        unsubs.push(webSocket.on('metrics_update', (update) => {
            if (!update?.metrics) return;
            setData(prev => ({
                ...prev,
                metrics: update.metrics,
            }));
        }));

        // Handle region updates
        unsubs.push(webSocket.on('region_update', (update) => {
            if (!update?.regions) return;
            setData(prev => ({
                ...prev,
                regions: update.regions,
            }));
        }));

        // Handle new news articles
        unsubs.push(webSocket.on('new_news', (update) => {
            if (!update?.articles) return;
            setData(prev => ({
                ...prev,
                news: [...update.articles, ...prev.news].slice(0, 50),
            }));
        }));

        // Handle weather alerts
        unsubs.push(webSocket.on('weather_alert', (update) => {
            if (!update?.alerts) return;
            setData(prev => ({
                ...prev,
                alerts: [...update.alerts, ...prev.alerts].slice(0, 20),
                summary: prev.summary ? {
                    ...prev.summary,
                    total_active_alerts: (prev.summary.total_active_alerts || 0) + update.alerts.length,
                } : prev.summary,
            }));
        }));

        return () => unsubs.forEach(unsub => unsub());
    }, [webSocket]);

    // Initial HTTP fetch + fallback polling only when WebSocket is NOT connected
    useEffect(() => {
        fetchAllData();

        // Only poll if no WebSocket is connected
        if (!webSocket?.isConnected) {
            const interval = setInterval(fetchAllData, 30000);
            return () => clearInterval(interval);
        }
    }, [fetchAllData, webSocket?.isConnected]);

    return { ...data, refresh: fetchAllData };
}

/**
 * Custom hook for risk assessment
 */
export function useRiskAssessment() {
    const [assessment, setAssessment] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchAssessment() {
            try {
                const data = await predictionsAPI.getRiskAssessment();
                setAssessment(data);
            } catch (error) {
                // Generate mock assessment
                setAssessment({
                    overall_risk: {
                        score: 0.58,
                        level: 'medium',
                        confidence: 0.82,
                        trend: 'stable',
                    },
                    contributing_factors: [
                        'Elevated geopolitical tensions in key manufacturing regions',
                        'Seasonal shipping capacity constraints',
                        'Rising raw material costs',
                    ],
                    recommendations: [
                        '📊 Increase monitoring frequency',
                        '📋 Review supplier risk assessments',
                        '🔍 Conduct scenario planning exercises',
                    ],
                });
            } finally {
                setLoading(false);
            }
        }

        fetchAssessment();
    }, []);

    return { assessment, loading };
}

/**
 * Custom hook for forecast data
 */
export function useForecast(days = 30) {
    const [forecast, setForecast] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchForecast() {
            try {
                const data = await predictionsAPI.getForecast(days);
                setForecast(data.forecast);
            } catch (error) {
                // Generate mock forecast
                const mockForecast = Array.from({ length: days }, (_, i) => {
                    const date = new Date();
                    date.setDate(date.getDate() + i + 1);
                    return {
                        date: date.toISOString().split('T')[0],
                        risk_score: Math.min(1, Math.max(0, 0.5 + Math.sin(i / 7) * 0.2 + (Math.random() - 0.5) * 0.1)),
                        confidence: Math.max(0.5, 0.95 - i * 0.012),
                        risk_level: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
                    };
                });
                setForecast(mockForecast);
            } finally {
                setLoading(false);
            }
        }

        fetchForecast();
    }, [days]);

    return { forecast, loading };
}
