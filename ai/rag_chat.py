import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Zomato Review AI",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

EMBEDDING_MODEL = "openai/text-embedding-3-small"
CHAT_MODEL = "qwen/qwen3.8-27b:free"
NEW_REVIEWS = 500
TOP_K = 5
CACHE_FILE = "review_embeddings.parquet"

OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("OpenRouter API key is not configured.")
    st.stop()

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(239, 68, 68, 0.14), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(244, 63, 94, 0.10), transparent 25%),
        #0d0d0f;
    color: #ffffff;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

header {
    visibility: hidden;
}

.hero {
    padding: 35px 10px 25px 10px;
}

.logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 35px;
}

.logo-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: linear-gradient(135deg, #ef4444, #e11d48);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.hero-title {
    font-size: 52px;
    line-height: 1.08;
    font-weight: 800;
    letter-spacing: -2px;
    margin-bottom: 15px;
}

.hero-title span {
    background: linear-gradient(90deg, #ff5a5f, #ff385c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #a1a1aa;
    font-size: 17px;
    line-height: 1.6;
    max-width: 680px;
    margin-bottom: 30px;
}

.search-container {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 8px;
    backdrop-filter: blur(20px);
    margin-bottom: 35px;
}

.stTextInput > div > div > input {
    background: transparent !important;
    color: white !important;
    border: none !important;
    font-size: 16px !important;
    padding: 14px 18px !important;
}

.stTextInput > div > div {
    border: none !important;
    box-shadow: none !important;
}

.stTextInput label {
    display: none;
}

.stat-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 22px;
    min-height: 110px;
    backdrop-filter: blur(15px);
}

.stat-number {
    font-size: 27px;
    font-weight: 700;
    margin-bottom: 5px;
}

.stat-label {
    color: #92929b;
    font-size: 13px;
}

.section-heading {
    font-size: 22px;
    font-weight: 700;
    margin-top: 42px;
    margin-bottom: 16px;
}

.answer-card {
    background: linear-gradient(
        135deg,
        rgba(239,68,68,0.12),
        rgba(255,255,255,0.045)
    );
    border: 1px solid rgba(239,68,68,0.22);
    border-radius: 20px;
    padding: 28px;
    line-height: 1.75;
    font-size: 16px;
    color: #eeeeee;
    box-shadow: 0 15px 45px rgba(0,0,0,0.18);
}

.ai-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.25);
    color: #ff6b6b;
    padding: 7px 12px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 15px;
}

.review-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 12px;
}

.review-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

.review-city {
    font-weight: 600;
    color: #ffffff;
}

.review-rating {
    color: #fbbf24;
    font-weight: 600;
}

.review-text {
    color: #b5b5bd;
    line-height: 1.6;
    font-size: 14px;
}

.match-score {
    color: #777780;
    font-size: 11px;
    margin-top: 10px;
}

.footer {
    text-align: center;
    color: #66666f;
    font-size: 12px;
    margin-top: 60px;
    padding-top: 25px;
    border-top: 1px solid rgba(255,255,255,0.06);
}

.stSpinner > div {
    border-top-color: #ef4444 !important;
}

[data-testid="stExpander"] {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
}

</style>
""", unsafe_allow_html=True)


def read_reviews_from_snowflake():

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

    query = f"""
        SELECT
            REVIEW_ID,
            CITY,
            RATING,
            COMMENT
        FROM ZOMATO.STAGING.STG_REVIEWS
        SAMPLE ({NEW_REVIEWS} ROWS)
    """

    cursor = conn.cursor()

    try:
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
    finally:
        cursor.close()
        conn.close()

    df.columns = [col.lower() for col in df.columns]

    df = df.dropna(subset=["comment"])

    df["comment"] = df["comment"].astype(str)

    return df


def embed(texts):

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return [item.embedding for item in response.data]


@st.cache_data
def load_reviews():

    if os.path.exists(CACHE_FILE):
        return pd.read_parquet(CACHE_FILE)

    df = read_reviews_from_snowflake()

    df["embedding"] = embed(
        df["comment"].tolist()
    )

    df.to_parquet(CACHE_FILE)

    return df


def cosine_similarity(vec_a, vec_b):

    denominator = (
        np.linalg.norm(vec_a)
        * np.linalg.norm(vec_b)
    )

    if denominator == 0:
        return 0.0

    return np.dot(vec_a, vec_b) / denominator


def find_similar_reviews(question, df):

    question_vector = embed([question])[0]

    scores = []

    for review_vector in df["embedding"]:
        scores.append(
            cosine_similarity(
                question_vector,
                review_vector
            )
        )

    result = df.copy()

    result["score"] = scores

    return result.nlargest(
        TOP_K,
        "score"
    )


def ask_llm(question, top_reviews):

    context = ""

    for _, row in top_reviews.iterrows():

        context += (
            f"City: {row['city']}\n"
            f"Rating: {row['rating']} stars\n"
            f"Review: {row['comment']}\n\n"
        )

    system_prompt = """
You are an AI data analyst for a food delivery application.

Answer ONLY using the customer reviews provided.

Give a concise and useful answer.

Do not invent information.

If the reviews do not provide enough information,
say exactly:

"I don't have enough information in the provided reviews."
"""

    user_prompt = f"""
Question:
{question}

Customer Reviews:
{context}
"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.choices[0].message.content


st.markdown("""
<div class="hero">

<div class="logo">
    <div class="logo-icon">🍴</div>
    Zomato Review Intelligence
</div>

<div class="hero-title">
    Understand what your<br>
    <span>customers are saying.</span>
</div>

<div class="hero-subtitle">
    Ask questions about customer reviews and get AI-powered insights
    using Retrieval-Augmented Generation.
</div>

</div>
""", unsafe_allow_html=True)


review_df = load_reviews()


col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">{len(review_df)}</div>
            <div class="stat-label">Customer Reviews</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">{TOP_K}</div>
            <div class="stat-label">Relevant Reviews per Query</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:

    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-number">RAG</div>
            <div class="stat-label">AI Retrieval Pipeline</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    '<div class="section-heading">Ask your reviews</div>',
    unsafe_allow_html=True
)

question = st.text_input(
    "",
    placeholder="🔍  What are customers saying about delivery?",
    label_visibility="collapsed"
)


if question:

    with st.spinner("Finding the most relevant reviews..."):

        top_reviews = find_similar_reviews(
            question,
            review_df
        )

    with st.spinner("Generating AI insight..."):

        answer = ask_llm(
            question,
            top_reviews
        )

    st.markdown(
        '<div class="section-heading">AI Insight</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="ai-badge">✦ AI GENERATED INSIGHT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="answer-card">
            {answer}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-heading">Supporting Reviews</div>',
        unsafe_allow_html=True
    )

    for _, row in top_reviews.iterrows():

        stars = "★" * int(row["rating"])

        st.markdown(
            f"""
            <div class="review-card">

                <div class="review-header">

                    <div class="review-city">
                        📍 {row["city"]}
                    </div>

                    <div class="review-rating">
                        {stars} {row["rating"]}
                    </div>

                </div>

                <div class="review-text">
                    {row["comment"]}
                </div>

                <div class="match-score">
                    Relevance score: {row["score"]:.4f}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


st.markdown(
    """
    <div class="footer">
        Zomato Review Intelligence · Snowflake · RAG · OpenRouter
    </div>
    """,
    unsafe_allow_html=True
)