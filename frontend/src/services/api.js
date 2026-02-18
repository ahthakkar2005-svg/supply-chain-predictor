/**
 * API Service for Supply Chain Predictor
 * Handles all backend communication
 */

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        throw error;
    }
}

// Dashboard API
export const dashboardAPI = {
    getSummary: () => fetchAPI('/dashboard/summary'),
    getRegions: () => fetchAPI('/dashboard/regions'),
    getMetrics: () => fetchAPI('/dashboard/metrics'),
    getTimeSeries: (days = 30) => fetchAPI(`/dashboard/time-series?days=${days}`),
    getPredictions: (limit = 10) => fetchAPI(`/dashboard/predictions?limit=${limit}`),
    getAlerts: (unreadOnly = false) => fetchAPI(`/dashboard/alerts?unread_only=${unreadOnly}`),
    getSuppliers: (limit = 15) => fetchAPI(`/dashboard/suppliers?limit=${limit}`),
    getNews: (limit = 20) => fetchAPI(`/dashboard/news?limit=${limit}`),
    markAlertRead: (alertId) => fetchAPI(`/dashboard/alerts/${alertId}/read`, { method: 'POST' }),
    acknowledgeAlert: (alertId) => fetchAPI(`/dashboard/alerts/${alertId}/acknowledge`, { method: 'POST' }),
    refreshData: () => fetchAPI('/dashboard/refresh', { method: 'POST' }),
};

// Predictions API
export const predictionsAPI = {
    getForecast: (days = 30) => fetchAPI(`/predictions/forecast?days=${days}`),
    analyzeText: (text) => fetchAPI('/predictions/analyze-text', {
        method: 'POST',
        body: JSON.stringify({ text }),
    }),
    getRiskAssessment: () => fetchAPI('/predictions/risk-assessment'),
    getDisruptionTypes: () => fetchAPI('/predictions/disruption-types'),
    getRegionalBreakdown: () => fetchAPI('/predictions/regional-breakdown'),
};

