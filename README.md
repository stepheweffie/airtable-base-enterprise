# Mercor Contractor Application Automation System

A comprehensive Airtable-based system for collecting, processing, and evaluating contractor applications using multi-table forms, JSON compression/decompression, automated shortlisting, and LLM evaluation.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)

## Overview

This system provides a complete workflow for contractor application management:

1. **Data Collection**: Multi-table forms collect structured applicant information
2. **JSON Compression**: Normalizes data across tables into single JSON objects
3. **Automated Shortlisting**: Evaluates candidates against defined criteria
4. **LLM Evaluation**: Uses OpenAI to provide qualitative assessment and follow-up questions
5. **Data Management**: Supports decompression and bi-directional synchronization

## System Architecture

### Database Schema (Airtable)

The system uses 5 interconnected Airtable tables:

- **Applicants** (Parent): Central table with compressed JSON and LLM outputs
- **Personal Details** (1:1): Contact information and personal data
- **Work Experience** (1:many): Employment history and skills
- **Salary Preferences** (1:1): Compensation expectations
- **Shortlisted Leads** (Auto-generated): Qualifying candidates

### Automation Components

- `json_compressor.py`: Gathers multi-table data into compressed JSON
- `json_decompressor.py`: Expands JSON back to normalized tables
- `shortlister.py`: Evaluates candidates against business criteria
- `llm_evaluator.py`: Provides AI-powered candidate assessment
- `main.py`: Orchestrates the complete automation pipeline

## Setup Instructions

### Prerequisites

- Python 3.8+
- Airtable account with API access
- OpenAI API account
- Virtual environment (recommended)

### 1. Environment Setup

```bash
# Clone the project
git clone https://github.com/stepheweffie/airtable-base-enterprise.git
cd airtable-base-enterprise
git checkout airtable-base

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Airtable Configuration

Follow the detailed schema setup in [AIRTABLE_SCHEMA.md](AIRTABLE_SCHEMA.md):

1. Create a new Airtable base called "Mercor Contractor Applications"
2. Set up all 5 tables with the specified fields and relationships
3. Create forms for data collection
4. Generate API credentials (Personal Access Token)
5. Note your Base ID from the API documentation

### 3. Environment Variables

Create a `.env` file in the project root:

```bash
# Required Configuration
AIRTABLE_API_KEY=your_personal_access_token
AIRTABLE_BASE_ID=your_base_id

# OpenAI Configuration (or use exported environment variable)
OPENAI_API_KEY=your_openai_api_key

# Optional Settings
MAX_TOKENS_PER_REQUEST=1500
LLM_MODEL=gpt-3.5-turbo
```

### 4. Verification

Test your setup:

```bash
# Activate virtual environment
source venv/bin/activate

# Test configuration
python -c "import config; config.validate_config(); print('Configuration valid!')"

# Check system status
python main.py status
```

## Usage Guide

### Command Line Interface

The system provides a unified CLI through `main.py`:

```bash
# Show system status
python main.py status

# Run complete automation pipeline
python main.py pipeline

# Process specific applicant
python main.py pipeline APPLICANT_123

# Run individual components
python main.py compress
python main.py shortlist
python main.py evaluate

# Force re-processing
python main.py pipeline --force
```

### Individual Component Usage

#### JSON Compression

```bash
# Compress all applicants
python json_compressor.py

# Compress specific applicant
python json_compressor.py APPLICANT_123

# Force update existing compressed data
python json_compressor.py --force
```

#### JSON Decompression

```bash
# Decompress all applicants
python json_decompressor.py

# Decompress specific applicant
python json_decompressor.py APPLICANT_123

# Validate decompression integrity
python json_decompressor.py APPLICANT_123 --validate
```

#### Shortlisting Automation

```bash
# Process all applicants
python shortlister.py

# Process specific applicant
python shortlister.py APPLICANT_123

# Show shortlisting summary
python shortlister.py --summary

# Force re-evaluation
python shortlister.py --force
```

#### LLM Evaluation

```bash
# Evaluate all applicants
python llm_evaluator.py

# Evaluate specific applicant
python llm_evaluator.py APPLICANT_123

# Show evaluation summary
python llm_evaluator.py --summary

