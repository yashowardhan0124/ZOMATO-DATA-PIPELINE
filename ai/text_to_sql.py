import os
import json
import pandas as pd
import streamlit as st
import snowflake.connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "qwen/qwen3.8-27b:free"

FORBIDDEN_WORDS = [
    "drop",
    "delete",
    "truncate",
    "alter",
    "update",
    "insert",
    "create",
    "replace",
    "grant",
    "revoke"
]

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisine has the most orders?",
    "Average delivery time by city",
    "Cancel rate by payment method"
]

OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("OpenRouter API key is not configured.")
    st.stop()

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

SCHEMA = """
Tables available in Snowflake.

FCT_ORDERS(
    order_id,
    order_date,
    customer_id,
    restaurant_id,
    city,
    cuisine,
    payment_method,
    order_status,
    is_delivered,
    sales_amount,
    discount,
    delivery_fee,
    gst,
    customer_rating,
    delivery_time_min
)

DIM_RESTAURANT(
    restaurant_id,
    restaurant_name,
    city,
    cuisine,
    rating,
    cost_for_two
)

DIM_CUSTOMER(
    customer_id,
    customer_name,
    age,
    age_segment,
    gender,
    city
)

MART_DAILY_CITY_REVENUNE(
    order_date,
    city,
    orders,
    cancel_rate,
    gmv,
    aov
)

MART_RESTAURANT_PERFORMANCE(
    restaurant_id,
    restaurant_name,
    city,
    cuisine,
    orders,
    revenue,
    avg_customer_rating,
    cancel_rate
)

MART_DELIVERY_SLA(
    city,
    order_hour,
    delivered_orders,
    p50_delivery_min,
    late_rate
)

Rules:

Use bare table names only.

Prefer MART tables when they fit the question.

GMV means delivered revenue.

Use SELECT queries only.

Never modify data.
"""

SYSTEM_PROMPT = f"""
You are an expert Snowflake SQL analyst.

Convert the user's natural language question into ONE SQL query.

Rules:
- SELECT or WITH queries only.
- Never modify data.
- Use bare table names.
- Do not use database or schema prefixes.
- Add LIMIT 100 or less unless the question asks for a single aggregate.
- Use correct Snowflake SQL syntax.
- Prefer MART tables when appropriate.
- Return JSON only.

Required format:

{{"sql":"your SQL query"}}

{SCHEMA}
"""


