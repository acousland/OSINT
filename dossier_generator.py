"""
OSINT Dossier Generator
Processes large volumes of scraped PDFs to create comprehensive company dossiers
Uses hierarchical summarization and semantic chunking to handle context window limitations
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# PDF and text processing
import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# AI/LLM integration (you can adapt this to your preferred provider)
import openai  # or any other LLM provider

@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    source_file: str
    chunk_id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    summary: str = ""

@dataclass
class CompanyDossier:
    """Structured company dossier"""
    company_name: str
    executive_summary: str
    business_overview: str
    financial_highlights: str
    key_personnel: List[str]
    products_services: List[str]
    locations: List[str]
    recent_developments: List[str]
    risk_factors: List[str]
    competitive_position: str
    sources: List[str]
    last_updated: str

class DossierGenerator:
    def __init__(self, downloads_dir: str = "downloads", chunk_size: int = 1000, 
                 overlap: int = 200, max_context_tokens: int = 4000):
        self.downloads_dir = Path(downloads_dir)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_context_tokens = max_context_tokens
        
        # Initialize embedding model (lightweight but effective)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Storage for processed data
        self.chunks: List[DocumentChunk] = []
        self.document_summaries: Dict[str, str] = {}
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, source_file: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            if len(chunk_text.strip()) > 50:  # Skip very small chunks
                chunks.append(chunk_text)
                
        return chunks
    
    def create_chunk_id(self, content: str, source_file: str) -> str:
        """Create unique ID for chunk"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{Path(source_file).stem}_{content_hash}"
    
    def process_pdfs(self, company_domain: str = None, pdf_directory: str = None) -> None:
        """Process all PDFs for a specific company domain or from a custom directory"""
        if pdf_directory:
            # Use custom PDF directory
            pdf_dir = Path(pdf_directory)
            company_name = pdf_dir.name  # Use directory name as company identifier
        else:
            # Use standard scraped structure
            company_dir = self.downloads_dir / company_domain / "pdfs"
            pdf_dir = company_dir
            company_name = company_domain
        
        if not pdf_dir.exists():
            print(f"No PDFs found at {pdf_dir}")
            return
            
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"Processing {len(pdf_files)} PDF files from {pdf_dir}...")
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_file)
            if not text:
                continue
                
            # Create chunks
            text_chunks = self.chunk_text(text, str(pdf_file))
            
            # Process each chunk
            for chunk_text in text_chunks:
                # Create embedding
                embedding = self.embedding_model.encode(chunk_text)
                
                # Create chunk object
                chunk = DocumentChunk(
                    source_file=str(pdf_file),
                    chunk_id=self.create_chunk_id(chunk_text, str(pdf_file)),
                    content=chunk_text,
                    embedding=embedding,
                    metadata={
                        "file_name": pdf_file.name,
                        "company_domain": company_name,
                        "chunk_length": len(chunk_text),
                        "processed_at": datetime.now().isoformat()
                    }
                )
                
                self.chunks.append(chunk)
        
        print(f"Created {len(self.chunks)} chunks from {len(pdf_files)} PDFs")
    
    def summarize_document(self, text: str, file_name: str) -> str:
        """Create summary of individual document"""
        # Truncate if too long for context window
        max_chars = self.max_context_tokens * 3  # Rough estimate
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            
        prompt = f"""
        Summarize the following document from {file_name} in 2-3 paragraphs, focusing on:
        - Key business information
        - Financial data
        - Important dates and events
        - Personnel or organizational changes
        
        Document content:
        {text}
        
        Summary:
        """
        
        # Replace with your preferred LLM API call
        return self._call_llm(prompt, max_tokens=300)
    
    def find_relevant_chunks(self, query: str, top_k: int = 10) -> List[DocumentChunk]:
        """Find most relevant chunks for a given query"""
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate similarities
        similarities = []
        for chunk in self.chunks:
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                chunk.embedding.reshape(1, -1)
            )[0][0]
            similarities.append((similarity, chunk))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in similarities[:top_k]]
    
    def cluster_chunks_by_topic(self, n_clusters: int = 8) -> Dict[int, List[DocumentChunk]]:
        """Cluster chunks by semantic similarity to identify topics"""
        if len(self.chunks) < n_clusters:
            n_clusters = max(1, len(self.chunks) // 2)
        
        # Get embeddings
        embeddings = np.array([chunk.embedding for chunk in self.chunks])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group chunks by cluster
        clusters = {}
        for i, chunk in enumerate(self.chunks):
            cluster_id = cluster_labels[i]
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(chunk)
        
        return clusters
    
    def generate_topic_summary(self, chunks: List[DocumentChunk], topic_name: str) -> str:
        """Generate summary for a cluster of related chunks"""
        # Combine chunk contents, respecting context window
        combined_text = ""
        for chunk in chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += f"\n--- From {chunk.metadata['file_name']} ---\n"
                combined_text += chunk.content + "\n"
        
        prompt = f"""
        Analyze the following related content about {topic_name} and provide a comprehensive summary:
        
        {combined_text}
        
        Summary:
        """
        
        return self._call_llm(prompt, max_tokens=500)
    
    def generate_company_dossier(self, company_domain: str = None, pdf_directory: str = None, company_name: str = None) -> CompanyDossier:
        """Generate comprehensive company dossier"""
        print("Generating company dossier...")
        
        # Process PDFs if not already done
        if not self.chunks:
            self.process_pdfs(company_domain=company_domain, pdf_directory=pdf_directory)
        
        # Determine company name
        if company_name:
            final_company_name = company_name
        elif pdf_directory:
            final_company_name = Path(pdf_directory).name
        elif company_domain:
            final_company_name = company_domain.replace("www.", "").replace(".com", "").replace(".au", "")
        else:
            final_company_name = "Unknown Company"
        
        # Cluster chunks by topic
        clusters = self.cluster_chunks_by_topic()
        
        # Generate topic summaries
        topic_summaries = {}
        for cluster_id, chunks in clusters.items():
            topic_name = f"Topic_{cluster_id}"
            summary = self.generate_topic_summary(chunks, topic_name)
            topic_summaries[topic_name] = summary
        
        # Extract specific information using targeted queries
        business_overview = self._extract_business_info()
        financial_info = self._extract_financial_info()
        personnel_info = self._extract_personnel_info()
        locations = self._extract_locations()
        products_services = self._extract_products_services()
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(topic_summaries)
        
        # Create dossier
        dossier = CompanyDossier(
            company_name=final_company_name,
            executive_summary=exec_summary,
            business_overview=business_overview,
            financial_highlights=financial_info,
            key_personnel=personnel_info,
            products_services=products_services,
            locations=locations,
            recent_developments=[],  # Could be extracted with date-aware analysis
            risk_factors=[],  # Could be extracted with risk-focused queries
            competitive_position="",  # Could be extracted with competitor analysis
            sources=[chunk.source_file for chunk in self.chunks],
            last_updated=datetime.now().isoformat()
        )
        
        return dossier
    
    def _extract_business_info(self) -> str:
        """Extract business overview information"""
        relevant_chunks = self.find_relevant_chunks(
            "business model company overview services products operations", 
            top_k=5
        )
        
        content = "\n".join([chunk.content for chunk in relevant_chunks])
        if not content:
            return "No business information found in available documents."
            
        prompt = f"""
        Based on the following content, provide a business overview:
        
        {content[:self.max_context_tokens * 3]}
        
        Business Overview:
        """
        
        return self._call_llm(prompt, max_tokens=400)
    
    def _extract_financial_info(self) -> str:
        """Extract financial information"""
        relevant_chunks = self.find_relevant_chunks(
            "revenue profit financial results earnings quarterly annual", 
            top_k=5
        )
        
        content = "\n".join([chunk.content for chunk in relevant_chunks])
        if not content:
            return "No financial information found in available documents."
            
        prompt = f"""
        Extract key financial highlights from the following content:
        
        {content[:self.max_context_tokens * 3]}
        
        Financial Highlights:
        """
        
        return self._call_llm(prompt, max_tokens=300)
    
    def _extract_personnel_info(self) -> List[str]:
        """Extract key personnel information"""
        relevant_chunks = self.find_relevant_chunks(
            "CEO president director manager executive leadership team", 
            top_k=3
        )
        
        personnel = []
        for chunk in relevant_chunks:
            # Simple pattern matching for names and titles
            pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)(?:,?\s+(?:CEO|President|Director|Manager|CFO|COO|CTO))'
            matches = re.findall(pattern, chunk.content)
            personnel.extend(matches)
        
        return list(set(personnel))  # Remove duplicates
    
    def _extract_locations(self) -> List[str]:
        """Extract company locations"""
        relevant_chunks = self.find_relevant_chunks(
            "office location address headquarters branch facility", 
            top_k=3
        )
        
        locations = []
        for chunk in relevant_chunks:
            # Pattern for locations (simplified)
            pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:, [A-Z]{2,3})?)'
            matches = re.findall(pattern, chunk.content)
            locations.extend([match for match in matches if len(match) > 3])
        
        return list(set(locations))[:10]  # Limit and remove duplicates
    
    def _extract_products_services(self) -> List[str]:
        """Extract products and services"""
        relevant_chunks = self.find_relevant_chunks(
            "product service offering solution platform software", 
            top_k=3
        )
        
        products = []
        for chunk in relevant_chunks:
            # This would need more sophisticated NLP in practice
            lines = chunk.content.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ['product', 'service', 'solution']):
                    products.append(line.strip())
        
        return list(set(products))[:15]  # Limit and remove duplicates
    
    def _generate_executive_summary(self, topic_summaries: Dict[str, str]) -> str:
        """Generate executive summary from topic summaries"""
        combined_summaries = "\n\n".join(topic_summaries.values())
        
        prompt = f"""
        Based on the following topic summaries, create a concise executive summary of the company:
        
        {combined_summaries[:self.max_context_tokens * 3]}
        
        Executive Summary:
        """
        
        return self._call_llm(prompt, max_tokens=400)
    
    def check_api_configuration(self) -> Dict[str, Any]:
        """Check if API is properly configured"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        result = {
            "configured": False,
            "provider": "OpenAI",
            "status": "",
            "suggestions": []
        }
        
        if not api_key:
            result["status"] = "No API key found"
            result["suggestions"] = [
                "Create a .env file in the project root",
                "Add: OPENAI_API_KEY=your_actual_api_key_here",
                "Get your API key from: https://platform.openai.com/api-keys"
            ]
            return result
        
        if api_key == "your_openai_api_key_here":
            result["status"] = "Default placeholder API key detected"
            result["suggestions"] = [
                "Replace the placeholder with your actual OpenAI API key",
                "Get your API key from: https://platform.openai.com/api-keys"
            ]
            return result
        
        if len(api_key) < 20:
            result["status"] = "API key appears to be too short"
            result["suggestions"] = [
                "Check that you copied the complete API key",
                "OpenAI API keys typically start with 'sk-' and are much longer"
            ]
            return result
        
        result["configured"] = True
        result["status"] = "API key configured"
        return result
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Call LLM API - configured to use environment variables
        """
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return "[ERROR: No API key configured. Please set OPENAI_API_KEY in your .env file]"
        
        try:
            # Set the API key
            openai.api_key = api_key
            
            # Call OpenAI API (using the newer client format)
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            # Fallback for older OpenAI library versions
            try:
                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"[ERROR: OpenAI API call failed: {str(e)}]"
                
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower():
                return "[ERROR: Invalid API key. Please check your OPENAI_API_KEY in the .env file]"
            elif "quota" in error_msg.lower():
                return "[ERROR: API quota exceeded. Please check your OpenAI account billing]"
            elif "rate" in error_msg.lower():
                return "[ERROR: Rate limit exceeded. Please wait and try again]"
            else:
                return f"[ERROR: OpenAI API call failed: {error_msg}]"
    
    def save_dossier(self, dossier: CompanyDossier, output_path: str) -> None:
        """Save dossier to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(asdict(dossier), f, indent=2, default=str)
        print(f"Dossier saved to {output_path}")
    
    def export_dossier_html(self, dossier: CompanyDossier, output_path: str) -> None:
        """Export dossier as HTML report"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Company Dossier - {dossier.company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .section {{ margin-bottom: 30px; }}
                .list-item {{ margin-bottom: 5px; }}
                .metadata {{ color: #7f8c8d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>Company Dossier: {dossier.company_name}</h1>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="summary">{dossier.executive_summary}</div>
            </div>
            
            <div class="section">
                <h2>Business Overview</h2>
                <p>{dossier.business_overview}</p>
            </div>
            
            <div class="section">
                <h2>Financial Highlights</h2>
                <p>{dossier.financial_highlights}</p>
            </div>
            
            <div class="section">
                <h2>Key Personnel</h2>
                <ul>
                    {"".join([f"<li class='list-item'>{person}</li>" for person in dossier.key_personnel])}
                </ul>
            </div>
            
            <div class="section">
                <h2>Products & Services</h2>
                <ul>
                    {"".join([f"<li class='list-item'>{item}</li>" for item in dossier.products_services[:10]])}
                </ul>
            </div>
            
            <div class="section">
                <h2>Locations</h2>
                <ul>
                    {"".join([f"<li class='list-item'>{location}</li>" for location in dossier.locations[:10]])}
                </ul>
            </div>
            
            <div class="metadata">
                <p>Generated on: {dossier.last_updated}</p>
                <p>Sources: {len(set(dossier.sources))} documents processed</p>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_template)
        print(f"HTML report saved to {output_path}")

def main():
    """Example usage"""
    generator = DossierGenerator()
    
    # Generate dossier for ABN Group
    dossier = generator.generate_company_dossier("www.abngroup.com.au")
    
    # Save results
    generator.save_dossier(dossier, "abngroup_dossier.json")
    generator.export_dossier_html(dossier, "abngroup_dossier.html")
    
    print("Dossier generation complete!")

if __name__ == "__main__":
    main()
