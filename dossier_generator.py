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

# HTML processing
from bs4 import BeautifulSoup
import lxml

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
    """Structured company dossier following business intelligence proforma"""
    company_name: str
    
    # 1. Company Identity and Purpose
    company_identity_and_purpose: str
    
    # 2. Products and Services Offered
    products_and_services_offered: str
    
    # 3. Customer and Stakeholder Landscape
    customer_and_stakeholder_landscape: str
    
    # 4. Core Business Activities and Processes
    core_business_activities_and_processes: str
    
    # 5. Organisational Structure and Functions
    organisational_structure_and_functions: str
    
    # 6. Channels and Customer Interactions
    channels_and_customer_interactions: str
    
    # 7. Compliance and Regulatory Context
    compliance_and_regulatory_context: str
    
    # 8. Technology Landscape
    technology_landscape: str
    
    # 9. Strategic Priorities and Data Challenges
    strategic_priorities_and_data_challenges: str
    
    # Metadata
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
    
    def extract_text_from_html(self, html_path: Path) -> str:
        """Extract text content from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Try to use BeautifulSoup if available, otherwise use regex
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                # Get text and clean it
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
                
            except ImportError:
                # Fallback: Simple regex-based HTML tag removal
                import re
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', ' ', content)
                # Clean up whitespace
                text = ' '.join(text.split())
                return text
                
        except Exception as e:
            print(f"Error extracting text from {html_path}: {e}")
            return ""
    
    def load_html_metadata(self, html_path: Path) -> Dict[str, Any]:
        """Load metadata for HTML file if available"""
        metadata_path = html_path.parent / f"{html_path.stem}_metadata.json"
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading metadata for {html_path}: {e}")
            return {}
    
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
    
    def process_documents(self, company_domain: str = None, pdf_directory: str = None, html_directory: str = None) -> None:
        """Process all documents (PDFs and HTML) for a specific company domain or from custom directories"""
        if pdf_directory or html_directory:
            # Use custom directories
            company_name = Path(pdf_directory or html_directory).name
            pdf_dir = Path(pdf_directory) if pdf_directory else None
            html_dir = Path(html_directory) if html_directory else None
        else:
            # Use standard scraped structure
            company_dir = self.downloads_dir / company_domain
            pdf_dir = company_dir / "pdfs" if (company_dir / "pdfs").exists() else None
            html_dir = company_dir / "html_pages" if (company_dir / "html_pages").exists() else None
            company_name = company_domain
        
        total_files = 0
        processed_files = 0
        
        # Process PDF files
        if pdf_dir and pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            total_files += len(pdf_files)
            print(f"Processing {len(pdf_files)} PDF files from {pdf_dir}...")
            
            for pdf_file in pdf_files:
                print(f"Processing PDF: {pdf_file.name}")
                
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
                            "file_type": "pdf",
                            "processed_at": datetime.now().isoformat()
                        }
                    )
                    
                    self.chunks.append(chunk)
                
                processed_files += 1
        
        # Process HTML files
        if html_dir and html_dir.exists():
            html_files = list(html_dir.glob("*.html"))
            total_files += len(html_files)
            print(f"Processing {len(html_files)} HTML files from {html_dir}...")
            
            for html_file in html_files:
                print(f"Processing HTML: {html_file.name}")
                
                # Extract text
                text = self.extract_text_from_html(html_file)
                if not text or len(text) < 100:  # Skip very short content
                    continue
                    
                # Load metadata
                html_metadata = self.load_html_metadata(html_file)
                
                # Create chunks
                text_chunks = self.chunk_text(text, str(html_file))
                
                # Process each chunk
                for chunk_text in text_chunks:
                    # Create embedding
                    embedding = self.embedding_model.encode(chunk_text)
                    
                    # Create chunk object
                    chunk = DocumentChunk(
                        source_file=str(html_file),
                        chunk_id=self.create_chunk_id(chunk_text, str(html_file)),
                        content=chunk_text,
                        embedding=embedding,
                        metadata={
                            "file_name": html_file.name,
                            "company_domain": company_name,
                            "chunk_length": len(chunk_text),
                            "file_type": "html",
                            "url": html_metadata.get("url", ""),
                            "title": html_metadata.get("title", ""),
                            "content_type": html_metadata.get("content_type", ""),
                            "processed_at": datetime.now().isoformat()
                        }
                    )
                    
                    self.chunks.append(chunk)
                
                processed_files += 1
        
        print(f"Document processing complete:")
        print(f"  Total files found: {total_files}")
        print(f"  Files processed: {processed_files}")
        print(f"  Chunks created: {len(self.chunks)}")
        
        if total_files == 0:
            print(f"No documents found. Checked directories:")
            if pdf_dir:
                print(f"  PDF directory: {pdf_dir}")
            if html_dir:
                print(f"  HTML directory: {html_dir}")
    
    # Legacy method for backward compatibility
    def process_pdfs(self, company_domain: str = None, pdf_directory: str = None) -> None:
        """Legacy method - now calls process_documents for PDFs only"""
        self.process_documents(company_domain=company_domain, pdf_directory=pdf_directory)
    
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
    
    def generate_company_dossier(self, company_domain: str = None, pdf_directory: str = None, 
                               html_directory: str = None, company_name: str = None) -> CompanyDossier:
        """Generate comprehensive company dossier from PDFs and HTML content"""
        print("Generating company dossier...")
        
        # Process documents if not already done
        if not self.chunks:
            self.process_documents(
                company_domain=company_domain, 
                pdf_directory=pdf_directory, 
                html_directory=html_directory
            )
        
        # Determine company name
        if company_name:
            final_company_name = company_name
        elif pdf_directory:
            final_company_name = Path(pdf_directory).name
        elif html_directory:
            final_company_name = Path(html_directory).name
        elif company_domain:
            final_company_name = company_domain.replace("www.", "").replace(".com", "").replace(".au", "")
        else:
            final_company_name = "Unknown Company"
        
        if not self.chunks:
            print("No content found to process. Returning minimal dossier.")
            return CompanyDossier(
                company_name=final_company_name,
                company_identity_and_purpose="No content available for analysis of company identity and purpose.",
                products_and_services_offered="No information found about products and services.",
                customer_and_stakeholder_landscape="No customer or stakeholder information found.",
                core_business_activities_and_processes="No business activities or processes information found.",
                organisational_structure_and_functions="No organisational structure information found.",
                channels_and_customer_interactions="No customer interaction channels information found.",
                compliance_and_regulatory_context="No compliance or regulatory information found.",
                technology_landscape="No technology landscape information found.",
                strategic_priorities_and_data_challenges="No strategic priorities or data challenges information found.",
                sources=[],
                last_updated=datetime.now().isoformat()
            )
        
        # Show content breakdown
        pdf_chunks = len([c for c in self.chunks if c.metadata.get("file_type") == "pdf"])
        html_chunks = len([c for c in self.chunks if c.metadata.get("file_type") == "html"])
        print(f"Content breakdown: {pdf_chunks} PDF chunks, {html_chunks} HTML chunks")
        
        # Cluster chunks by topic
        clusters = self.cluster_chunks_by_topic()
        
        # Generate topic summaries
        topic_summaries = {}
        for cluster_id, chunks in clusters.items():
            topic_name = f"Topic_{cluster_id}"
            summary = self.generate_topic_summary(chunks, topic_name)
            topic_summaries[topic_name] = summary
        
        # Extract specific information using new proforma structure
        company_identity = self._extract_company_identity_and_purpose()
        products_services = self._extract_products_and_services()
        customer_stakeholder = self._extract_customer_and_stakeholder_landscape()
        business_activities = self._extract_core_business_activities()
        org_structure = self._extract_organisational_structure()
        channels_interactions = self._extract_channels_and_interactions()
        compliance_regulatory = self._extract_compliance_and_regulatory()
        technology_landscape = self._extract_technology_landscape()
        strategic_priorities = self._extract_strategic_priorities()
        
        # Create dossier using new proforma structure
        dossier = CompanyDossier(
            company_name=final_company_name,
            company_identity_and_purpose=company_identity,
            products_and_services_offered=products_services,
            customer_and_stakeholder_landscape=customer_stakeholder,
            core_business_activities_and_processes=business_activities,
            organisational_structure_and_functions=org_structure,
            channels_and_customer_interactions=channels_interactions,
            compliance_and_regulatory_context=compliance_regulatory,
            technology_landscape=technology_landscape,
            strategic_priorities_and_data_challenges=strategic_priorities,
            sources=[chunk.source_file for chunk in self.chunks],
            last_updated=datetime.now().isoformat()
        )
        
        return dossier
    
    def _extract_company_identity_and_purpose(self) -> str:
        """Extract company identity, mission, and primary objectives"""
        relevant_chunks = self.find_relevant_chunks(
            "company mission vision purpose objectives core business industry sector competitive advantage positioning",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No company identity information found in available documents."
        
        prompt = f"""
        Analyze the following content and provide a comprehensive overview of the company's identity and purpose:
        
        1. What the company does (core business activities)
        2. Mission and primary objectives
        3. Core industry or sector
        4. Special positioning or competitive differentiators
        
        Content:
        {combined_text}
        
        Company Identity and Purpose:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_products_and_services(self) -> str:
        """Extract products and services offered"""
        relevant_chunks = self.find_relevant_chunks(
            "products services offerings solutions portfolio categories lines hierarchy classification",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No products and services information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the company's products and services:
        
        1. Major categories or lines of products/services
        2. Product/service hierarchy or classification system
        3. Key offerings and their positioning
        4. Any specialized or unique solutions
        
        Content:
        {combined_text}
        
        Products and Services Offered:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_customer_and_stakeholder_landscape(self) -> str:
        """Extract customer and stakeholder information"""
        relevant_chunks = self.find_relevant_chunks(
            "customers clients stakeholders partners suppliers distributors segments retail business government",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No customer and stakeholder information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the customer and stakeholder landscape:
        
        1. Typical customers and their types/segments (retail, business, government)
        2. Key external stakeholders (partners, suppliers, distributors)
        3. Customer characteristics and segmentation
        4. Stakeholder relationships and dependencies
        
        Content:
        {combined_text}
        
        Customer and Stakeholder Landscape:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_core_business_activities(self) -> str:
        """Extract core business activities and processes"""
        relevant_chunks = self.find_relevant_chunks(
            "business activities processes operations sales manufacturing production service delivery financial management human resources workflow",
            top_k=20
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No core business activities information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the core business activities and processes:
        
        1. Primary value-creating activities or value streams
        2. Sales processes (marketing to order fulfillment)
        3. Manufacturing, production, or service delivery processes
        4. Financial management processes (billing, invoicing, payments)
        5. Human resource processes (hiring, payroll, management)
        6. Other business-critical processes and their flow
        
        Content:
        {combined_text}
        
        Core Business Activities and Processes:
        """
        
        return self._call_llm(prompt, max_tokens=1000)
    
    def _extract_organisational_structure(self) -> str:
        """Extract organisational structure and functions"""
        relevant_chunks = self.find_relevant_chunks(
            "organisational structure departments teams units functions roles collaboration management leadership divisions",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No organisational structure information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the organisational structure and functions:
        
        1. Organisational units, departments, or teams and their roles
        2. How units collaborate or exchange information
        3. Leadership structure and management hierarchy
        4. Functional groupings and their responsibilities
        
        Content:
        {combined_text}
        
        Organisational Structure and Functions:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_channels_and_interactions(self) -> str:
        """Extract channels and customer interactions"""
        relevant_chunks = self.find_relevant_chunks(
            "channels interactions customers touchpoints online physical locations call centres social media distributors sales",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No channels and customer interactions information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe channels and customer interactions:
        
        1. How customers and stakeholders interact with the company
        2. Online channels (websites, digital platforms, social media)
        3. Physical channels (locations, retail, offices)
        4. Service channels (call centres, support, distributors)
        5. Significant touchpoints and customer journey
        
        Content:
        {combined_text}
        
        Channels and Customer Interactions:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_compliance_and_regulatory(self) -> str:
        """Extract compliance and regulatory context"""
        relevant_chunks = self.find_relevant_chunks(
            "compliance regulatory regulation standards audits reporting obligations privacy financial safety legal requirements",
            top_k=12
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No compliance and regulatory information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the compliance and regulatory context:
        
        1. Important regulatory or compliance areas (privacy, financial reporting, safety)
        2. Critical compliance-related processes (audits, reporting obligations)
        3. Industry standards and requirements
        4. Regulatory bodies and oversight
        
        Content:
        {combined_text}
        
        Compliance and Regulatory Context:
        """
        
        return self._call_llm(prompt, max_tokens=600)
    
    def _extract_technology_landscape(self) -> str:
        """Extract technology landscape information"""
        relevant_chunks = self.find_relevant_chunks(
            "technology systems IT CRM ERP HR software platforms digital infrastructure cloud applications databases",
            top_k=15
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No technology landscape information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe the technology landscape:
        
        1. Core technology or IT systems in use (CRM, ERP, HR systems)
        2. Business processes each technology supports
        3. Digital platforms and infrastructure
        4. Technology integration and architecture
        
        Content:
        {combined_text}
        
        Technology Landscape:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
    def _extract_strategic_priorities(self) -> str:
        """Extract strategic priorities and data challenges"""
        relevant_chunks = self.find_relevant_chunks(
            "strategic priorities strategy data challenges integration analytics transformation digital future goals objectives",
            top_k=12
        )
        
        combined_text = ""
        for chunk in relevant_chunks:
            if len(combined_text) + len(chunk.content) < self.max_context_tokens * 3:
                combined_text += "\n" + chunk.content
        
        if not combined_text:
            return "No strategic priorities and data challenges information found in available documents."
        
        prompt = f"""
        Analyze the following content and describe strategic priorities and data challenges:
        
        1. Strategic data-related challenges or aspirations
        2. Data integration, standardisation, or analytics priorities
        3. Digital transformation initiatives
        4. Future goals and strategic objectives
        5. Technology and data modernization efforts
        
        Content:
        {combined_text}
        
        Strategic Priorities and Data Challenges:
        """
        
        return self._call_llm(prompt, max_tokens=800)
    
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
        """Export dossier as HTML report with business intelligence proforma format"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Business Intelligence Dossier - {dossier.company_name}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #1a365d; text-align: center; margin-bottom: 40px; border-bottom: 3px solid #2b77ad; padding-bottom: 20px; }}
                h2 {{ color: #2b77ad; border-left: 4px solid #4a90c2; padding-left: 15px; margin-top: 30px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 40px; padding: 20px; background-color: #f8fafe; border-radius: 8px; border: 1px solid #e2e8f0; }}
                .section-content {{ padding: 10px 0; color: #2d3748; }}
                .metadata {{ color: #718096; font-size: 0.9em; text-align: center; margin-top: 40px; padding: 20px; background-color: #edf2f7; border-radius: 5px; }}
                .proforma-header {{ text-align: center; color: #4a5568; font-style: italic; margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>Business Intelligence Dossier: {dossier.company_name}</h1>
            <div class="proforma-header">Comprehensive Business Analysis Proforma</div>
            
            <div class="section">
                <h2>1. Company Identity and Purpose</h2>
                <div class="section-content">{dossier.company_identity_and_purpose}</div>
            </div>
            
            <div class="section">
                <h2>2. Products and Services Offered</h2>
                <div class="section-content">{dossier.products_and_services_offered}</div>
            </div>
            
            <div class="section">
                <h2>3. Customer and Stakeholder Landscape</h2>
                <div class="section-content">{dossier.customer_and_stakeholder_landscape}</div>
            </div>
            
            <div class="section">
                <h2>4. Core Business Activities and Processes</h2>
                <div class="section-content">{dossier.core_business_activities_and_processes}</div>
            </div>
            
            <div class="section">
                <h2>5. Organisational Structure and Functions</h2>
                <div class="section-content">{dossier.organisational_structure_and_functions}</div>
            </div>
            
            <div class="section">
                <h2>6. Channels and Customer Interactions</h2>
                <div class="section-content">{dossier.channels_and_customer_interactions}</div>
            </div>
            
            <div class="section">
                <h2>7. Compliance and Regulatory Context</h2>
                <div class="section-content">{dossier.compliance_and_regulatory_context}</div>
            </div>
            
            <div class="section">
                <h2>8. Technology Landscape</h2>
                <div class="section-content">{dossier.technology_landscape}</div>
            </div>
            
            <div class="section">
                <h2>9. Strategic Priorities and Data Challenges</h2>
                <div class="section-content">{dossier.strategic_priorities_and_data_challenges}</div>
            </div>
            
            <div class="metadata">
                <p><strong>Analysis Generated:</strong> {dossier.last_updated}</p>
                <p><strong>Data Sources:</strong> {len(set(dossier.sources))} documents processed</p>
                <p><strong>Intelligence Framework:</strong> 9-Section Business Analysis Proforma</p>
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