st.set_page_config(
    page_title="Zomato Data Intelligence",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 50% -20%,
                rgba(226, 55, 68, 0.18),
                transparent 38%
            ),
            #0b0b0d;
        color: #ffffff;
    }

    .main .block-container {
        max-width: 1150px;
        padding-top: 55px;
        padding-bottom: 60px;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 42px;
    }

    .brand-icon {
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: linear-gradient(
            135deg,
            #e23744,
            #ff3f56
        );
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 8px 25px rgba(226, 55, 68, 0.25);
    }

    .brand-name {
        font-size: 17px;
        font-weight: 750;
        color: #f5f5f5;
    }

    .hero-title {
        font-size: 52px;
        line-height: 1.08;
        font-weight: 850;
        letter-spacing: -2px;
        color: #ffffff;
        margin: 0;
    }

    .hero-red {
        color: #ff3f56;
    }

    .hero-subtitle {
        font-size: 17px;
        line-height: 1.7;
        color: #99999f;
        margin-top: 18px;
        margin-bottom: 38px;
        max-width: 780px;
    }

    .metric-card {
        background: rgba(25, 25, 28, 0.92);
        border: 1px solid #2b2b2f;
        border-radius: 17px;
        padding: 25px 24px;
        min-height: 120px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
    }

    .metric-value {
        font-size: 29px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .metric-label {
        font-size: 13px;
        color: #85858b;
    }

    .section-title {
        font-size: 25px;
        font-weight: 800;
        color: #ffffff;
        margin-top: 45px;
        margin-bottom: 8px;
    }

    .section-subtitle {
        color: #85858b;
        font-size: 14px;
        margin-bottom: 18px;
    }

    div[data-testid="stTextInput"] label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    div[data-testid="stTextInput"] input {
        background: #171719 !important;
        color: #ffffff !important;
        border: 1px solid #343438 !important;
        border-radius: 13px !important;
        height: 54px !important;
        padding: 0 18px !important;
        font-size: 15px !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #e23744 !important;
        box-shadow: 0 0 0 1px #e23744 !important;
    }

    .question-card {
        background: #171719;
        border: 1px solid #29292d;
        border-radius: 13px;
        padding: 15px 17px;
        margin-bottom: 10px;
        color: #cfcfd3;
        font-size: 14px;
    }

    .result-card {
        background: #171719;
        border: 1px solid #29292d;
        border-radius: 17px;
        padding: 24px;
        margin-top: 25px;
    }

    .answer-title {
        color: #ff3f56;
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .sql-title {
        color: #ffffff;
        font-size: 18px;
        font-weight: 750;
        margin-top: 28px;
        margin-bottom: 10px;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2c2c30;
    }

    .stCodeBlock {
        border-radius: 13px !important;
    }

    div.stButton > button {
        background: #e23744;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
    }

    div.stButton > button:hover {
        background: #ff3f56;
        color: white;
    }

    .success-box {
        background: rgba(46, 204, 113, 0.08);
        border: 1px solid rgba(46, 204, 113, 0.25);
        border-radius: 12px;
        padding: 13px 16px;
        color: #79e2a5;
        margin-top: 15px;
    }

    .model-badge {
        display: inline-block;
        background: rgba(226, 55, 68, 0.12);
        color: #ff5265;
        border: 1px solid rgba(226, 55, 68, 0.25);
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="MARTS",
        role="DBT_ROLE"
    )


def generate_sql(question):

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    answer = response.choices[0].message.content

    data = json.loads(answer)

    sql = data["sql"]

    sql = sql.replace("ZOMATO.MARTS.", "")
    sql = sql.replace("ZOMATO.", "")

    return sql.strip().rstrip(";")


def is_safe(sql):

    lowered = sql.lower().strip()

    if not (
        lowered.startswith("select")
        or lowered.startswith("with")
    ):
        return False

    for word in FORBIDDEN_WORDS:
        if word in lowered:
            return False

    return True


def run_query(sql):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        return cursor.fetch_pandas_all()
    finally:
        cursor.close()


st.markdown(
    """
    <div class="brand">
        <div class="brand-icon">🍴</div>
        <div class="brand-name">Zomato Data Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="hero-title">
        Ask questions about your
        <span class="hero-red">Zomato data.</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero-subtitle">
        Explore your orders, restaurants, customers and delivery
        performance using natural language and AI-powered SQL.
    </div>
    """,
    unsafe_allow_html=True
)


col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-value">Snowflake</div>
            <div class="metric-label">Data Warehouse</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-value">AI + SQL</div>
            <div class="metric-label">Natural Language Analytics</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-value">RAG Ready</div>
            <div class="metric-label">Data Intelligence Pipeline</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    '<div class="section-title">Ask your Zomato data</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">Ask a business question in normal English.</div>',
    unsafe_allow_html=True
)


question = st.text_input(
    "Your question",
    placeholder="e.g. Top 10 restaurants by revenue in Bangalore",
    label_visibility="collapsed"
)


if not question:

    st.markdown(
        '<div class="section-title" style="font-size:19px;">Try asking</div>',
        unsafe_allow_html=True
    )

    for q in EXAMPLE_QUESTIONS:
        st.markdown(
            f'<div class="question-card">💬 {q}</div>',
            unsafe_allow_html=True
        )


if question:

    with st.spinner("Generating SQL..."):

        try:
            sql = generate_sql(question)

        except Exception as e:
            st.error(f"AI error: {e}")
            st.stop()

    if not is_safe(sql):

        st.error(
            "The generated SQL is not safe to run."
        )

    else:

        try:

            with st.spinner("Running analysis..."):

                df = run_query(sql)

            st.markdown(
                """
                <div class="result-card">
                    <div class="answer-title">
                        ✓ Analysis completed
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(df)}</div>
                        <div class="metric-label">Rows Returned</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(df.columns)}</div>
                        <div class="metric-label">Data Columns</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">Qwen</div>
                        <div class="metric-label">AI SQL Model</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown(
                '<div class="section-title">Results</div>',
                unsafe_allow_html=True
            )

            if not df.empty:

                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True
                )

                if (
                    len(df.columns) == 2
                    and pd.api.types.is_numeric_dtype(
                        df.iloc[:, 1]
                    )
                ):

                    st.markdown(
                        '<div class="section-title">Visualization</div>',
                        unsafe_allow_html=True
                    )

                    chart_df = df.copy()

                    chart_df = chart_df.set_index(
                        chart_df.columns[0]
                    )

                    st.bar_chart(
                        chart_df.iloc[:, 0]
                    )

            else:

                st.info(
                    "The query executed successfully, "
                    "but no records were returned."
                )

            with st.expander("View generated SQL"):

                st.code(
                    sql,
                    language="sql"
                )

        except Exception as e:

            st.error(
                f"Error running query: {e}"
            )