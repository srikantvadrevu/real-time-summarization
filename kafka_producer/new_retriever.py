# MIT License
#
# Copyright (c) 2023 Your Organization Name
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This script fetches the latest news articles from NewsAPI based on a specified category
and sends them to a Kafka topic. It's designed to be run periodically to keep the news feed updated.
"""

import os
import requests
import json
import logging
from kafka import KafkaProducer
import time
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'latest_news')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

def initialize_kafka_producer():
    """Initialize and return a Kafka producer."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info("Kafka producer initialized successfully")
        return producer
    except Exception as e:
        logging.error(f"Failed to initialize Kafka producer: {str(e)}")
        return None

def fetch_latest_news(query='latest'):
    """Fetch latest news articles from NewsAPI."""
    if not NEWS_API_KEY:
        logging.error("NEWS_API_KEY is not set in the environment variables")
        return []

    url = f'https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        logging.info(f"Fetched {len(articles)} articles for category: {query}")
        return articles
    except requests.RequestException as e:
        logging.error(f"Error fetching news: {str(e)}")
        return []

def send_to_kafka(producer, articles, category='latest'):
    """Send fetched articles to Kafka topic."""
    for article in articles:
        news_item = {
            'title': article.get('title'),
            'content': article.get('content'),
            'url': article.get('url'),
            'published_at': article.get('publishedAt'),
            'category': category
        }
        try:
            producer.send(KAFKA_TOPIC, news_item)
            logging.info(f"Sent to Kafka: {news_item['title']}")
            time.sleep(0.2)  # Throttle to avoid overwhelming the Kafka broker
        except Exception as e:
            logging.error(f"Failed to send article to Kafka: {str(e)}")

def main(category):
    """Main function to fetch news and send to Kafka."""
    producer = initialize_kafka_producer()
    if not producer:
        return

    articles = fetch_latest_news(category)
    if articles:
        send_to_kafka(producer, articles, category)
    else:
        logging.warning(f"No articles found for category: {category}")

    producer.close()

if __name__ == '__main__':
    # sports, pharma, technology, banking, startups, terrorism
    # category = 'terrorism'
    parser = argparse.ArgumentParser(description="Fetch and send news articles to Kafka")
    parser.add_argument("category", nargs="?", default="latest", help="News category to fetch (default: latest)")
    args = parser.parse_args()

    main(args.category)

