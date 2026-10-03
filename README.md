# Zomato AI Data Engineering — End-to-End Project

> 👨‍💻 **Project by:** Yashowardhan Sagar Shete

A complete batch data pipeline that takes Zomato-style food delivery data from raw CSVs all the way to AI-powered analytics:

**Zomato/Food Delivery Dataset → Amazon S3 → Snowflake → dbt → Airflow → AI (OpenAI)**

The dataset lands in an S3 data lake and flows into Snowflake through a storage integration, where dbt transforms it through medallion layers — RAW (Bronze) tables, cleaned STAGING (Silver) views, and business-ready MARTS (Gold) with dimensions, facts, and aggregate marts. Apache Airflow orchestrates the pipeline as one daily DAG. On top of the warehouse sits an AI layer powered by OpenAI: LLM enrichment turns free-text reviews into structured columns; RAG lets you chat with your reviews; and text-to-SQL lets you query the warehouse in plain English. Streamlit serves the AI applications.

## What gets built

| **Layer**         | **Where**                  | **What** |
|-------------------|----------------------------|----------|
| **Source**        | `data/`                    | Zomato food delivery datasets |
| **Lake**          | Amazon S3                  | Raw data organized by table |
| **Bronze**        | Snowflake `ZOMATO.RAW`     | Raw tables loaded from S3 |
| **Silver**        | Snowflake `ZOMATO.STAGING` | dbt staging views and cleaned data |
| **Gold**           | Snowflake `ZOMATO.MARTS`   | Dimensions, facts and business marts |
| **AI**            | Snowflake `ZOMATO.AI`      | LLM-enriched reviews, RAG chat, text-to-SQL |
| **Orchestration** | Airflow (Docker)            | Automated batch pipeline |

## Tech stack

Python · Pandas · Amazon S3 · Snowflake · dbt (dbt-snowflake) · Apache Airflow · OpenAI · Streamlit · Power BI · Docker · Git

## Repository structure

```text
├── airflow/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── dags/
│       └── zomato_batch.py
│
├── zomato/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── macros/
│
├── ai/
│   ├── enrich_reviews.py
│   ├── rag_chat.py
│   └── text_to_sql.py
│
├── data/
│   └── Zomato datasets
│
└── .gitignore
How the pipeline works
1 · Data lands in S3

The Zomato datasets are uploaded to Amazon S3 and organized into folders by table.

2 · S3 → Snowflake

Snowflake reads the data from S3 and loads it into the ZOMATO.RAW schema.

3 · Transform — dbt

dbt transforms the raw data into staging and business-ready marts.

Staging (Silver) — cleaned and standardized source data.
Dimensions (Gold) — customer, restaurant, food and date dimensions.
Facts (Gold) — orders and order items.
Marts (Gold) — daily city revenue, restaurant performance, delivery SLA and review insights.
Tests — uniqueness, not-null, relationships and accepted-value tests.
4 · Orchestrate — Airflow

Apache Airflow runs the complete pipeline:

S3 → Snowflake RAW → dbt → AI enrichment → MARTS

The pipeline is containerized using Docker.

5 · AI layer

The project includes three AI capabilities:

LLM enrichment (ai/enrich_reviews.py) — analyzes reviews and creates structured sentiment, topic and issue information.
RAG (ai/rag_chat.py) — allows users to chat with customer reviews and receive answers based on the review data.
Text-to-SQL (ai/text_to_sql.py) — allows users to ask questions in plain English and generate SELECT-only SQL queries for Snowflake.
6 · Analytics

Power BI can be connected to the Snowflake MARTS layer for dashboards covering:

Revenue and GMV
Orders
AOV
Cancellation rate
Restaurant performance
Delivery performance
Customer reviews
Sentiment analysis
Running it
# dbt
cd zomato
dbt debug
dbt build --exclude tag:ai

# Airflow
cd airflow
docker compose build
docker compose up -d

# AI applications
streamlit run ai/rag_chat.py
streamlit run ai/text_to_sql.py
Author

Yashowardhan Sagar Shete

B.Tech — Computer Science / AI Specialization
MIT-ADT University, Pune

GitHub: https://github.com/yashowardhan0124
