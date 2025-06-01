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
This script is a Spark job that processes terrorism-related news articles using a terrorism agent.
It reads data from a PostgreSQL database, filters for terrorism-related news, and processes
each article using the terrorism agent to determine appropriate actions.
"""

import os
import logging
from pyspark.sql import SparkSession
from agents.terrorism_agent import terrorism_agent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the OpenAI API key is set in the environment
if "OPENAI_API_KEY" not in os.environ:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    exit(1)

# Configuration
DB_URL = os.getenv("DB_URL", "jdbc:postgresql://localhost:5432/newsdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_TABLE = os.getenv("DB_TABLE", "news_processed")

def process_terrorism_news():
    """Main function to process terrorism-related news articles."""
    try:
        # Initialize Spark session
        spark = SparkSession.builder \
            .appName("TerrorismNewsAgent") \
            .getOrCreate()

        # Read from PostgreSQL
        df = spark.read \
            .format("jdbc") \
            .option("driver", "org.postgresql.Driver") \
            .option("url", DB_URL) \
            .option("dbtable", DB_TABLE) \
            .option("user", DB_USER) \
            .option("password", DB_PASSWORD) \
            .load()

        # Filter terrorism category
        terrorism_df = df.filter("category = 'terrorism'")
        rows = terrorism_df.collect()

        # Process each article
        for row in rows:
            article = {
                "title": row['title'],
                "summary": row['summary'],
                "url": row['url']
            }

            prompt = f"""System: You are an expert terrorism threat analyst. Based on the news summary, choose the most appropriate action.

News Title: {article['title']}

Summary: {article['summary']}

Decide what to do."""

            logging.info(f"Processing: {article['title']}")
            try:
                decision = terrorism_agent.run(prompt)
                logging.info(f"Decision: {decision}")
            except Exception as e:
                logging.error(f"Error processing article {article['title']}: {str(e)}")

    except Exception as e:
        logging.error(f"Error in process_terrorism_news: {str(e)}")
    finally:
        if 'spark' in locals():
            spark.stop()

if __name__ == "__main__":
    process_terrorism_news()