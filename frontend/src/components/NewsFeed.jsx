import React from 'react';
import { formatDistanceToNow } from '../utils/formatters';

/**
 * News Item Component
 */
function NewsItem({ article }) {
    const { title, source, sentiment_score, published_at, region } = article;

    const getSentimentClass = () => {
        if (sentiment_score < -0.3) return 'negative';
        if (sentiment_score > 0.3) return 'positive';
        return 'neutral';
    };

    const timeAgo = formatDistanceToNow(published_at);

    return (
        <div className="news-item animate-fadeIn">
            <div className={`news-sentiment ${getSentimentClass()}`} />
            <div className="news-content">
                <div className="news-title">{title}</div>
                <div className="news-meta">
                    <span>{source}</span>
                    <span>{region}</span>
                    <span>{timeAgo}</span>
                </div>
            </div>
        </div>
    );
}

/**
 * News Feed Component
 * Displays latest supply chain news with sentiment indicators
 */
export function NewsFeed({ news = [] }) {
    if (news.length === 0) {
        return (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                No news articles available
            </div>
        );
    }

    return (
        <div className="news-feed">
            {news.map((article, index) => (
                <NewsItem key={article.id || index} article={article} />
            ))}
        </div>
    );
}

export default NewsFeed;