// Mock data for development when API is not available
export const mockData = {
    summary: {
        overall_risk_score: 0.62,
        overall_risk_level: 'medium',
        risk_trend: 'up',
        total_active_alerts: 5,
        critical_alerts: 1,
        high_alerts: 2,
        regions_at_risk: 3,
        predictions_accuracy: 0.87,
        last_updated: new Date().toISOString(),
    },
    regions: [
        { region_code: 'APAC', region_name: 'Asia Pacific', lat: 35.0, lng: 105.0, risk_score: 0.78, risk_level: 'high', active_alerts: 3, top_risks: ['Semiconductor shortage', 'Port congestion'] },
        { region_code: 'EU', region_name: 'Europe', lat: 50.0, lng: 10.0, risk_score: 0.52, risk_level: 'medium', active_alerts: 2, top_risks: ['Energy costs', 'Labor disputes'] },
        { region_code: 'NA', region_name: 'North America', lat: 40.0, lng: -100.0, risk_score: 0.35, risk_level: 'low', active_alerts: 1, top_risks: ['Transportation delays'] },
        { region_code: 'LATAM', region_name: 'Latin America', lat: -15.0, lng: -60.0, risk_score: 0.48, risk_level: 'medium', active_alerts: 1, top_risks: ['Weather events', 'Currency volatility'] },
        { region_code: 'MEA', region_name: 'Middle East & Africa', lat: 25.0, lng: 45.0, risk_score: 0.55, risk_level: 'medium', active_alerts: 2, top_risks: ['Geopolitical tensions'] },
    ],
    alerts: [
        { id: '1', title: 'Critical: Semiconductor Supply Risk - Asia Pacific', message: 'AI models predict 87% probability of significant semiconductor supply disruption in the next 14 days.', risk_level: 'critical', region: 'Asia Pacific', is_read: false, created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
        { id: '2', title: 'High: Port Congestion Alert - Europe', message: 'Rotterdam and Hamburg ports experiencing severe congestion. Container delays expected for 3-4 weeks.', risk_level: 'high', region: 'Europe', is_read: false, created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString() },
        { id: '3', title: 'Medium: Raw Material Price Volatility', message: 'Commodity prices showing unusual volatility. Procurement teams advised to review hedging strategies.', risk_level: 'medium', region: 'North America', is_read: true, created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString() },
        { id: '4', title: 'High: Weather Alert - Latin America', message: 'La Niña conditions strengthening. Agricultural and mining supply chains at elevated risk.', risk_level: 'high', region: 'Latin America', is_read: false, created_at: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString() },
        { id: '5', title: 'Medium: Supplier Financial Health Warning', message: '3 tier-2 suppliers showing signs of financial distress. Alternative sourcing recommended.', risk_level: 'medium', region: 'Europe', is_read: true, created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() },
    ],
    news: [
        { id: '1', title: 'Typhoon disrupts shipping routes in Asia Pacific, delays expected for 2+ weeks', source: 'Reuters', sentiment_score: -0.7, published_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(), region: 'Asia Pacific' },
        { id: '2', title: 'New tariffs imposed on semiconductor imports, prices expected to surge', source: 'Bloomberg', sentiment_score: -0.5, published_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), region: 'North America' },
        { id: '3', title: 'Port congestion at Rotterdam reaching critical levels', source: 'Financial Times', sentiment_score: -0.6, published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(), region: 'Europe' },
        { id: '4', title: 'Major electronics manufacturer announces expansion plans', source: 'WSJ', sentiment_score: 0.4, published_at: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(), region: 'Asia Pacific' },
        { id: '5', title: 'Supply chain recovery signs emerge in automotive sector', source: 'Supply Chain Dive', sentiment_score: 0.3, published_at: new Date(Date.now() - 14 * 60 * 60 * 1000).toISOString(), region: 'Europe' },
    ],
    timeSeries: Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (29 - i));
        return {
            date: date.toISOString().split('T')[0],
            overall_risk: 0.4 + Math.sin(i / 5) * 0.15 + Math.random() * 0.1,
            logistics_risk: 0.45 + Math.sin(i / 5) * 0.12 + Math.random() * 0.08,
            supplier_risk: 0.5 + Math.sin(i / 6) * 0.1 + Math.random() * 0.1,
            news_volume: 80 + Math.floor(Math.random() * 80),
        };
    }),
    metrics: [
        { category: 'Logistics', current_score: 0.58, previous_score: 0.52, trend: 'up', change_percent: 11.5 },
        { category: 'Suppliers', current_score: 0.52, previous_score: 0.55, trend: 'down', change_percent: -5.5 },
        { category: 'Manufacturing', current_score: 0.45, previous_score: 0.45, trend: 'stable', change_percent: 0 },
        { category: 'Raw Materials', current_score: 0.62, previous_score: 0.58, trend: 'up', change_percent: 6.9 },
        { category: 'Distribution', current_score: 0.38, previous_score: 0.42, trend: 'down', change_percent: -9.5 },
    ],
    suppliers: [
        { id: '1', name: 'Taiwan Semiconductor Manufacturing', region: 'Asia Pacific', risk_score: 0.72, tier: 1, is_critical: true },
        { id: '2', name: 'Samsung Electronics', region: 'Asia Pacific', risk_score: 0.65, tier: 1, is_critical: true },
        { id: '3', name: 'Intel Corporation', region: 'North America', risk_score: 0.45, tier: 1, is_critical: true },
        { id: '4', name: 'Foxconn Technology', region: 'Asia Pacific', risk_score: 0.58, tier: 1, is_critical: false },
        { id: '5', name: 'BASF Chemical', region: 'Europe', risk_score: 0.35, tier: 2, is_critical: false },
    ],
};

export default { dashboardAPI, predictionsAPI, mockData };
