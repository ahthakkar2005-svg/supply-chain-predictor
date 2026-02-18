/**
 * Utility functions for formatting data
 */

/**
 * Format a date to relative time (e.g., "2 hours ago")
 */
export function formatDistanceToNow(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffDay > 0) {
        return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    }
    if (diffHour > 0) {
        return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    }
    if (diffMin > 0) {
        return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    }
    return 'Just now';
}

/**
 * Format a number as percentage
 */
export function formatPercent(value, decimals = 0) {
    if (typeof value !== 'number') return '0%';
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a date for display
 */
export function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    });
}

/**
 * Format time for display
 */
export function formatTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
    });
}

export default { formatDistanceToNow, formatPercent, formatDate, formatTime };
