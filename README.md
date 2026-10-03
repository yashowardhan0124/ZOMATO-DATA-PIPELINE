# Zomato AI Data Engineering — End-to-End Project

> 👨‍💻 **Project by:** Yashowardhan Sagar Shete

A complete batch data pipeline that takes Zomato-style food delivery data from raw CSVs all the way to AI-powered analytics:

**Zomato/Food Delivery Dataset → Amazon S3 → Snowflake → dbt → Airflow → AI**

The dataset lands in an S3 data lake and flows into Snowflake, where dbt transforms it through RAW, STAGING and MARTS layers. Apache Airflow orchestrates the pipeline. The AI layer provides review enrichment, RAG-based review analysis, and natural-language SQL queries. Streamlit is used for the AI applications.

## What gets built

| Layer | Where | What |
|---|---|---|
| **Source** | `data/` | Restaurants, users, food, menu, orders, order items and reviews |
| **Lake** | Amazon S3 | Raw data organized by table |
| **Bronze** | Snowflake `ZOMATO.RAW` | Raw tables loaded from S3 |
| **Silver** | Snowflake `ZOMATO.STAGING` | Cleaned and transformed staging views |
| **Gold** | Snowflake `ZOMATO.MARTS` | Dimensions, facts and business marts |
| **AI** | Snowflake `ZOMATO.AI` | Review enrichment, RAG and text-to-SQL |
| **Orchestration** | Airflow + Docker | Automated data pipeline |
| **Analytics** | Power BI | Business dashboards and data visualization |

## Tech stack

Python · Pandas · Amazon S3 · Snowflake · dbt · Apache Airflow · OpenAI · Streamlit · Power BI · Docker · Git

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
