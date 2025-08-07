import streamlit as st
import pdfplumber
import PyPDF2
import re
import pandas as pd
from typing import Dict, List, Optional
import io
import os
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import json
import zipfile
from datetime import datetime





class W2FormParserGemini:
    """Enhanced W-2 form parser using Google Gemini API"""
    
    def __init__(self):
        self.extracted_data = {}
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Initialize Gemini if API key is available and library is installed
        if self.gemini_api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('models/gemini-1.5-pro')
                self.use_gemini = True
            except Exception as e:
                self.use_gemini = False
        else:
            self.use_gemini = False
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF using multiple methods"""
        try:
            # Try pdfplumber first (better for forms)
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    return text
            
            # Fallback to PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
            
        except Exception as e:
            return ""
    
    def extract_with_gemini(self, text: str) -> Dict:
        """Extract W-2 information using Gemini API"""
        if not self.use_gemini:
            return {}
        
        try:
            prompt = f"""
            You are an expert at extracting information from W-2 tax forms. Please analyze the following text from a W-2 form and extract the key information in JSON format.

            Text from W-2 form:
            {text[:4000]}  # Limit text length for API

            Please extract the following fields and return ONLY a valid JSON object:
            {{
                "employee_name": "Full name of employee",
                "employee_ssn": "Social Security Number (format: XXX-XX-XXXX)",
                "employee_address": "Complete address of employee",
                "employee_city_state_zip": "City, State ZIP code",
                "employer_name": "Name of employer/company",
                "employer_ein": "Employer Identification Number (format: XX-XXXXXXX)",
                "employer_address": "Complete address of employer",
                "employer_city_state_zip": "City, State ZIP code of employer",
                "wages_tips": "Box 1 - Wages, tips, other compensation (numeric value only)",
                "federal_income_tax": "Box 2 - Federal income tax withheld (numeric value only)",
                "social_security_wages": "Box 3 - Social security wages (numeric value only)",
                "social_security_tax": "Box 4 - Social security tax withheld (numeric value only)",
                "medicare_wages": "Box 5 - Medicare wages and tips (numeric value only)",
                "medicare_tax": "Box 6 - Medicare tax withheld (numeric value only)",
                "state_wages": "Box 16 - State wages, tips, etc. (numeric value only)",
                "state_income_tax": "Box 17 - State income tax (numeric value only)",
                "local_wages": "Box 18 - Local wages, tips, etc. (numeric value only)",
                "local_income_tax": "Box 19 - Local income tax (numeric value only)",
                "control_number": "Box d - Control number"
            }}

            Rules:
            1. If a field is not found, use empty string ""
            2. For monetary values, extract only the number (e.g., "75000.00" not "$75,000.00")
            3. For SSN and EIN, use the exact format shown
            4. Return ONLY the JSON object, no additional text
            5. Ensure all field names are exactly as shown above
            """

            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError as e:
                    return {}
            else:
                return {}
                
        except Exception as e:
            return {}
    
    def extract_w2_fields_regex(self, text: str) -> Dict:
        """Extract W-2 form fields using regex patterns (fallback method)"""
        data = {
            'employee_name': '',
            'employee_address': '',
            'employee_city_state_zip': '',
            'employee_ssn': '',
            'employer_name': '',
            'employer_address': '',
            'employer_city_state_zip': '',
            'employer_ein': '',
            'wages_tips': '',
            'federal_income_tax': '',
            'social_security_wages': '',
            'social_security_tax': '',
            'medicare_wages': '',
            'medicare_tax': '',
            'state_wages': '',
            'state_income_tax': '',
            'local_wages': '',
            'local_income_tax': '',
            'control_number': '',
            'other_info': []
        }
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\n', ' ')
        
        # Regex patterns for W-2 fields
        patterns = {
            'employee_name': [
                r'Employee\'s name[:\s]*([A-Za-z\s]+?)(?=\s*(?:SSN|Address|Box|$))',
                r'Name[:\s]*([A-Za-z\s]+?)(?=\s*(?:SSN|Address|Box|$))',
            ],
            'employee_ssn': [
                r'SSN[:\s]*(\d{3}-\d{2}-\d{4})',
                r'Social Security Number[:\s]*(\d{3}-\d{2}-\d{4})',
            ],
            'employer_name': [
                r'Employer\'s name[:\s]*([A-Za-z\s&.,]+?)(?=\s*(?:EIN|Address|Box|$))',
                r'Employer[:\s]*([A-Za-z\s&.,]+?)(?=\s*(?:EIN|Address|Box|$))'
            ],
            'employer_ein': [
                r'EIN[:\s]*(\d{2}-\d{7})',
                r'Employer identification number[:\s]*(\d{2}-\d{7})',
            ],
            'wages_tips': [
                r'Box 1[:\s]*\$?([\d,]+\.?\d*)',
                r'Wages, tips, other comp\.[:\s]*\$?([\d,]+\.?\d*)',
            ],
            'federal_income_tax': [
                r'Box 2[:\s]*\$?([\d,]+\.?\d*)',
                r'Federal income tax withheld[:\s]*\$?([\d,]+\.?\d*)',
            ],
            'social_security_wages': [
                r'Box 3[:\s]*\$?([\d,]+\.?\d*)',
                r'Social security wages[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'social_security_tax': [
                r'Box 4[:\s]*\$?([\d,]+\.?\d*)',
                r'Social security tax withheld[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'medicare_wages': [
                r'Box 5[:\s]*\$?([\d,]+\.?\d*)',
                r'Medicare wages and tips[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'medicare_tax': [
                r'Box 6[:\s]*\$?([\d,]+\.?\d*)',
                r'Medicare tax withheld[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'control_number': [
                r'Box d[:\s]*([A-Za-z0-9]+)',
                r'Control number[:\s]*([A-Za-z0-9]+)'
            ]
        }
        
        # Extract data using patterns
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 1:
                        data[field] = value
                        break
        
        # Extract addresses and other fields
        address_patterns = [
            r'Employee\'s address[:\s]*([^A-Z\n]+?)(?=\s*(?:City|State|ZIP|Box|$))',
            r'Address[:\s]*([^A-Z\n]+?)(?=\s*(?:City|State|ZIP|Box|$))'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                if address and len(address) > 5:
                    data['employee_address'] = address
                    break
        
        # Extract city, state, zip
        city_state_patterns = [
            r'City, State ZIP[:\s]*([A-Za-z\s,]+?\d{5}(?:-\d{4})?)',
            r'([A-Za-z\s,]+?\d{5}(?:-\d{4})?)'
        ]
        
        for pattern in city_state_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                city_state = match.group(1).strip()
                if city_state and len(city_state) > 5:
                    data['employee_city_state_zip'] = city_state
                    break
        
        # Extract state and local tax information
        state_patterns = [
            r'Box 16[:\s]*\$?([\d,]+\.?\d*)',
            r'State wages, tips, etc\.[:\s]*\$?([\d,]+\.?\d*)'
        ]
        
        state_tax_patterns = [
            r'Box 17[:\s]*\$?([\d,]+\.?\d*)',
            r'State income tax[:\s]*\$?([\d,]+\.?\d*)'
        ]
        
        local_patterns = [
            r'Box 18[:\s]*\$?([\d,]+\.?\d*)',
            r'Local wages, tips, etc\.[:\s]*\$?([\d,]+\.?\d*)'
        ]
        
        local_tax_patterns = [
            r'Box 19[:\s]*\$?([\d,]+\.?\d*)',
            r'Local income tax[:\s]*\$?([\d,]+\.?\d*)'
        ]
        
        # Extract state and local data
        for pattern in state_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['state_wages'] = match.group(1).strip()
                break
        
        for pattern in state_tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['state_income_tax'] = match.group(1).strip()
                break
        
        for pattern in local_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['local_wages'] = match.group(1).strip()
                break
        
        for pattern in local_tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['local_income_tax'] = match.group(1).strip()
                break
        
        return data
    
    def parse_pdf(self, pdf_file) -> Dict:
        """Main method to parse PDF and extract W-2 information"""
        text = self.extract_text_from_pdf(pdf_file)
        if not text:
            return {}
        
        # Try Gemini first if available
        if self.use_gemini:
            gemini_data = self.extract_with_gemini(text)
            if gemini_data:
                return gemini_data
        
        # Fallback to regex
        return self.extract_w2_fields_regex(text)

def process_multiple_w2s(uploaded_files, parser):
    """Process multiple W-2 forms and return combined results"""
    all_results = []
    
    for uploaded_file in uploaded_files:
        try:
            # Parse the PDF
            extracted_data = parser.parse_pdf(uploaded_file)
            
            if extracted_data:
                # Add file information
                extracted_data['filename'] = uploaded_file.name
                extracted_data['file_size'] = f"{uploaded_file.size / 1024:.2f} KB"
                extracted_data['processing_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                all_results.append(extracted_data)
                
        except Exception as e:
            pass
    
    return all_results

def create_summary_dataframe(all_results):
    """Create a summary DataFrame from all results"""
    if not all_results:
        return pd.DataFrame()
    
    # Prepare data for DataFrame
    df_data = []
    for result in all_results:
        row = {
            'Filename': result.get('filename', ''),
            'Employee Name': result.get('employee_name', ''),
            'Employee SSN': result.get('employee_ssn', ''),
            'Employer Name': result.get('employer_name', ''),
            'Employer EIN': result.get('employer_ein', ''),
            'Wages/Tips': result.get('wages_tips', ''),
            'Federal Tax': result.get('federal_income_tax', ''),
            'SS Wages': result.get('social_security_wages', ''),
            'SS Tax': result.get('social_security_tax', ''),
            'Medicare Wages': result.get('medicare_wages', ''),
            'Medicare Tax': result.get('medicare_tax', ''),
            'State Wages': result.get('state_wages', ''),
            'State Tax': result.get('state_income_tax', ''),
            'Local Wages': result.get('local_wages', ''),
            'Local Tax': result.get('local_income_tax', ''),
            'Control Number': result.get('control_number', ''),
            'Processing Time': result.get('processing_timestamp', '')
        }
        df_data.append(row)
    
    return pd.DataFrame(df_data)

def main():
    st.set_page_config(
        page_title="W-2 Form Scanner - Batch Processing",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("📄 W-2 Form Scanner")
    st.write("Upload PDFs • Extract Data • Download Results")
    
    # Initialize parser
    parser = W2FormParserGemini()
    

    

    
    uploaded_files = st.file_uploader(
        "Choose multiple PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload multiple W-2 forms in PDF format"
    )
    
    if uploaded_files:
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Process All W-2 Forms", type="primary", use_container_width=True):
                try:
                    # Process all files
                    all_results = process_multiple_w2s(uploaded_files, parser)
                    
                    if all_results:
                        # Create summary DataFrame
                        summary_df = create_summary_dataframe(all_results)
                        
                        # Display summary
                        st.subheader("📊 Extracted Data")
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        # Statistics
                        total_forms = len(all_results)
                        total_fields_extracted = sum(
                            sum(1 for v in result.values() if v and isinstance(v, str) and v.strip())
                            for result in all_results
                        )
                        avg_fields_per_form = total_fields_extracted / total_forms if total_forms > 0 else 0
                        
                        # Simple stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Forms", total_forms)
                        with col2:
                            st.metric("Fields", total_fields_extracted)
                        with col3:
                            st.metric("Avg/Form", f"{avg_fields_per_form:.1f}")
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = summary_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"w2_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col2:
                            json_str = json.dumps(all_results, indent=2)
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_str,
                                file_name=f"w2_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        # Individual file results
                        for i, result in enumerate(all_results):
                            with st.expander(f"📄 {result.get('filename', f'File {i+1}')}", expanded=False):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**👤 Employee Information**")
                                    st.write(f"**Name:** {result.get('employee_name', 'Not found')}")
                                    st.write(f"**SSN:** {result.get('employee_ssn', 'Not found')}")
                                    st.write(f"**Address:** {result.get('employee_address', 'Not found')}")
                                
                                with col2:
                                    st.markdown("**🏢 Employer Information**")
                                    st.write(f"**Name:** {result.get('employer_name', 'Not found')}")
                                    st.write(f"**EIN:** {result.get('employer_ein', 'Not found')}")
                                    st.write(f"**Address:** {result.get('employer_address', 'Not found')}")
                                
                                st.markdown("**💰 Financial Information**")
                                col3, col4 = st.columns(2)
                                with col3:
                                    st.write(f"**Wages:** ${result.get('wages_tips', '0')}")
                                    st.write(f"**Federal Tax:** ${result.get('federal_income_tax', '0')}")
                                    st.write(f"**SS Wages:** ${result.get('social_security_wages', '0')}")
                                with col4:
                                    st.write(f"**SS Tax:** ${result.get('social_security_tax', '0')}")
                                    st.write(f"**Medicare Wages:** ${result.get('medicare_wages', '0')}")
                                    st.write(f"**Medicare Tax:** ${result.get('medicare_tax', '0')}")
                except Exception as e:
                    pass
    


if __name__ == "__main__":
    main() 