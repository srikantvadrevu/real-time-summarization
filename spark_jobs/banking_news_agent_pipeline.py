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
This script is a Spark job that processes banking news articles using a banking agent.
It reads data from a PostgreSQL database, filters for banking-related news, and processes
each article using the banking agent to determine what action should be taken.
"""

import os
import logging
from pyspark.sql import SparkSession
from agents.banking_agent import banking_agent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the OpenAI API key is set in the environment
if "OPENAI_API_KEY" not in os.environ:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    exit(1)

def process_banking_news():
    """Main function to process banking news articles."""
    try:
        # Initialize Spark session
        spark = SparkSession.builder \
            .appName("BankingNewsAgent") \
            .getOrCreate()

        # Read from PostgreSQL
        df = spark.read \
            .format("jdbc") \
            .option("driver", "org.postgresql.Driver") \
            .option("url", os.getenv("DB_URL", "jdbc:postgresql://localhost:5432/newsdb")) \
            .option("dbtable", "news_processed") \
            .option("user", os.getenv("DB_USER", "postgres")) \
            .option("password", os.getenv("DB_PASSWORD", "")) \
            .load()

        # Filter banking category
        banking_df = df.filter("category = 'banking'")
        rows = banking_df.collect()

        # Run agent on each article
        for row in rows:
            article = {
                "title": row['title'],
                "summary": row['summary'],
                "url": row['url']
            }

            prompt = f"News Title: {article['title']}\n\nSummary: {article['summary']}\n\nWhat action should be taken?"
            logging.info(f"Processing: {article['title']}")
            try:
                decision = banking_agent.run(prompt)
                logging.info(f"Decision: {decision}")
            except Exception as e:
                logging.error(f"Error processing article {article['title']}: {str(e)}")

    except Exception as e:
        logging.error(f"Error in process_banking_news: {str(e)}")
    finally:
        if 'spark' in locals():
            spark.stop()

if __name__ == "__main__":
    process_banking_news()
