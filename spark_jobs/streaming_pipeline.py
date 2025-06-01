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
This script is a Spark streaming job that processes news articles from a Kafka topic,
summarizes and categorizes them using OpenAI's language models, and then writes
the processed data to a PostgreSQL database.
"""

import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType
import psycopg2
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the OpenAI API key is set in the environment
if "OPENAI_API_KEY" not in os.environ:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    exit(1)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "latest_news")
DB_NAME = os.getenv("DB_NAME", "newsdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Summarizer prompt
summary_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a factual and concise news summarizer. "
        "Summarize the provided content into 2–3 accurate sentences. "
        "If the content is unclear or incomplete, respond only with 'unknown'."
    ),
    HumanMessagePromptTemplate.from_template("{content}")
])

# Categorizer prompt
categorization_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """You are a reliable news classifier. Given a news article, choose the single most likely category from the following list:

            - sports
            - pharma
            - technology
            - banking
            - startups
            - terrorism
            
            Only return the category name: one of the six above, or "unknown".
            
            If you are not at least 50% confident in your classification, or the article does not clearly belong to any of the categories, return only: unknown.
            
            Respond with exactly one word: the category name or unknown."""
    ),
    HumanMessagePromptTemplate.from_template("{content}")
])

# LLMs with deterministic output
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.0)

summary_chain = LLMChain(llm=llm, prompt=summary_prompt)
category_chain = LLMChain(llm=llm, prompt=categorization_prompt)

def summarize_with_openai(content):
    """Summarize the content using OpenAI."""
    if not content or len(content.strip()) < 50:
        return "unknown"
    try:
        response = summary_chain.run(content=content[:3000])
        return response.strip() if response.strip() else "unknown"
    except Exception as e:
        logging.error(f"Summarization error: {e}")
        return "unknown"

def categorize_with_openai(content):
    """Categorize the content using OpenAI."""
    if not content or len(content.strip()) < 50:
        return "unknown"
    try:
        response = category_chain.run(content=content[:3000])
        label = response.strip().lower()
        valid_labels = ["sports", "pharma", "technology", "banking", "startups", "terrorism", "unknown"]
        return label if label in valid_labels else "unknown"
    except Exception as e:
        logging.error(f"Categorization error: {e}")
        return "unknown"

def write_to_postgres(df, epoch_id):
    """Write the processed data to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()

        for row in df.collect():
            summary = summarize_with_openai(row.content)
            category = categorize_with_openai(row.content)
            logging.info(f"Processing: {row.title}")
            cursor.execute("""
                INSERT INTO news_processed (title, summary, category, url, published_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (row.title, summary, category, row.url, row.published_at))

        conn.commit()
        logging.info(f"Batch {epoch_id} written to PostgreSQL")
    except Exception as e:
        logging.error(f"Error writing to PostgreSQL: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main function to run the Spark streaming job."""
    # Spark session
    spark = SparkSession.builder \
        .appName("KafkaNewsLangchainPipeline") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    schema = StructType() \
        .add("title", StringType()) \
        .add("content", StringType()) \
        .add("url", StringType()) \
        .add("category", StringType()) \
        .add("published_at", StringType())

    # Kafka stream
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()

    df_parsed = df_raw.selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), schema).alias("data")) \
        .select("data.*")

    # Use foreachBatch to summarize + write
    query = df_parsed.writeStream \
        .trigger(processingTime="10 seconds") \
        .foreachBatch(write_to_postgres) \
        .outputMode("append") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()