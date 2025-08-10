"""
In-Memory Dossier Generator
Processes scraped content in memory to create comprehensive company dossiers
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import io

# PDF processing
import PyPDF2

# Text processing
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# HTML processing
from bs4 import BeautifulSoup

# AI/LLM integration
from openai import OpenAI
import os
from dotenv import load_dotenv

# Import global configuration
from osint_toolkit.utils.config import config

load_dotenv()

@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    source_url: str
    chunk_id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    summary: str = ""

@dataclass
class CompanyDossier:
    """Structured company dossier following business intelligence proforma"""
    company_name: str
    
    # 9 Business Intelligence Sections
    company_identity_and_purpose: str
    products_and_services_offered: str
    customer_and_stakeholder_landscape: str
    core_business_activities_and_processes: str
    organisational_structure_and_functions: str
    channels_and_customer_interactions: str
    compliance_and_regulatory_context: str
    technology_landscape: str
    strategic_priorities_and_data_challenges: str
    
    # Metadata
    sources: List[str]
    last_updated: str

class InMemoryDossierGenerator:
    """Generate dossiers from in-memory scraped content"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200, max_context_tokens: int = 4000):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_context_tokens = max_context_tokens
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Storage for processed data
        self.chunks: List[DocumentChunk] = []
        self.document_summaries: Dict[str, str] = {}
    
    def check_api_configuration(self) -> Dict[str, Any]:
        """Check if OpenAI API is properly configured"""
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return {
                "configured": False,
                "status": "No API key found",
                "suggestions": [
                    "Create a .env file in your project directory",
                    "Add your OpenAI API key: OPENAI_API_KEY=sk-your-key-here",
                    "Restart the application"
                ]
            }
        
        if not api_key.startswith('sk-'):
            return {
                "configured": False,
                "status": "Invalid API key format",
                "suggestions": [
                    "Check your API key format (should start with 'sk-')",
                    "Get a valid API key from https://platform.openai.com/",
                    "Update your .env file with the correct key"
                ]
            }
        
        # Test API connection
        try:
            client = OpenAI(api_key=api_key)
            # Simple test call
            models = client.models.list()
            return {
                "configured": True,
                "status": "API key valid and working",
                "suggestions": []
            }
        except Exception as e:
            return {
                "configured": False,
                "status": f"API connection failed: {str(e)}",
                "suggestions": [
                    "Check your internet connection",
                    "Verify your API key is active",
                    "Check OpenAI service status"
                ]
            }
    
    async def generate_dossier_from_memory(self, 
                                         html_content: Dict[str, Any], 
                                         pdf_content: Dict[str, Any],
                                         company_name: str,
                                         progress_callback: Optional[callable] = None) -> CompanyDossier:
        """
        Generate a comprehensive dossier from in-memory content
        
        Args:
            html_content: Dictionary of HTML content from scraper
            pdf_content: Dictionary of PDF content from scraper
            company_name: Name of the company for the dossier
            progress_callback: Optional callback for progress updates
            
        Returns:
            CompanyDossier object with all sections filled
        """
        if progress_callback:
            progress_callback("Processing content...")
        
        # Process all content into chunks
        await self._process_content_to_chunks(html_content, pdf_content, progress_callback)
        
        if progress_callback:
            progress_callback("Clustering content by topics...")
        
        # Cluster content by semantic similarity
        clustered_chunks = self._cluster_content()
        
        if progress_callback:
            progress_callback("Generating dossier sections...")
        
        # Generate each section of the dossier
        dossier_sections = await self._generate_all_sections(clustered_chunks, company_name, progress_callback)
        
        # Create final dossier
        sources = list(html_content.keys()) + list(pdf_content.keys())
        
        dossier = CompanyDossier(
            company_name=company_name,
            sources=sources,
            last_updated=datetime.now().isoformat(),
            **dossier_sections
        )
        
        if progress_callback:
            progress_callback("Dossier generation complete!")
        
        return dossier
    
    async def _process_content_to_chunks(self, html_content: Dict, pdf_content: Dict, progress_callback: Optional[callable] = None):
        """Process all content into semantic chunks"""
        self.chunks.clear()
        total_items = len(html_content) + len(pdf_content)
        processed = 0
        
        # Process HTML content
        for url, content_data in html_content.items():
            text = content_data.get('text', '')
            if text:
                chunks = self._create_text_chunks(text, url, 'html', content_data.get('metadata', {}))
                self.chunks.extend(chunks)
            
            processed += 1
            if progress_callback:
                progress_callback(f"Processing content {processed}/{total_items}...")
        
        # Process PDF content
        for url, content_data in pdf_content.items():
            pdf_bytes = content_data.get('content', b'')
            if pdf_bytes:
                text = self._extract_text_from_pdf_bytes(pdf_bytes)
                if text:
                    chunks = self._create_text_chunks(text, url, 'pdf', {'size': content_data.get('size', 0)})
                    self.chunks.extend(chunks)
            
            processed += 1
            if progress_callback:
                progress_callback(f"Processing content {processed}/{total_items}...")
    
    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                try:
                    text += page.extract_text() + "\n"
                except Exception:
                    continue
            
            return text.strip()
        except Exception:
            return ""
    
    def _create_text_chunks(self, text: str, source_url: str, doc_type: str, metadata: Dict) -> List[DocumentChunk]:
        """Create overlapping chunks from text"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:  # Skip very short content
            return []
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Create embedding
            embedding = self.embedding_model.encode(chunk_text)
            
            # Create chunk ID
            chunk_id = hashlib.md5(f"{source_url}_{i}".encode()).hexdigest()[:8]
            
            chunk = DocumentChunk(
                source_url=source_url,
                chunk_id=chunk_id,
                content=chunk_text,
                embedding=embedding,
                metadata={
                    **metadata,
                    'type': doc_type,
                    'chunk_index': len(chunks),
                    'word_count': len(chunk_words)
                }
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _cluster_content(self, max_clusters: int = 8) -> Dict[int, List[DocumentChunk]]:
        """Cluster chunks by semantic similarity"""
        if not self.chunks:
            return {}
        
        # Get embeddings
        embeddings = np.array([chunk.embedding for chunk in self.chunks])
        
        # Determine optimal number of clusters
        n_clusters = min(max_clusters, len(self.chunks))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group chunks by cluster
        clustered_chunks = {}
        for chunk, label in zip(self.chunks, cluster_labels):
            if label not in clustered_chunks:
                clustered_chunks[label] = []
            clustered_chunks[label].append(chunk)
        
        return clustered_chunks
    
    async def _generate_all_sections(self, clustered_chunks: Dict, company_name: str, progress_callback: Optional[callable]) -> Dict[str, str]:
        """Generate all 9 sections of the business dossier"""
        
        # Prepare context from clustered content
        context_summary = self._prepare_context_summary(clustered_chunks)
        
        sections = {
            'company_identity_and_purpose': 'Company Identity and Purpose',
            'products_and_services_offered': 'Products and Services Offered',
            'customer_and_stakeholder_landscape': 'Customer and Stakeholder Landscape',
            'core_business_activities_and_processes': 'Core Business Activities and Processes',
            'organisational_structure_and_functions': 'Organisational Structure and Functions',
            'channels_and_customer_interactions': 'Channels and Customer Interactions',
            'compliance_and_regulatory_context': 'Compliance and Regulatory Context',
            'technology_landscape': 'Technology Landscape',
            'strategic_priorities_and_data_challenges': 'Strategic Priorities and Data Challenges'
        }
        
        results = {}
        total_sections = len(sections)
        
        for i, (section_key, section_title) in enumerate(sections.items()):
            if progress_callback:
                progress_callback(f"Generating section {i+1}/{total_sections}: {section_title}")
            
            section_content = await self._generate_section(section_title, context_summary, company_name, progress_callback)
            results[section_key] = section_content
        
        return results
    
    def _prepare_context_summary(self, clustered_chunks: Dict) -> str:
        """Prepare a comprehensive but concise context summary"""
        summaries = []
        
        for cluster_id, chunks in clustered_chunks.items():
            # Get representative content from each cluster
            cluster_content = []
            for chunk in chunks[:3]:  # Top 3 chunks per cluster
                cluster_content.append(chunk.content[:300])  # First 300 chars
            
            cluster_summary = f"Topic Cluster {cluster_id + 1}:\n" + "\n".join(cluster_content)
            summaries.append(cluster_summary)
        
        return "\n\n".join(summaries)
    
    async def _generate_section(self, section_title: str, context: str, company_name: str, progress_callback: Optional[callable]) -> str:
        """Generate a specific section using AI"""
        
        prompt = f"""
