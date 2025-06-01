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
This script consumes messages from a Kafka topic and loads them into a PostgreSQL database.
It's designed to handle news articles, storing their title, content, URL, category, and publication date.

For database setup instructions, please refer to the README.md file.
"""

import os
import json
import logging
from kafka import KafkaConsumer
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka configuration
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'latest_news')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')

# PostgreSQL configuration
DB_NAME = os.getenv('DB_NAME', 'newsdb')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # Set this in your environment for security
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

try:
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='news-consumer-group'
    )

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    logging.info("Successfully connected to Kafka and PostgreSQL")

except (psycopg2.Error, Exception) as e:
    logging.error(f"Error during setup: {str(e)}")
    exit(1)

def insert_news_item(news):
    """Insert a news item into the database."""
    try:
        cursor.execute(
            """
            INSERT INTO news_articles (title, content, url, category, published_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (news['title'], news['content'], news['url'], news['category'], news['published_at'])
        )
        conn.commit()
        logging.info(f"Inserted: {news['title']}")
    except psycopg2.Error as e:
        logging.error(f"Error inserting news item: {str(e)}")
        conn.rollback()

def main():
    """Main function to consume messages and write to DB."""
    try:
        for message in consumer:
            news_item = message.value
            insert_news_item(news_item)
    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
    finally:
        if conn:
            cursor.close()
            conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main()
