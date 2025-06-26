# BharatLens - Advanced News Analysis Platform

BharatLens is a comprehensive news analysis platform that combines advanced NLP, AI, and data visualization to provide deep insights into news topics with bias detection and credibility analysis.

## 🌟 Features

### Backend Analysis
- **News Article Fetching**: Automated collection of articles from NewsAPI
- **RAG-based Summarization**: Advanced retrieval-augmented generation for comprehensive summaries
- **Bias Detection**: Multi-dimensional bias analysis across sources and time
- **Sentiment Analysis**: Detailed sentiment scoring and subjectivity analysis
- **Source Credibility**: Analysis of news source reliability and bias patterns
- **Temporal Analysis**: Historical bias evolution tracking
- **Quality Metrics**: BERTScore, relevance, readability, and coherence evaluation

### Frontend Interface
- **Modern UI**: Clean, responsive design with gradient backgrounds and glassmorphism effects
- **Real-time Analysis**: Interactive form with loading indicators and progress feedback
- **Results Visualization**: 
  - Executive summaries with structured formatting
  - Quality metrics dashboard
  - Interactive charts for bias evolution and source analysis
  - Detailed bias reports
- **Mobile Responsive**: Optimized for all device sizes
- **Error Handling**: User-friendly error messages and validation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- NewsAPI key (free at [newsapi.org](https://newsapi.org))

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd llm
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   ```bash
   # Windows
   set NEWS_API_KEY=your_api_key_here
   
   # Linux/Mac
   export NEWS_API_KEY=your_api_key_here
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the Frontend**
   - Open your browser and go to `http://127.0.0.1:5000`
   - Enter a news topic and click "Analyze"

## 📁 Project Structure

```
llm/
├── app.py                 # Flask application with API endpoints
├── analysis_logic.py      # Core analysis engine
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/
│   └── index.html       # Main frontend template
├── static/
│   ├── css/
│   │   └── style.css    # Frontend styles
│   ├── js/
│   │   └── app.js       # Frontend JavaScript
│   └── visuals/         # Generated charts (auto-created)
└── project_data/        # Analysis data storage (auto-created)
```

## 🔧 API Endpoints

### POST `/analyze`
Analyzes a news topic and returns comprehensive results.

**Request:**
```json
{
  "topic": "FIFA World Cup"
}
```

**Response:**
```json
{
  "executive_summary": "Structured analysis summary...",
  "detailed_bias_report": "Article-by-article bias analysis...",
  "summary_evaluation": {
    "Faithfulness (BERTScore F1)": "0.85",
    "Relevance to Query": "0.92",
    "Readability (Flesch Score)": "65.2",
    "Coherence (Sentence Similarity)": "0.78"
  },
  "visualizations": {
    "historical_bias_chart_url": "/static/visuals/historical_bias_20241201_143022.png",
    "source_bias_chart_url": "/static/visuals/source_bias_20241201_143022.png"
  }
}
```

## 🎨 Frontend Features

### Design Philosophy
- **Modern Aesthetics**: Gradient backgrounds, glassmorphism effects, and smooth animations
- **User Experience**: Intuitive interface with clear visual hierarchy
- **Accessibility**: High contrast ratios and keyboard navigation support
- **Performance**: Optimized loading and smooth interactions

### Key Components
1. **Search Interface**: Clean form with placeholder examples and validation
2. **Loading States**: Animated spinner with informative progress messages
3. **Results Display**: 
   - Executive summary with markdown formatting
   - Metrics dashboard with visual indicators
   - Chart visualizations for bias analysis
   - Scrollable bias reports
4. **Error Handling**: Contextual error messages with recovery suggestions

### Responsive Design
- **Desktop**: Full-width layout with side-by-side charts
- **Tablet**: Adaptive grid layouts
- **Mobile**: Stacked layout with optimized touch targets

## 🔍 Analysis Capabilities

### News Processing Pipeline
1. **Article Collection**: Fetches 25 relevant articles from NewsAPI
2. **Content Extraction**: Uses trafilatura for clean text extraction
3. **RAG Processing**: Creates embeddings and retrieves relevant context
4. **Summarization**: Generates structured summaries using T5 model
5. **Bias Analysis**: Performs sentiment and subjectivity analysis
6. **Visualization**: Creates charts for bias evolution and source analysis

### Quality Metrics
- **Faithfulness**: BERTScore F1 for summary accuracy
- **Relevance**: Token overlap with query
- **Readability**: Flesch reading ease score
- **Coherence**: Sentence similarity analysis

## 🛠️ Technical Stack

### Backend
- **Flask**: Web framework
- **NewsAPI**: News article fetching
- **Transformers**: Hugging Face models for NLP
- **ChromaDB**: Vector database for RAG
- **Matplotlib**: Data visualization
- **spaCy**: NLP processing
- **TextBlob**: Sentiment analysis

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **JavaScript (ES6+)**: Interactive functionality
- **Bootstrap 5**: Responsive framework
- **Font Awesome**: Icon library

## 🔧 Configuration

### Environment Variables
- `NEWS_API_KEY`: Your NewsAPI key (required)

### File Paths (config.py)
- `PROJECT_DATA_PATH`: Directory for analysis data
- `VISUALS_PATH`: Directory for generated charts

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set `debug=False` in app.py
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure reverse proxy (Nginx)
4. Set up environment variables securely

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NewsAPI for news data
- Hugging Face for NLP models
- The open-source community for various libraries and tools

---

**BharatLens** - Empowering informed decision-making through advanced news analysis. 