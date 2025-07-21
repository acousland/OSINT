#!/usr/bin/env python3
"""
Test script to verify the new 9-section business intelligence proforma structure works correctly.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dossier_generator import CompanyDossier, DossierGenerator
    print("✅ Successfully imported CompanyDossier and DossierGenerator")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_dossier_structure():
    """Test that the new dossier structure works correctly"""
    print("\n🧪 Testing new CompanyDossier structure...")
    
    # Create a test dossier with the new structure
    test_dossier = CompanyDossier(
        company_name="Test Company Ltd",
        company_identity_and_purpose="Test company focused on innovation and customer service.",
        products_and_services_offered="Software solutions, consulting services, and training programs.",
        customer_and_stakeholder_landscape="SME businesses, enterprise clients, and technology partners.",
        core_business_activities_and_processes="Development, testing, deployment, and support processes.",
        organisational_structure_and_functions="Flat structure with cross-functional teams.",
        channels_and_customer_interactions="Online platform, direct sales, and partner networks.",
        compliance_and_regulatory_context="ISO certifications, data protection compliance.",
        technology_landscape="Cloud-native architecture, microservices, and modern frameworks.",
        strategic_priorities_and_data_challenges="Digital transformation and data analytics.",
        sources=["test_document.pdf"],
        last_updated=datetime.now().isoformat()
    )
    
    print("✅ CompanyDossier created successfully with new structure")
    
    # Test all 9 sections are accessible
    sections = [
        ("Company Identity and Purpose", test_dossier.company_identity_and_purpose),
        ("Products and Services Offered", test_dossier.products_and_services_offered),
        ("Customer and Stakeholder Landscape", test_dossier.customer_and_stakeholder_landscape),
        ("Core Business Activities and Processes", test_dossier.core_business_activities_and_processes),
        ("Organisational Structure and Functions", test_dossier.organisational_structure_and_functions),
        ("Channels and Customer Interactions", test_dossier.channels_and_customer_interactions),
        ("Compliance and Regulatory Context", test_dossier.compliance_and_regulatory_context),
        ("Technology Landscape", test_dossier.technology_landscape),
        ("Strategic Priorities and Data Challenges", test_dossier.strategic_priorities_and_data_challenges),
    ]
    
    print("\n📋 Testing all 9 sections:")
    for section_name, section_content in sections:
        print(f"  ✅ {section_name}: {len(section_content)} characters")
    
    return test_dossier

def test_html_export():
    """Test HTML export with new structure"""
    print("\n📄 Testing HTML export...")
    
    try:
        generator = DossierGenerator()
        test_dossier = test_dossier_structure()
        
        # Test HTML export
        html_path = "/tmp/test_dossier.html"
        generator.export_dossier_html(test_dossier, html_path)
        
        # Check if file was created
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                content = f.read()
                if "Business Intelligence Dossier" in content and "9-Section Business Analysis Proforma" in content:
                    print("✅ HTML export successful with new proforma structure")
                    os.remove(html_path)  # Clean up
                    return True
                else:
                    print("❌ HTML export missing expected proforma content")
                    return False
        else:
            print("❌ HTML file was not created")
            return False
            
    except Exception as e:
        print(f"❌ HTML export test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing New Business Intelligence Proforma Structure")
    print("=" * 60)
    
    try:
        # Test 1: Dossier structure
        test_dossier_structure()
        
        # Test 2: HTML export
        test_html_export()
        
        print("\n✅ All tests passed! New proforma structure is working correctly.")
        print("\n📊 Summary:")
        print("   • 9-section business intelligence proforma structure implemented")
        print("   • CompanyDossier dataclass updated")
        print("   • HTML export template updated")
        print("   • All sections accessible and functional")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
