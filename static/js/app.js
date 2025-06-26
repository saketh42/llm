// BharatLens Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const analysisForm = document.getElementById('analysisForm');
    const topicInput = document.getElementById('topicInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');

    // Form submission handler
    analysisForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const topic = topicInput.value.trim();
        if (!topic) return;

        // Show loading, hide results
        loadingIndicator.style.display = 'block';
        resultsSection.style.display = 'none';
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic })
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data);
            } else {
                showError(data.error || 'Analysis failed. Please try again.');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            loadingIndicator.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    });

    // Enter key handler
    topicInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analysisForm.dispatchEvent(new Event('submit'));
        }
    });

    // Display analysis results
    function displayResults(data) {
        // Display Perspectives
        const perspectivesSection = document.getElementById('perspectivesSection');
        const perspectivesCards = document.getElementById('perspectivesCards');
        perspectivesCards.innerHTML = '';
        if (data.perspectives && data.perspectives.length > 0) {
            data.perspectives.forEach(p => {
                const card = document.createElement('div');
                card.className = 'col-md-6 mb-3';
                card.innerHTML = `
                    <div class="card h-100 shadow-sm">
                        <div class="card-body">
                            <h5 class="card-title">${p.label}</h5>
                            <p class="card-text">${formatSummary(p.summary)}</p>
                        </div>
                    </div>
                `;
                perspectivesCards.appendChild(card);
            });
            perspectivesSection.style.display = 'block';
        } else {
            perspectivesSection.style.display = 'none';
        }

        // Display Executive Summary
        const summaryDiv = document.getElementById('executiveSummary');
        summaryDiv.innerHTML = formatSummary(data.executive_summary);

        // Display Evaluation Metrics
        const metricsDiv = document.getElementById('evaluationMetrics');
        metricsDiv.innerHTML = '';
        
        if (data.summary_evaluation) {
            Object.entries(data.summary_evaluation).forEach(([metric, score]) => {
                const metricDiv = document.createElement('div');
                metricDiv.className = 'evaluation-item';
                metricDiv.innerHTML = `
                    <div class="evaluation-score">${score}</div>
                    <div>${metric}</div>
                `;
                metricsDiv.appendChild(metricDiv);
            });
        }

        // Display Visualizations
        if (data.visualizations) {
            const historicalDiv = document.getElementById('historicalChart');
            const sourceDiv = document.getElementById('sourceChart');
            
            if (data.visualizations.historical_bias_chart_url) {
                historicalDiv.innerHTML = `<img src="${data.visualizations.historical_bias_chart_url}" alt="Historical Bias Chart">`;
            }
            
            if (data.visualizations.source_bias_chart_url) {
                sourceDiv.innerHTML = `<img src="${data.visualizations.source_bias_chart_url}" alt="Source Bias Chart">`;
            }
        }

        // Display Bias Report
        const biasDiv = document.getElementById('biasReport');
        biasDiv.textContent = data.detailed_bias_report || 'No bias report available.';

        // Show results
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Format summary text with markdown-like formatting
    function formatSummary(summary) {
        if (!summary) return '<p>No summary available.</p>';
        
        // Convert markdown-like formatting to HTML
        return summary
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/^(\d+\.\s*)/gm, '<br><strong>$1</strong>');
    }

    // Show error message
    function showError(message) {
        resultsSection.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i> ${message}
            </div>
        `;
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Add some UI enhancements
    topicInput.addEventListener('input', function() {
        if (this.value.trim()) {
            analyzeBtn.classList.add('btn-primary');
        } else {
            analyzeBtn.classList.remove('btn-primary');
        }
    });

    // Add tooltips for better UX
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 