Based on the following content about {company_name}, provide a comprehensive analysis for the section "{section_title}".

CONTENT:
{context[:self.max_context_tokens * 3]}

INSTRUCTIONS:
- Focus specifically on "{section_title}"
- Provide detailed, factual information
- Use bullet points and clear structure
- Include specific examples where available
- Be comprehensive but concise
- If information is limited, state what is known and what is unclear

SECTION: {section_title}
"""

        try:
            # Get API key and create client
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return f"Error: OpenAI API key not configured"
            
            client = OpenAI(api_key=api_key)
            
            # Determine model: environment variable (OPENAI_MODEL) or config default
            model_name = os.getenv("OPENAI_MODEL") or getattr(config, "OPENAI_MODEL", "gpt-5-nano")

            # If using GPT-5 family, prefer Responses API with reasoning controls
            if model_name.startswith("gpt-5"):
                try:
                    responses_kwargs = {
                        "model": model_name,
                        "input": prompt,
                        # Minimal reasoning for speed; can be adjusted via env
                        "reasoning": {"effort": os.getenv("OPENAI_REASONING_EFFORT", "minimal")},
                    }
                    verbosity = os.getenv("OPENAI_VERBOSITY")
                    if verbosity:
                        responses_kwargs["text"] = {"verbosity": verbosity}
                    # Optional max tokens control (new param name in GPT-5 stack)
                    max_comp = os.getenv("OPENAI_MAX_COMPLETION_TOKENS")
                    if max_comp:
                        responses_kwargs["max_output_tokens"] = int(max_comp)
                    resp = client.responses.create(**responses_kwargs)

                    # Robust extraction of text from Responses API output
                    try:
                        # New style: resp.output is a list of objects with .content
                        parts = []
                        output = getattr(resp, "output", []) or []
                        for item in output:
                            content_list = getattr(item, "content", [])
                            for c in content_list:
                                ctype = getattr(c, "type", None)
                                if ctype in ("output_text", "text"):
                                    text_obj = getattr(c, "text", None)
                                    if isinstance(text_obj, str):
                                        parts.append(text_obj)
                                    else:
                                        value = getattr(text_obj, "value", None)
                                        if value:
                                            parts.append(value)
                        if parts:
                            return "\n".join(parts).strip()
                        # Fallback: maybe top-level content
                        fallback_text = getattr(resp, "content", None)
                        if isinstance(fallback_text, str):
                            return fallback_text.strip()
                        # Last resort: repr
                        return str(resp)
                    except Exception as parse_err:
                        return f"Error parsing GPT-5 response: {parse_err}"
                except Exception as gpt5_err:
                    # Fallback to legacy chat if Responses API fails
                    pass  # Will attempt legacy path below

            # Legacy / non GPT-5 path via Chat Completions (remove unsupported params for GPT-5 models)
            chat_kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a business intelligence analyst creating detailed company dossiers."},
                    {"role": "user", "content": prompt}
                ],
            }
            # Only include completion/temperature style params if not GPT-5 nano (which rejects them)
            if not model_name.startswith("gpt-5"):
                chat_kwargs["max_completion_tokens"] = 800
                chat_kwargs["temperature"] = 0.3
            response = client.chat.completions.create(**chat_kwargs)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating section: {str(e)}"
    
    def export_dossier(self, dossier: CompanyDossier) -> Dict[str, str]:
        """Export dossier in multiple formats"""
        
        # JSON export
        json_content = json.dumps(asdict(dossier), indent=2)
        
        # HTML export
        html_content = self._generate_html_report(dossier)
        
        return {
            'json': json_content,
            'html': html_content
        }
    
    def _generate_html_report(self, dossier: CompanyDossier) -> str:
        """Generate a professional HTML report"""
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dossier.company_name} - Business Intelligence Dossier</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }}
        .section {{ margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #3498db; }}
        .metadata {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .sources {{ font-size: 0.9em; color: #6c757d; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 {dossier.company_name}</h1>
        <p><strong>Business Intelligence Dossier</strong></p>
        
        <div class="metadata">
            <strong>Generated:</strong> {dossier.last_updated}<br>
            <strong>Sources:</strong> {len(dossier.sources)} documents analyzed
        </div>
        
        <div class="section">
            <h2>1. Company Identity and Purpose</h2>
            <pre>{dossier.company_identity_and_purpose}</pre>
        </div>
        
        <div class="section">
            <h2>2. Products and Services Offered</h2>
            <pre>{dossier.products_and_services_offered}</pre>
        </div>
        
        <div class="section">
            <h2>3. Customer and Stakeholder Landscape</h2>
            <pre>{dossier.customer_and_stakeholder_landscape}</pre>
        </div>
        
        <div class="section">
            <h2>4. Core Business Activities and Processes</h2>
            <pre>{dossier.core_business_activities_and_processes}</pre>
        </div>
        
        <div class="section">
            <h2>5. Organisational Structure and Functions</h2>
            <pre>{dossier.organisational_structure_and_functions}</pre>
        </div>
        
        <div class="section">
            <h2>6. Channels and Customer Interactions</h2>
            <pre>{dossier.channels_and_customer_interactions}</pre>
        </div>
        
        <div class="section">
            <h2>7. Compliance and Regulatory Context</h2>
            <pre>{dossier.compliance_and_regulatory_context}</pre>
        </div>
        
        <div class="section">
            <h2>8. Technology Landscape</h2>
            <pre>{dossier.technology_landscape}</pre>
        </div>
        
        <div class="section">
            <h2>9. Strategic Priorities and Data Challenges</h2>
            <pre>{dossier.strategic_priorities_and_data_challenges}</pre>
        </div>
        
        <div class="sources">
            <h3>Sources Analyzed:</h3>
            <ul>
                {"".join(f"<li>{source}</li>" for source in dossier.sources)}
            </ul>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
