# OSINT Dossier Generator

An intelligent system for processing large volumes of scraped PDFs to generate comprehensive company dossiers. Solves the challenge of analyzing hundreds of documents while respecting AI model context window limitations.

## 🚀 Key Features

- **Hierarchical Summarization**: Processes PDFs in chunks, clusters by topic, then generates summaries
- **Semantic Search**: Uses embeddings to find relevant information across documents
- **Context Window Management**: Intelligently handles large document sets within AI model limits
- **Multiple Output Formats**: JSON for data processing, HTML for human-readable reports
- **Streamlit UI**: User-friendly interface for generating and viewing dossiers
- **CLI Support**: Command-line interface for automated processing

## 🏗️ Architecture

### The Challenge
- Processing 100+ PDFs can exceed AI context windows (4K-32K tokens)
- Individual PDF processing loses cross-document insights
- Manual review of hundreds of documents is impractical

### The Solution
1. **PDF Text Extraction**: Extract text from all PDFs
2. **Intelligent Chunking**: Split documents into overlapping chunks (1000 words)
3. **Semantic Embedding**: Generate vector embeddings for each chunk
4. **Topic Clustering**: Group related chunks using K-means clustering
5. **Hierarchical Summarization**: Summarize clusters, then create executive summary
6. **Targeted Extraction**: Use semantic search for specific information types
7. **Structured Output**: Generate comprehensive dossier in multiple formats

## 🛠️ Installation

1. **Clone and setup virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure API access**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Required API Keys**:
   - OpenAI API key (or configure alternative LLM provider)
   - Modify `dossier_generator.py` to use your preferred AI service

## 📊 Usage

### Web Interface (Recommended)
```bash
./run.sh dossier
# Or: streamlit run dossier_ui.py
```

### Command Line Interface
```bash
python cli_dossier.py www.example.com --format both --output-dir results
```

### Python API
```python
from dossier_generator import DossierGenerator

generator = DossierGenerator()
dossier = generator.generate_company_dossier("www.example.com")
generator.save_dossier(dossier, "output.json")
```

## 📁 File Structure

```
OSINT/
├── dossier_generator.py    # Main dossier generation logic
├── dossier_ui.py          # Streamlit web interface
├── cli_dossier.py         # Command-line interface
├── downloads/             # Scraped content (input)
│   └── www.example.com/
│       └── pdfs/          # PDF files to process
├── dossiers/              # Generated dossiers (output)
├── requirements.txt       # Python dependencies
└── .env.example          # Configuration template
```

## 🔧 Configuration Options

### Processing Parameters
- **Chunk Size**: Text chunk size (500-2000 words)
- **Chunk Overlap**: Overlap between chunks (100-500 words)  
- **Max Clusters**: Number of topic clusters (3-15)
- **Context Tokens**: Maximum tokens per AI request (2000-8000)

### Output Sections
- Executive Summary
- Business Overview
- Financial Highlights
- Key Personnel
- Products & Services
- Locations
- Recent Developments
- Risk Factors

## 🧠 AI Model Integration

The system is designed to work with various AI providers:

### Currently Supported
- OpenAI GPT models (3.5-turbo, GPT-4)
- Easy to extend for other providers

### To Add New Provider
1. Modify `_call_llm()` method in `DossierGenerator`
2. Add API configuration to `.env`
3. Update requirements.txt with new dependencies

Example for Anthropic Claude:
```python
def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

## 📈 Performance Optimization

### For Large Document Sets (100+ PDFs)
1. **Batch Processing**: Process in chunks of 50-100 documents
2. **Parallel Processing**: Use multiprocessing for PDF text extraction
3. **Caching**: Cache embeddings and summaries for reprocessing
4. **GPU Acceleration**: Use GPU for embedding generation if available

### Memory Management
- Stream process large PDFs
- Use generators for chunk processing
- Clear embeddings from memory after clustering

## 🔍 Example Output

```json
{
  "company_name": "ABN Group",
  "executive_summary": "ABN Group is a diversified construction and property development company...",
  "business_overview": "The company operates through multiple subsidiaries...",
  "financial_highlights": "Revenue of $X million in latest period...",
  "key_personnel": ["John Smith, CEO", "Jane Doe, CFO"],
  "products_services": ["Home construction", "Property development"],
  "locations": ["Perth, WA", "Melbourne, VIC"],
  "sources": ["annual_report.pdf", "investor_presentation.pdf"],
  "last_updated": "2025-07-21T10:30:00"
}
```

## 🚨 Error Handling

### Common Issues
1. **No PDFs Found**: Ensure PDFs are in `downloads/domain/pdfs/` directory
2. **API Rate Limits**: Implement backoff strategy in `_call_llm()`
3. **Memory Issues**: Reduce chunk size or process fewer documents
4. **PDF Extraction Errors**: Some PDFs may be scanned images (consider OCR)

### Debugging
- Enable verbose logging in `DossierGenerator`
- Check embedding model loading
- Verify API key configuration
- Test with smaller document sets first

## 🔒 Security Considerations

- Store API keys in `.env` file (never commit to git)
- Consider data privacy when using cloud AI services
- Implement rate limiting for API calls
- Sanitize file paths to prevent directory traversal

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

### Extending the System
- Add new extraction patterns for specific information types
- Implement industry-specific dossier templates
- Add data visualization components
- Integrate with additional data sources

## 📝 License

[Your License Here]

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review error logs in the terminal
3. Ensure all dependencies are installed correctly
4. Verify API key configuration
