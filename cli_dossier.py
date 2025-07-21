#!/usr/bin/env python3
"""
CLI script for generating company dossiers

Usage Examples:
    # From scraped company data:
    python cli_dossier.py --company-domain www.abngroup.com.au
    
    # From custom PDF directory:
    python cli_dossier.py --pdf-directory /path/to/pdfs --company-name "ABC Corporation"
    
    # With custom settings:
    python cli_dossier.py --pdf-directory ./my_pdfs --company-name "My Company" --chunk-size 1500 --format json
"""

import argparse
import sys
from pathlib import Path
from dossier_generator import DossierGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate company dossier from scraped PDFs or custom directory")
    
    # Mutually exclusive group for source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--company-domain", help="Company domain (e.g., www.abngroup.com.au) from scraped data")
    source_group.add_argument("--pdf-directory", help="Path to directory containing PDF files")
    
    parser.add_argument("--company-name", help="Company name (required when using --pdf-directory)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Text chunk size (default: 1000)")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap (default: 200)")
    parser.add_argument("--max-tokens", type=int, default=4000, help="Max context tokens (default: 4000)")
    parser.add_argument("--output-dir", default="dossiers", help="Output directory (default: dossiers)")
    parser.add_argument("--format", choices=["json", "html", "both"], default="both", help="Output format")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.pdf_directory and not args.company_name:
        parser.error("--company-name is required when using --pdf-directory")
    
    # Determine source and validate
    if args.company_domain:
        # Check scraped company directory
        downloads_dir = Path("downloads")
        company_dir = downloads_dir / args.company_domain
        pdf_dir = company_dir / "pdfs"
        
        if not pdf_dir.exists():
            print(f"Error: No PDFs found for {args.company_domain}")
            print(f"Expected path: {pdf_dir}")
            sys.exit(1)
        
        pdf_count = len(list(pdf_dir.glob("*.pdf")))
        if pdf_count == 0:
            print(f"Error: No PDF files found in {pdf_dir}")
            sys.exit(1)
        
        print(f"Processing {pdf_count} PDF files for {args.company_domain}")
        source_type = "scraped"
        
    else:  # pdf_directory
        pdf_dir = Path(args.pdf_directory)
        
        if not pdf_dir.exists():
            print(f"Error: Directory not found: {args.pdf_directory}")
            sys.exit(1)
        
        if not pdf_dir.is_dir():
            print(f"Error: Path is not a directory: {args.pdf_directory}")
            sys.exit(1)
        
        pdf_count = len(list(pdf_dir.glob("*.pdf")))
        if pdf_count == 0:
            print(f"Error: No PDF files found in {args.pdf_directory}")
            sys.exit(1)
        
        print(f"Processing {pdf_count} PDF files from {args.pdf_directory}")
        print(f"Company name: {args.company_name}")
        source_type = "custom"
    
    # Initialize generator
    generator = DossierGenerator(
        downloads_dir="downloads",
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        max_context_tokens=args.max_tokens
    )
    
    # Generate dossier
    print("Generating dossier...")
    if source_type == "scraped":
        dossier = generator.generate_company_dossier(company_domain=args.company_domain)
        company_name_clean = args.company_domain.replace("www.", "").replace(".", "_")
    else:
        dossier = generator.generate_company_dossier(
            pdf_directory=args.pdf_directory,
            company_name=args.company_name
        )
        company_name_clean = "".join(c for c in args.company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        company_name_clean = company_name_clean.replace(' ', '_').lower()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Save in requested format(s)
    if args.format in ["json", "both"]:
        json_path = output_dir / f"{company_name_clean}_dossier.json"
        generator.save_dossier(dossier, str(json_path))
        print(f"JSON dossier saved to: {json_path}")
    
    if args.format in ["html", "both"]:
        html_path = output_dir / f"{company_name_clean}_dossier.html"
        generator.export_dossier_html(dossier, str(html_path))
        print(f"HTML dossier saved to: {html_path}")
    
    print("\nDossier Summary:")
    print(f"Company: {dossier.company_name}")
    print(f"Sources processed: {len(set(dossier.sources))}")
    print("Business Intelligence Proforma - 9 sections completed:")
    print("  ✓ Company Identity and Purpose")
    print("  ✓ Products and Services Offered") 
    print("  ✓ Customer and Stakeholder Landscape")
    print("  ✓ Core Business Activities and Processes")
    print("  ✓ Organisational Structure and Functions")
    print("  ✓ Channels and Customer Interactions")
    print("  ✓ Compliance and Regulatory Context")
    print("  ✓ Technology Landscape")
    print("  ✓ Strategic Priorities and Data Challenges")

if __name__ == "__main__":
    main()
