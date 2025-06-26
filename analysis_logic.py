# analysis_logic.py

# ======================================================================
# 1. IMPORTS (consolidated)
# ======================================================================
import uuid
import os
import joblib
from collections import defaultdict
import re
import logging
from datetime import datetime

import chromadb
import spacy
import textblob
from newsapi import NewsApiClient
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from urllib.parse import urlparse

import nltk
import textstat
from rouge_score import rouge_scorer

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

import requests
import trafilatura
from bert_score import score as bert_scorer
from sentence_transformers.util import cos_sim

from transformers import pipeline
from sklearn.ensemble import RandomForestRegressor

import collections

# Local imports from our project structure
import config

# ======================================================================
# 2. INITIAL SETUP (Models, etc.)
# ======================================================================
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Download NLTK data (will only download if missing)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab')


# Load NLP models once to avoid reloading on every API call
try:
    nlp = spacy.load("en_core_web_sm")
    sentiment_pipeline = pipeline("sentiment-analysis")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    summarizer_pipeline = pipeline("summarization", model="google/flan-t5-base")

    # Load NLP models once to avoid reloading
    nlp = spacy.load("en_core_web_sm")
    sentiment_pipeline = pipeline("sentiment-analysis")
except Exception as e:
    logging.error(f"Failed to load a pre-trained model: {e}")
    # In a real app, you might want to exit or handle this more gracefully
    nlp = None
    sentiment_pipeline = None
    embedding_model = None
    summarizer_pipeline = None


# ======================================================================
# 3. COMPREHENSIVE ANALYSIS HELPERS (RAG, BIAS REPORT)
# ======================================================================

