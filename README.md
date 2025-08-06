# 📄 W-2 Form Scanner

A powerful Streamlit application that extracts information from W-2 tax forms using AI-powered text extraction and regex patterns.

## ✨ Features

- **📁 Batch Processing**: Upload and process multiple W-2 forms simultaneously
- **🤖 AI-Powered Extraction**: Uses Google Gemini AI for accurate field extraction
- **🔍 Regex Fallback**: Reliable regex patterns when AI is unavailable
- **📊 Data Preview**: Clean table view of extracted information
- **📥 Multiple Export Formats**: Download results as CSV or JSON
- **🎯 Clean Interface**: Minimal, user-friendly design

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key (optional, for enhanced extraction)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/w2-form-scanner.git
   cd w2-form-scanner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key (optional)**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```
   
   Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

## 📋 Usage

1. **Upload W-2 Forms**: Drag and drop or browse for PDF files
2. **Process Files**: Click "Process All W-2 Forms" button
3. **Review Results**: View extracted data in the table
4. **Download Data**: Export as CSV or JSON format

## 🔧 How It Works

### AI-Powered Extraction
- Uses Google Gemini AI to intelligently extract W-2 fields
- Handles various form layouts and formats
- Provides high accuracy for complex documents

### Regex Fallback
- Comprehensive regex patterns for all W-2 fields
- Works without API key or internet connection
- Reliable extraction from standard W-2 formats

### Extracted Fields
- **Employee Information**: Name, SSN, Address
- **Employer Information**: Name, EIN, Address
- **Financial Data**: Wages, Taxes, Social Security, Medicare
- **Additional Fields**: Control numbers, State/Local taxes

## 📁 Project Structure

```
w2-form-scanner/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
└── .gitignore         # Git ignore rules
```

## 🛠️ Dependencies

- `streamlit` - Web application framework
- `pdfplumber` - PDF text extraction
- `PyPDF2` - PDF processing fallback
- `pandas` - Data manipulation
- `google-generativeai` - Gemini AI integration
- `python-dotenv` - Environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for advanced text extraction
- Streamlit for the web framework
- PDFPlumber for reliable PDF processing

---

**Note**: This application is designed for educational and personal use. Always ensure compliance with data privacy regulations when processing sensitive documents. 