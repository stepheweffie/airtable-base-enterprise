# Airtable Schema Documentation

## Overview
This document outlines the complete Airtable base schema for the Mercor contractor application system. The base consists of 5 interconnected tables designed to capture, process, and evaluate contractor applications.

## Table Structure

### 1. Applicants (Parent Table)
**Purpose**: Central table that stores one row per applicant and holds compressed data plus LLM outputs

| Field Name | Field Type | Description | Required | Notes |
|------------|------------|-------------|----------|--------|
| Applicant ID | Single Line Text (Primary) | Unique identifier for each applicant | Yes | Auto-generated or manually entered |
| Compressed JSON | Long Text | Complete application data in JSON format | No | Populated by compression script |
| Shortlist Status | Single Select | Current shortlisting status | No | Options: "Pending", "Shortlisted", "Rejected" |
| LLM Summary | Long Text | AI-generated summary of applicant | No | Max 75 words, populated by LLM script |
| LLM Score | Number | AI quality score from 1-10 | No | Higher is better |
| LLM Follow-Ups | Long Text | AI-suggested follow-up questions | No | Bullet-point format |
| Created At | Created Time | Timestamp when record was created | Auto | System field |
| Modified At | Last Modified Time | Timestamp when record was last updated | Auto | System field |

### 2. Personal Details (Child Table)
**Purpose**: One-to-one relationship storing personal information for each applicant

| Field Name | Field Type | Description | Required | Notes |
|------------|------------|-------------|----------|--------|
| Record ID | Auto Number (Primary) | Unique record identifier | Auto | System generated |
| Applicant ID | Link to Applicants | Links back to parent record | Yes | One-to-one relationship |
| Full Name | Single Line Text | Applicant's full name | Yes | |
| Email | Email | Contact email address | Yes | |
| Location | Single Line Text | Current location/city/country | Yes | Used for geographic filtering |
| LinkedIn | URL | LinkedIn profile URL | No | |
| Phone | Phone Number | Contact phone number | No | |
| Portfolio URL | URL | Personal website or portfolio | No | |

### 3. Work Experience (Child Table)
**Purpose**: One-to-many relationship storing work history for each applicant

| Field Name | Field Type | Description | Required | Notes |
|------------|------------|-------------|----------|--------|
| Record ID | Auto Number (Primary) | Unique record identifier | Auto | System generated |
| Applicant ID | Link to Applicants | Links back to parent record | Yes | One-to-many relationship |
| Company | Single Line Text | Company name | Yes | Used for tier-1 company detection |
| Title | Single Line Text | Job title/position | Yes | |
| Start Date | Date | Employment start date | Yes | Used for experience calculation |
| End Date | Date | Employment end date | No | Leave blank for current position |
| Technologies | Multiple Select | Technologies/skills used | No | Options: Python, JavaScript, React, etc. |
| Description | Long Text | Job description and achievements | No | |
| Is Current | Checkbox | Currently employed at this company | No | Auto-calculated if End Date is blank |

### 4. Salary Preferences (Child Table)
**Purpose**: One-to-one relationship storing compensation expectations

| Field Name | Field Type | Description | Required | Notes |
|------------|------------|-------------|----------|--------|
| Record ID | Auto Number (Primary) | Unique record identifier | Auto | System generated |
| Applicant ID | Link to Applicants | Links back to parent record | Yes | One-to-one relationship |
| Preferred Rate | Number | Desired hourly rate | Yes | Used for filtering |
| Minimum Rate | Number | Minimum acceptable hourly rate | No | |
| Currency | Single Select | Currency for rates | Yes | Options: USD, EUR, GBP, CAD, INR |
| Availability | Number | Hours available per week | Yes | Used for availability filtering |
| Start Date | Date | When can start working | No | |
| Contract Type | Single Select | Preferred contract type | No | Options: Hourly, Fixed-price, Retainer |

### 5. Shortlisted Leads (Helper Table)
**Purpose**: Auto-populated table for candidates who meet all criteria

| Field Name | Field Type | Description | Required | Notes |
|------------|------------|-------------|----------|--------|
| Record ID | Auto Number (Primary) | Unique record identifier | Auto | System generated |
| Applicant | Link to Applicants | Reference to shortlisted applicant | Yes | Auto-populated |
| Compressed JSON | Long Text | Copy of applicant's compressed data | Yes | For quick access |
| Score Reason | Long Text | Human-readable explanation of why shortlisted | Yes | Auto-generated |
| Created At | Created Time | When candidate was shortlisted | Auto | System field |
| LLM Score | Lookup | LLM score from Applicants table | Auto | Lookup field |
| Applicant Name | Lookup | Name from Personal Details via Applicants | Auto | Lookup field |

## Relationships

```
Applicants (1) ←→ (1) Personal Details
Applicants (1) ←→ (n) Work Experience  
Applicants (1) ←→ (1) Salary Preferences
Applicants (1) ←→ (1) Shortlisted Leads
```

## Field Configuration Details

### Single Select Options

**Shortlist Status**:
- Pending
- Shortlisted  
- Rejected

**Currency**:
- USD
- EUR
- GBP
- CAD
- INR

**Contract Type**:
- Hourly
- Fixed-price
- Retainer

**Technologies** (Multiple Select):
- Python
- JavaScript
- TypeScript
- React
- Node.js
- Vue.js
- Angular
- Django
- Flask
- FastAPI
- PostgreSQL
- MySQL
- MongoDB
- Redis
- AWS
- Google Cloud
- Azure
- Docker
- Kubernetes
- Git
- Machine Learning
- Data Science
- DevOps

## Setup Instructions

1. **Create New Base**: Create a new Airtable base called "Mercor Contractor Applications"

2. **Create Tables**: Create all 5 tables with the exact names specified above

3. **Configure Fields**: Add all fields as specified in the tables above, paying attention to field types and requirements

4. **Set Up Relationships**: 
   - Link Personal Details to Applicants via Applicant ID
   - Link Work Experience to Applicants via Applicant ID  
   - Link Salary Preferences to Applicants via Applicant ID
   - Link Shortlisted Leads to Applicants via Applicant field

5. **Configure Lookup Fields**: In Shortlisted Leads table:
   - Add lookup field for LLM Score from Applicants
   - Add lookup field for Applicant Name from Personal Details via Applicants

6. **Set Field Options**: Configure all Single Select and Multiple Select fields with the options listed above

7. **Get API Credentials**:
   - Go to Account → API
   - Generate personal access token with full access
   - Copy your base ID from the API documentation

## Form Setup

Since Airtable forms can only write to one table at a time, you'll need to create 3 separate forms:

1. **Personal Details Form**: Collects basic information and generates/shows Applicant ID
2. **Work Experience Form**: Pre-filled with Applicant ID, allows multiple submissions
3. **Salary Preferences Form**: Pre-filled with Applicant ID

Each form should include the Applicant ID field to link records properly.

## Views Recommendations

Create these views for better data management:

- **All Applicants**: Default view of Applicants table
- **Complete Applications**: Filter for records with all child tables populated
- **Pending Review**: Filter for applications awaiting LLM evaluation
- **Shortlisted**: Filter for shortlisted candidates
- **Recent Applications**: Sort by Created At (newest first)

This schema supports the full automation workflow while maintaining data integrity and relationships.