def fetch_articles_newsapi(topic: str, num_articles: int = 20) -> list:
    """Fetches and cleans news articles using NewsAPI and trafilatura."""
    if not config.NEWS_API_KEY:
        raise ValueError("NewsAPI key not found. Please set the NEWS_API_KEY environment variable.")
    newsapi = NewsApiClient(api_key=config.NEWS_API_KEY)

    logging.info(f"Fetching article links for '{topic}' from NewsAPI...")
    articles_raw = newsapi.get_everything(q=topic, language='en', sort_by='relevancy', page_size=num_articles)

    articles = []
    logging.info("Downloading and cleaning full article content...")
    for i, a in enumerate(articles_raw.get("articles", [])):
        title = a.get("title", "")
        url = a.get("url", "")
        if not url or title == "[Removed]":
            continue

        logging.info(f"  > Processing ({i+1}/{len(articles_raw.get('articles', []))}) : {title[:50]}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            downloaded_html = requests.get(url, headers=headers, timeout=10).text
            cleaned_text = trafilatura.extract(
                downloaded_html, include_comments=False, include_tables=False, no_fallback=True
            )
            if cleaned_text:
                articles.append({
                    "title": title, "text": cleaned_text, "url": url, "publishedAt": a.get("publishedAt")
                })
            else:
                logging.warning(f"Could not extract main content from {url}")
        except Exception as e:
            logging.error(f"Failed to process URL {url}: {e}")

    logging.info(f"Successfully processed and cleaned {len(articles)} articles.")
    return articles

def create_rag_system(articles: list, topic: str) -> chromadb.Collection:
    """Creates an in-memory RAG system using ChromaDB."""
    collection_name = f"news_{topic.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    documents = []
    for article in articles:
        full_text = f"Title: {article['title']}\n{article['text']}"
        chunks = text_splitter.split_text(full_text)
        for chunk in chunks:
            documents.append({
                'text': chunk, 'metadata': {'source': article['url'], 'title': article['title']}
            })

    # Note: chromadb.Client() is an in-memory client. For persistence,
    # you would use chromadb.PersistentClient(path="/path/to/db")
    client = chromadb.Client()
    collection = client.create_collection(name=collection_name)
    if documents:
        collection.add(
            documents=[doc['text'] for doc in documents],
            metadatas=[doc['metadata'] for doc in documents],
            ids=[f"doc_{i}" for i in range(len(documents))]
        )
    return collection

def generate_summary_with_rag(topic: str, collection: chromadb.Collection) -> (str, str):
    """Generates a structured summary using the RAG system."""
    query = f"Provide a comprehensive overview of the key events, different perspectives, and economic impacts related to {topic}"
    try:
        context_chunks = collection.query(query_texts=[query], n_results=7)['documents'][0]
        context = "\n\n---\n\n".join(context_chunks)
    except IndexError:
         logging.warning("RAG collection returned no documents for the query. Context will be empty.")
         context = "No relevant information found in the provided articles."


    prompt_for_summarizer = f"""
    As an expert news analyst, synthesize the following context about '{topic}'.
    Your summary must be detailed and well-structured. Do not give a simple paragraph.

    Instead, follow this format:
    1.  **Overall Situation:** A brief, 2-3 sentence overview of the current state of affairs.
    2.  **Key Driving Factors:** A bulleted list of the primary causes or factors mentioned.
    3.  **Diverging Viewpoints:** Describe any different perspectives or points of contention.
    4.  **Economic Implications:** A bulleted list of the potential economic consequences.
    5.  **Outlook:** A concluding sentence on the future outlook based on the text.

    CONTEXT:
    ---
    {context}
    ---
    ANALYST SUMMARY:
    """
    if summarizer_pipeline:
        summary = summarizer_pipeline(
            prompt_for_summarizer, max_length=750, min_length=150, do_sample=False
        )[0]['summary_text']
        return summary, context
    return "Summarizer model not available.", context

def generate_detailed_bias_report(articles: list) -> str:
    """Generates a detailed, article-by-article bias report."""
    report = "# Detailed Bias Analysis\n"
    if not nlp:
        return "NLP model not available for bias report."
    for article in articles:
        text = article.get('text', '')
        blob = textblob.TextBlob(text)
        report += f"\n## Article: {article['title']}\n"
        report += f"- **URL**: {article['url']}\n"
        report += f"- **Overall Polarity**: {blob.sentiment.polarity:.2f} (1 is positive, -1 is negative)\n"
        report += f"- **Overall Subjectivity**: {blob.sentiment.subjectivity:.2f} (1 is opinion, 0 is fact-based)\n"
    return report

def extract_dynamic_perspectives(articles, topic, n_clusters=4):
    """
    Dynamically cluster articles by semantic similarity and summarize each cluster as a perspective.
    Returns a list of {label, summary} dicts.
    """
    if not articles or not embedding_model:
        return []
    texts = [a.get('title', '') + '. ' + a.get('text', '') for a in articles]
    embeddings = embedding_model.embed_documents(texts)
    
    # Use KMeans to cluster embeddings
    from sklearn.cluster import KMeans
    import numpy as np
    X = np.array(embeddings)
    n_clusters = min(n_clusters, len(articles))
    if n_clusters < 2:
        n_clusters = 1
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
    labels = kmeans.fit_predict(X)
    
    # Group articles by cluster
    clusters = collections.defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(articles[idx])
    
    # Label each cluster by most common country/entity/topic
    def get_cluster_label(arts):
        # Try to extract most common country/entity from titles/texts
        all_text = ' '.join([a.get('title', '') + ' ' + a.get('text', '') for a in arts]).lower()
        # Use spaCy NER for GPE (countries/cities)
        if nlp:
            doc = nlp(all_text)
            gpes = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
            if gpes:
                most_common = collections.Counter(gpes).most_common(1)[0][0]
                return most_common.title() + ' Perspective'
        # Fallback: use most common word in titles
        words = [w for a in arts for w in a.get('title', '').split()]
        if words:
            return collections.Counter(words).most_common(1)[0][0].title() + ' Perspective'
        return 'Perspective'
    
    # Summarize each cluster
    perspective_summaries = []
    for cluster_arts in clusters.values():
        label = get_cluster_label(cluster_arts)
        context = '\n'.join([a.get('title', '') + '. ' + a.get('text', '') for a in cluster_arts])
        prompt = f"As an expert analyst, summarize the perspective labeled '{label}' on '{topic}'. Focus on unique viewpoints, arguments, and evidence from the articles."
        if summarizer_pipeline:
            try:
                summary = summarizer_pipeline(prompt + '\n' + context[:2000], max_length=300, min_length=60, do_sample=False)[0]['summary_text']
            except Exception as e:
                summary = f"Error generating summary: {e}"
        else:
            summary = "Summarizer model not available."
        perspective_summaries.append({'label': label, 'summary': summary})
    return perspective_summaries

# ======================================================================
# 4. EVALUATION METRICS MODULE
# ======================================================================

def evaluate_rag_summary(summary: str, context: str, query: str) -> dict:
    """Runs a suite of evaluation metrics on the generated RAG summary."""
    logging.info("Running evaluation metrics on the generated summary...")
    if not embedding_model:
        return {"error": "Embedding model not available for evaluation."}

    # Faithfulness (BERTScore)
    _, _, f1 = bert_scorer([summary], [context], lang='en', verbose=False)
    faithfulness_score = f1.mean().item()

    # Relevance to Query
    summary_tokens = set(nltk.word_tokenize(summary.lower()))
    query_tokens = set(nltk.word_tokenize(query.lower()))
    relevance_score = len(summary_tokens.intersection(query_tokens)) / len(query_tokens) if query_tokens else 0

    # Readability
    readability_score = textstat.flesch_reading_ease(summary)

    # Coherence
    sentences = nltk.sent_tokenize(summary)
    coherence_score = 0
    if len(sentences) > 1:
        embeddings = embedding_model.embed_documents(sentences)
        similarities = [cos_sim(embeddings[i], embeddings[i+1]).item() for i in range(len(embeddings)-1)]
        coherence_score = np.mean(similarities) if similarities else 0

    return {
        "Faithfulness (BERTScore F1)": f"{faithfulness_score:.2f}",
        "Relevance to Query": f"{relevance_score:.2f}",
        "Readability (Flesch Score)": f"{readability_score:.2f}",
        "Coherence (Sentence Similarity)": f"{coherence_score:.2f}"
    }

# ======================================================================
# 5. TEMPORAL BIAS ANALYZER CLASS
# ======================================================================
class TemporalBiasAnalyzer:
    """Analyzes the evolution of media bias over time."""
    def __init__(self, project_path=config.PROJECT_DATA_PATH):
        os.makedirs(project_path, exist_ok=True)
        self.model_path = os.path.join(project_path, 'temporal_bias_model.joblib')
        self.dataset_path = os.path.join(project_path, 'historical_bias_data.csv')

    def process_articles_for_temporal_analysis(self, articles: list) -> pd.DataFrame:
        temporal_data = []
        for article in articles:
            if article.get('publishedAt') and article.get('text'):
                polarity = textblob.TextBlob(article['text']).sentiment.polarity
                temporal_data.append({
                    'date': pd.to_datetime(article['publishedAt']).date(),
                    'bias_intensity': polarity
                })
        if not temporal_data:
            return pd.DataFrame()
        df = pd.DataFrame(temporal_data)
        daily_avg_df = df.groupby('date')['bias_intensity'].mean().reset_index()
        daily_avg_df['date'] = pd.to_datetime(daily_avg_df['date'])
        return daily_avg_df

    def train_model(self, data: pd.DataFrame):
        data['days_since_start'] = (data['date'] - data['date'].min()).dt.days
        if len(data) < 2:
            logging.warning("Not enough historical data to train temporal model.")
            return None
        feature_df = data[['days_since_start', 'bias_intensity']].copy()
        feature_df['target_bias'] = feature_df['bias_intensity'].shift(-1)
        feature_df = feature_df.dropna()
        X = feature_df[['days_since_start', 'bias_intensity']]
        y = feature_df['target_bias']
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model

    def update_model_with_new_data(self, new_data_df: pd.DataFrame):
        if new_data_df.empty:
            logging.info("No new data to update the temporal model.")
            # Still load historical data if it exists for visualization
            if os.path.exists(self.dataset_path):
                 return None, pd.read_csv(self.dataset_path, parse_dates=['date'])
            return None, None

        if os.path.exists(self.dataset_path):
            historical_data = pd.read_csv(self.dataset_path, parse_dates=['date'])
            updated_data = pd.concat([historical_data, new_data_df], ignore_index=True)
        else:
            updated_data = new_data_df

        updated_data.drop_duplicates(subset=['date'], keep='last', inplace=True)
        updated_data.sort_values(by='date', inplace=True)
        updated_data.to_csv(self.dataset_path, index=False)
        logging.info(f"Historical dataset updated. Total data points: {len(updated_data)}")
        logging.info("Re-training temporal model with new data...")
        model = self.train_model(updated_data)
        if model:
            joblib.dump(model, self.model_path)
            logging.info(f"Temporal model saved to {self.model_path}")
        return model, updated_data

# ======================================================================
# 6. VISUALIZATION FUNCTIONS (MODIFIED FOR BACKEND)
# ======================================================================

def visualize_bias_evolution(historical_data: pd.DataFrame, output_path: str):
    """Saves a line plot of bias evolution to a file."""
    if historical_data is None or historical_data.empty:
        logging.warning("Cannot generate bias evolution viz: data is empty.")
        return
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(historical_data['date'], historical_data['bias_intensity'], marker='o', linestyle='-', color='b', label='Daily Average Bias')
    if len(historical_data) >= 3:
        historical_data['rolling_avg'] = historical_data['bias_intensity'].rolling(window=3).mean()
        ax.plot(historical_data['date'], historical_data['rolling_avg'], linestyle='--', color='r', label='3-Day Rolling Average')
    ax.set_title('Historical Bias Evolution Over Time', fontsize=18, weight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Average Bias Intensity (Sentiment Polarity)', fontsize=12)
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig) # Important to release memory
    logging.info(f"Bias evolution chart saved to {output_path}")

def visualize_source_bias(articles: list, output_path: str):
    """Analyzes and saves a bar chart of source bias to a file."""
    if not articles:
        logging.warning("Cannot generate source bias viz: no articles provided.")
        return

    source_sentiments = defaultdict(list)
    for article in articles:
        try:
            source_name = urlparse(article['url']).netloc.replace('www.', '')
        except:
            source_name = 'unknown'
        polarity = textblob.TextBlob(article['text']).sentiment.polarity
        source_sentiments[source_name].append(polarity)

    avg_sentiments = {source: np.mean(scores) for source, scores in source_sentiments.items()}
    sorted_sources = sorted(avg_sentiments.items(), key=lambda item: item[1])
    sources = [item[0] for item in sorted_sources]
    sentiments = [item[1] for item in sorted_sources]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, max(8, len(sources) * 0.5))) # Dynamic height
    colors = ['#d65f5f' if s < 0 else '#6acc64' for s in sentiments]
    ax.barh(sources, sentiments, color=colors)
    ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_title('Average Sentiment by News Source', fontsize=18, weight='bold')
    ax.set_xlabel('Average Sentiment Polarity (Negative to Positive)', fontsize=12)
    ax.set_ylabel('News Source', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig) # Important to release memory
    logging.info(f"Source bias chart saved to {output_path}")