# Force regenerate evaluation
python llm_evaluator.py APPLICANT_123 --regenerate
```

### Typical Workflow

1. **Collect Applications**: Applicants fill out the 3 Airtable forms
2. **Compress Data**: `python main.py compress` to create JSON representations
3. **Run Shortlisting**: `python main.py shortlist` to evaluate against criteria
4. **LLM Evaluation**: `python main.py evaluate` to get AI insights
5. **Review Results**: Check Shortlisted Leads table and LLM summaries

Or run the complete pipeline: `python main.py pipeline`

## API Reference

### Configuration (config.py)

Key configuration constants:

- `AIRTABLE_API_KEY`: Your Airtable personal access token
- `AIRTABLE_BASE_ID`: Base ID from Airtable API docs
- `OPENAI_API_KEY`: OpenAI API key
- `TIER_1_COMPANIES`: List of tier-1 companies for experience evaluation
- `ALLOWED_LOCATIONS`: List of acceptable geographic locations

### JSON Structure

Compressed JSON format:

```json
{
  "personal": {
    "name": "John Doe",
    "email": "john@example.com",
    "location": "San Francisco, CA",
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "experience": [
    {
      "company": "Google",
      "title": "Software Engineer",
      "start_date": "2020-01-01",
      "end_date": "2023-01-01",
      "technologies": ["Python", "JavaScript"],
      "years_experience": 3.0
    }
  ],
  "salary": {
    "preferred_rate": 85,
    "currency": "USD",
    "availability": 30
  },
  "metadata": {
    "total_experience_years": 5.2,
    "has_tier1_company": true,
    "compressed_at": "2024-01-15T10:30:00"
  }
}
```

### Shortlisting Criteria

Candidates must meet ALL three criteria:

1. **Experience**: ≥ 4 years total OR worked at tier-1 company
2. **Compensation**: Rate ≤ $100 USD/hour AND availability ≥ 20 hrs/week
3. **Location**: Located in US, Canada, UK, Germany, or India

### LLM Evaluation Output

The LLM provides structured feedback:

- **Summary**: 75-word candidate overview
- **Score**: Quality rating from 1-10
- **Issues**: Data gaps or inconsistencies
- **Follow-Ups**: Suggested clarifying questions

## Customization Guide

### Modifying Shortlisting Criteria

Edit `config.py` and `shortlister.py`:

```python
# Add new tier-1 companies
TIER_1_COMPANIES.extend(['YourCompany', 'AnotherCompany'])

# Modify location criteria
ALLOWED_LOCATIONS.extend(['Australia', 'Singapore'])

# Update experience requirement (in shortlister.py)
meets_criteria = total_experience >= 3.0 or has_tier1  # Changed from 4.0
```

### Customizing LLM Prompts

Modify `llm_evaluator.py` method `build_evaluation_prompt()`:

```python
prompt = f"""You are a recruiting specialist for tech startups.
[Your custom prompt here...]

EVALUATION CRITERIA:
1. Technical depth and modern stack experience
2. Startup experience and adaptability
3. Communication and remote work skills

[Rest of prompt...]"""
```

### Adding New Data Fields

1. Update Airtable schema with new fields
2. Modify `json_compressor.py` to include new fields in JSON
3. Update `json_decompressor.py` to handle new fields during expansion
4. Adjust LLM prompt if new fields should be evaluated

### Custom Business Logic

Add new evaluation criteria in `shortlister.py`:

```python
def check_custom_criteria(self, applicant_data):
    # Your custom logic here
    meets_criteria = your_custom_evaluation(applicant_data)
    reason = "Your explanation"
    return meets_criteria, reason

# Then add to evaluate_applicant method
custom_pass, custom_reason = self.check_custom_criteria(applicant_data)
overall_pass = experience_pass and compensation_pass and location_pass and custom_pass
```

### Rate Limiting and API Optimization

Adjust LLM API settings in `config.py`:

```python
MAX_TOKENS_PER_REQUEST = 1000  # Reduce for faster/cheaper requests
LLM_MODEL = 'gpt-4'  # Upgrade for better quality
```

Add delays in `llm_evaluator.py`:

```python
# Increase delay between API calls
time.sleep(1.0)  # Default is 0.5 seconds
```

## Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure `.env` file exists with all required variables
- Check that `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` are correct
- Verify OpenAI API key is set (either in `.env` or exported)

**"No applicant records found"**
- Verify Airtable base ID is correct
- Check that tables exist with exact names from schema
- Ensure API key has proper permissions

**"LLM evaluation failed"**
- Check OpenAI API key and account status
- Verify you have sufficient API credits
- Check rate limits (add delays if hitting limits)

**"Invalid JSON format"**
- Run compression script to regenerate JSON
- Check for corrupted data in Airtable
- Validate data integrity with decompressor

### Debug Mode

Enable verbose logging:

```bash
python main.py status --verbose
```

Check individual components:

```bash
python -c "
from json_compressor import JSONCompressor
compressor = JSONCompressor()
print('Compressor initialized successfully')
"
```

### Data Integrity

Validate system integrity:

```bash
# Test compression/decompression cycle
python json_compressor.py APPLICANT_123
python json_decompressor.py APPLICANT_123 --validate

# Check for orphaned records
python main.py cleanup --dry-run
```

### Performance Optimization

For large datasets:

1. Process in batches using specific applicant IDs
2. Use `--force` sparingly to avoid unnecessary re-processing
3. Monitor API rate limits and add delays as needed
4. Consider upgrading to GPT-4 for better quality vs. processing more applicants with GPT-3.5-turbo

### Support

For additional support:

1. Check the logs for detailed error messages
2. Verify your Airtable schema matches the documentation exactly
3. Test individual components before running the full pipeline
4. Ensure your API keys have proper permissions and sufficient credits

---

## File Structure

```
mercor-airtable-automation/
├── config.py                  # Configuration and constants
├── main.py                   # Main orchestrator script
├── json_compressor.py        # JSON compression automation
├── json_decompressor.py      # JSON decompression automation
├── shortlister.py           # Shortlisting automation
├── llm_evaluator.py         # LLM evaluation system
├── README.md               # This documentation
├── AIRTABLE_SCHEMA.md      # Detailed schema documentation
├── .env.example           # Environment variables template
└── requirements.txt       # Python dependencies (if created)
```

This system provides a complete, production-ready solution for contractor application management with extensive customization options and robust error handling.
