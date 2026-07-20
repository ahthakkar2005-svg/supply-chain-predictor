import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * WebSocket connection states
 */
const WS_STATE = {
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    RECONNECTING: 'reconnecting',
};

/**
 * Custom hook for managing WebSocket connection
 * Handles auto-reconnect, heartbeat, and message dispatching
 */
export function useWebSocket(url = null) {
    const [connectionState, setConnectionState] = useState(WS_STATE.DISCONNECTED);
    const [lastMessage, setLastMessage] = useState(null);
    const [apiStatus, setApiStatus] = useState({ news_api: false, weather_api: false });

    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const heartbeatRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const listenersRef = useRef({});
    const maxReconnectAttempts = 10;

    // Build WebSocket URL
    const defaultWsUrl = import.meta.env.VITE_WS_URL || 'wss://supply-chain-predictor-00q5.onrender.com/ws';
    const wsUrl = url || defaultWsUrl;

    /**
     * Register an event listener for a specific event type
     */
    const on = useCallback((event, callback) => {
        if (!listenersRef.current[event]) {
            listenersRef.current[event] = [];
        }
        listenersRef.current[event].push(callback);

        // Return unsubscribe function
        return () => {
            listenersRef.current[event] = listenersRef.current[event].filter(cb => cb !== callback);
        };
    }, []);

    /**
     * Emit to registered listeners
     */
    const emit = useCallback((event, data) => {
        const listeners = listenersRef.current[event] || [];
        listeners.forEach(cb => {
            try {
                cb(data);
            } catch (e) {
                console.error(`WebSocket listener error for ${event}:`, e);
            }
        });
    }, []);

    /**
     * Send a message through the WebSocket
     */
    const send = useCallback((data) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);

    /**
     * Start heartbeat ping/pong
     */
    const startHeartbeat = useCallback(() => {
        if (heartbeatRef.current) clearInterval(heartbeatRef.current);
        heartbeatRef.current = setInterval(() => {
            send({ type: 'ping' });
        }, 25000);
    }, [send]);

    /**
     * Connect to WebSocket
     */
    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        setConnectionState(reconnectAttemptsRef.current > 0 ? WS_STATE.RECONNECTING : WS_STATE.CONNECTING);

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('🔌 WebSocket connected');
                setConnectionState(WS_STATE.CONNECTED);
                reconnectAttemptsRef.current = 0;
                startHeartbeat();
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setLastMessage(message);

                    // Handle initial snapshot
                    if (message.event === 'initial_snapshot') {
                        if (message.data?.api_status) {
                            setApiStatus(message.data.api_status);
                        }
                        emit('snapshot', message.data);
                    }

                    // Handle specific event types
                    if (message.event) {
                        emit(message.event, message.data);
                    }
                } catch (e) {
                    console.error('WebSocket parse error:', e);
                }
            };

            ws.onclose = (event) => {
                console.log('🔌 WebSocket disconnected', event.code, event.reason);
                setConnectionState(WS_STATE.DISCONNECTED);
                if (heartbeatRef.current) clearInterval(heartbeatRef.current);

                // Auto-reconnect with exponential backoff
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                    reconnectAttemptsRef.current++;
                    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
                    reconnectTimeoutRef.current = setTimeout(connect, delay);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (e) {
            console.error('WebSocket connection failed:', e);
            setConnectionState(WS_STATE.DISCONNECTED);
        }
    }, [wsUrl, emit, startHeartbeat]);

    /**
     * Disconnect from WebSocket
     */
    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        if (heartbeatRef.current) clearInterval(heartbeatRef.current);
        reconnectAttemptsRef.current = maxReconnectAttempts; // Prevent auto-reconnect
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setConnectionState(WS_STATE.DISCONNECTED);
    }, []);

    /**
     * Request a full data refresh
     */
    const refresh = useCallback(() => {
        send({ type: 'refresh' });
    }, [send]);

    // Connect on mount, disconnect on unmount
    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        connectionState,
        isConnected: connectionState === WS_STATE.CONNECTED,
        lastMessage,
        apiStatus,
        send,
        on,
        refresh,
        connect,
        disconnect,
    };
}

export { WS_STATE };