# ======================================================================
# 7. MAIN INTEGRATED WORKFLOW (REFACTORED FOR API)
# ======================================================================

def run_full_analysis(topic: str, num_articles: int = 25) -> dict:
    """
    Runs the full pipeline and returns a dictionary with all results.
    """
    logging.info(f"===== STARTING ANALYSIS FOR: {topic.upper()} =====")
    results = {}

    # Part 1: Fetch and generate reports
    articles = fetch_articles_newsapi(topic, num_articles=num_articles)
    if not articles:
        logging.warning("No articles found. Halting analysis.")
        return {"error": "No articles found for the given topic."}

    rag_collection = create_rag_system(articles, topic)
    summary_report, rag_context = generate_summary_with_rag(topic, rag_collection)
    bias_report = generate_detailed_bias_report(articles)

    # NEW: Dynamic perspective summaries
    dynamic_perspectives = extract_dynamic_perspectives(articles, topic)
    results['perspectives'] = dynamic_perspectives

    results['executive_summary'] = summary_report
    results['detailed_bias_report'] = bias_report

    # Part 2: Evaluation
    query_for_eval = f"Summarize the key events and perspectives about {topic}"
    evaluation_results = evaluate_rag_summary(summary_report, rag_context, query_for_eval)
    results['summary_evaluation'] = evaluation_results

    # Part 3: Temporal Feedback Loop
    analyzer = TemporalBiasAnalyzer()
    new_temporal_data = analyzer.process_articles_for_temporal_analysis(articles)
    _, historical_data = analyzer.update_model_with_new_data(new_temporal_data)

    # Part 4: Visualization
    os.makedirs(config.VISUALS_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    historical_chart_filename = f"historical_bias_{timestamp}.png"
    source_chart_filename = f"source_bias_{timestamp}.png"

    historical_chart_path = os.path.join(config.VISUALS_PATH, historical_chart_filename)
    source_chart_path = os.path.join(config.VISUALS_PATH, source_chart_filename)

    visualize_bias_evolution(historical_data, historical_chart_path)
    visualize_source_bias(articles, source_chart_path)

    results['visualizations'] = {
        "historical_bias_chart_url": f"/static/visuals/{historical_chart_filename}",
        "source_bias_chart_url": f"/static/visuals/{source_chart_filename}"
    }
    
    logging.info("✅ Analysis Complete.")
    return results