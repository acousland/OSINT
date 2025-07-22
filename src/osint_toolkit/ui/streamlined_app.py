"""
Streamlined OSINT Toolkit UI - In-Memory Pipeline
Combines mapping, scraping, and dossier generation in a single workflow
"""

import streamlit as st
import asyncio
import time
from typing import Optional
from pathlib import Path
import json
import base64

# Import our in-memory components
from osint_toolkit.core.in_memory_mapper import InMemoryWebMapper
from osint_toolkit.core.in_memory_scraper import InMemoryScraper
from osint_toolkit.core.in_memory_dossier import InMemoryDossierGenerator

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    """Main Streamlined OSINT Application"""
    
    st.set_page_config(
        page_title="OSINT Toolkit - Streamlined",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 OSINT Toolkit - Streamlined Pipeline")
    st.markdown("**Map → Scrape → Analyze** - All in memory, download final results only")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Mapping settings
    st.sidebar.markdown("### 🗺️ Mapping Settings")
    max_concurrent_map = st.sidebar.slider("Concurrent Mapping Requests", 10, 50, 30, 5)
    max_depth = st.sidebar.slider("Maximum Depth", 1, 5, 3, 1)
    
    # Scraping settings
    st.sidebar.markdown("### 📥 Scraping Settings")
    max_concurrent_scrape = st.sidebar.slider("Concurrent Scraping Requests", 5, 30, 20, 5)
    
    # Dossier settings
    st.sidebar.markdown("### 📋 Dossier Settings")
    chunk_size = st.sidebar.slider("Text Chunk Size", 500, 2000, 1000, 100)
    max_clusters = st.sidebar.slider("Topic Clusters", 3, 15, 8, 1)
    
    # Check API configuration for dossier generation
    dossier_gen = InMemoryDossierGenerator()
    api_status = dossier_gen.check_api_configuration()
    
    if not api_status["configured"]:
        st.error("🔑 OpenAI API Configuration Required for Dossier Generation")
        with st.expander("⚙️ API Configuration Help", expanded=True):
            st.markdown(f"**Status:** {api_status['status']}")
            for suggestion in api_status["suggestions"]:
                st.markdown(f"• {suggestion}")
    else:
        st.sidebar.success("✅ API Configured")
    
    # Main workflow
    st.markdown("### 🎯 Complete OSINT Workflow")
    
    # URL input
    col1, col2 = st.columns([3, 1])
    with col1:
        target_url = st.text_input(
            "🌐 Target Website URL",
            placeholder="https://example.com",
            help="Enter the website URL to analyze"
        )
    
    with col2:
        company_name = st.text_input(
            "🏢 Company Name",
            placeholder="Company Ltd",
            help="Name for the dossier"
        )
    
    # Workflow control
    col1, col2, col3 = st.columns(3)
    
    with col1:
        run_mapping = st.checkbox("🗺️ Map Website", value=True)
    with col2:
        run_scraping = st.checkbox("📥 Scrape Content", value=True)
    with col3:
        run_dossier = st.checkbox("📋 Generate Dossier", value=api_status["configured"])
    
    # Main execution button
    if st.button("🚀 Run Complete Analysis", type="primary", disabled=not target_url):
        if target_url and target_url.startswith(('http://', 'https://')):
            asyncio.run(run_complete_analysis(
                target_url=target_url,
                company_name=company_name or "Unknown Company",
                run_mapping=run_mapping,
                run_scraping=run_scraping,
                run_dossier=run_dossier and api_status["configured"],
                max_concurrent_map=max_concurrent_map,
                max_depth=max_depth,
                max_concurrent_scrape=max_concurrent_scrape,
                chunk_size=chunk_size,
                max_clusters=max_clusters
            ))
        else:
            st.error("Please enter a valid URL starting with http:// or https://")
    
    # Display session state results if available
    if hasattr(st.session_state, 'analysis_results'):
        display_results()

async def run_complete_analysis(target_url: str, company_name: str, run_mapping: bool, 
                               run_scraping: bool, run_dossier: bool, **kwargs):
    """Run the complete OSINT analysis pipeline"""
    
    # Initialize components
    mapper = InMemoryWebMapper(
        max_concurrent=kwargs['max_concurrent_map'],
        max_depth=kwargs['max_depth']
    )
    scraper = InMemoryScraper(max_concurrent=kwargs['max_concurrent_scrape'])
    dossier_gen = InMemoryDossierGenerator(chunk_size=kwargs['chunk_size'])
    
    # Progress tracking
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    results = {
        'target_url': target_url,
        'company_name': company_name,
        'timestamp': time.time()
    }
    
    try:
        # Phase 1: Mapping
        if run_mapping:
            with status_container:
                st.info("🗺️ **Phase 1: Mapping Website Structure**")
            
            def update_mapping_progress(message):
                status_text.text(f"Mapping: {message}")
            
            mapping_results = await mapper.map_website(target_url, update_mapping_progress)
            results['mapping'] = mapping_results
            
            progress_bar.progress(0.33)
            
            with status_container:
                st.success(f"✅ Mapping Complete: {len(mapping_results['discovered_urls'])} URLs discovered")
        
        # Phase 2: Scraping
        if run_scraping and run_mapping:
            with status_container:
                st.info("📥 **Phase 2: Scraping Content**")
            
            def update_scraping_progress(message):
                status_text.text(f"Scraping: {message}")
            
            urls_to_scrape = results['mapping']['discovered_urls']
            scraping_results = await scraper.scrape_content(urls_to_scrape, update_scraping_progress)
            results['scraping'] = scraping_results
            
            progress_bar.progress(0.66)
            
            with status_container:
                st.success(f"✅ Scraping Complete: {scraping_results['stats']['html_pages']} HTML pages, {scraping_results['stats']['pdf_files']} PDFs")
        
        # Phase 3: Dossier Generation
        if run_dossier and run_scraping:
            with status_container:
                st.info("📋 **Phase 3: Generating Dossier**")
            
            def update_dossier_progress(message):
                status_text.text(f"Dossier: {message}")
            
            html_content = results['scraping']['html_content']
            pdf_content = results['scraping']['pdf_content']
            
            dossier = await dossier_gen.generate_dossier_from_memory(
                html_content, pdf_content, company_name, update_dossier_progress
            )
            
            # Export dossier
            exported = dossier_gen.export_dossier(dossier)
            results['dossier'] = {
                'data': dossier,
                'exports': exported
            }
            
            progress_bar.progress(1.0)
            
            with status_container:
                st.success("✅ **Analysis Complete!**")
        
        # Store results in session state
        st.session_state.analysis_results = results
        
        # Auto-display results
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")

def display_results():
    """Display the analysis results"""
    
    if not hasattr(st.session_state, 'analysis_results'):
        return
    
    results = st.session_state.analysis_results
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if 'mapping' in results:
        with col1:
            st.metric(
                "URLs Discovered", 
                results['mapping']['stats']['total_urls'],
                delta=f"{results['mapping']['stats']['urls_per_second']:.1f}/sec"
            )
    
    if 'scraping' in results:
        with col2:
            st.metric(
                "Content Scraped",
                f"{results['scraping']['stats']['html_pages']} HTML",
                delta=f"{results['scraping']['stats']['pdf_files']} PDFs"
            )
        
        with col3:
            st.metric(
                "Content Size",
                f"{results['scraping']['stats']['content_size_mb']:.1f} MB",
                delta=f"{results['scraping']['stats']['time_taken']:.1f}s"
            )
    
    if 'dossier' in results:
        with col4:
            st.metric(
                "Dossier Generated",
                "✅ Complete",
                delta="9 sections"
            )
    
    # Detailed results tabs
    tabs = []
    tab_names = []
    
    if 'mapping' in results:
        tab_names.append("🗺️ Mapping")
    if 'scraping' in results:
        tab_names.append("📥 Scraping")
    if 'dossier' in results:
        tab_names.append("📋 Dossier")
    
    if tab_names:
        tabs = st.tabs(tab_names)
        
        tab_idx = 0
        
        # Mapping results
        if 'mapping' in results:
            with tabs[tab_idx]:
                display_mapping_results(results['mapping'])
            tab_idx += 1
        
        # Scraping results
        if 'scraping' in results:
            with tabs[tab_idx]:
                display_scraping_results(results['scraping'])
            tab_idx += 1
        
        # Dossier results
        if 'dossier' in results:
            with tabs[tab_idx]:
                display_dossier_results(results['dossier'])

def display_mapping_results(mapping_data):
    """Display mapping results"""
    st.markdown("### Website Structure Discovery")
    
    stats = mapping_data['stats']
    st.write(f"**Time taken:** {stats['time_taken']} seconds")
    st.write(f"**Processing speed:** {stats['urls_per_second']} URLs/second")
    
    # URL list
    with st.expander(f"📋 Discovered URLs ({len(mapping_data['discovered_urls'])})"):
        for url in mapping_data['discovered_urls']:
            st.write(f"• {url}")
    
    if mapping_data['failed_urls']:
        with st.expander(f"❌ Failed URLs ({len(mapping_data['failed_urls'])})"):
            for url in mapping_data['failed_urls']:
                st.write(f"• {url}")

def display_scraping_results(scraping_data):
    """Display scraping results"""
    st.markdown("### Content Extraction Summary")
    
    stats = scraping_data['stats']
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**HTML Pages:** {stats['html_pages']}")
        st.write(f"**PDF Files:** {stats['pdf_files']}")
    
    with col2:
        st.write(f"**Processing Time:** {stats['time_taken']}s")
        st.write(f"**Total Size:** {stats['content_size_mb']} MB")
    
    # Content preview
    if scraping_data['html_content']:
        with st.expander("📄 HTML Content Preview"):
            for url, content in list(scraping_data['html_content'].items())[:3]:
                st.write(f"**{url}**")
                st.write(f"Title: {content['metadata']['title']}")
                st.write(f"Words: {content['metadata']['word_count']}")
                st.write("---")

def display_dossier_results(dossier_data):
    """Display dossier results with download options"""
    st.markdown("### Business Intelligence Dossier")
    
    dossier = dossier_data['data']
    exports = dossier_data['exports']
    
    st.write(f"**Company:** {dossier.company_name}")
    st.write(f"**Generated:** {dossier.last_updated}")
    st.write(f"**Sources:** {len(dossier.sources)} documents")
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Download JSON Report",
            data=exports['json'],
            file_name=f"{dossier.company_name.replace(' ', '_')}_dossier.json",
            mime="application/json"
        )
    
    with col2:
        st.download_button(
            label="📥 Download HTML Report",
            data=exports['html'],
            file_name=f"{dossier.company_name.replace(' ', '_')}_dossier.html",
            mime="text/html"
        )
    
    # Dossier preview
    sections = [
        ("Company Identity and Purpose", dossier.company_identity_and_purpose),
        ("Products and Services", dossier.products_and_services_offered),
        ("Customer Landscape", dossier.customer_and_stakeholder_landscape),
        ("Business Activities", dossier.core_business_activities_and_processes),
        ("Organizational Structure", dossier.organisational_structure_and_functions),
        ("Customer Interactions", dossier.channels_and_customer_interactions),
        ("Compliance Context", dossier.compliance_and_regulatory_context),
        ("Technology Landscape", dossier.technology_landscape),
        ("Strategic Priorities", dossier.strategic_priorities_and_data_challenges)
    ]
    
    for title, content in sections:
        with st.expander(f"📋 {title}"):
            st.write(content)

if __name__ == "__main__":
    main()
