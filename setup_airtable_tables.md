# Airtable Base Setup Guide
Base ID: app2YwwqHprssdIVE

## Table 1: Applicants (Primary Table)

**Table Name:** Applicants

| Field Name | Field Type | Required | Configuration |
|------------|------------|----------|---------------|
| Applicant ID | Single Line Text | Yes | Set as Primary Field |
| Compressed JSON | Long Text | No | |
| Shortlist Status | Single Select | No | Options: "Pending", "Shortlisted", "Rejected" |
| LLM Summary | Long Text | No | |
| LLM Score | Number | No | Allow negative numbers: No, Precision: 0 decimal places |
| LLM Follow-Ups | Long Text | No | |
| Created At | Created Time | Auto | System field |
| Modified At | Last Modified Time | Auto | System field |

## Table 2: Personal Details

**Table Name:** Personal Details

| Field Name | Field Type | Required | Configuration |
|------------|------------|----------|---------------|
| Record ID | Autonumber | Auto | Set as Primary Field |
| Applicant ID | Link to Another Record | Yes | Link to: "Applicants" table, Allow linking to multiple records: No |
| Full Name | Single Line Text | Yes | |
| Email | Email | Yes | |
| Location | Single Line Text | Yes | |
| LinkedIn | URL | No | |
| Phone | Phone Number | No | |
| Portfolio URL | URL | No | |

## Table 3: Work Experience

**Table Name:** Work Experience

| Field Name | Field Type | Required | Configuration |
|------------|------------|----------|---------------|
| Record ID | Autonumber | Auto | Set as Primary Field |
| Applicant ID | Link to Another Record | Yes | Link to: "Applicants" table, Allow linking to multiple records: No |
| Company | Single Line Text | Yes | |
| Title | Single Line Text | Yes | |
| Start Date | Date | Yes | Include time: No |
| End Date | Date | No | Include time: No |
| Technologies | Multiple Select | No | See options below |
| Description | Long Text | No | |
| Is Current | Checkbox | No | |

**Technologies Options:**
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

## Table 4: Salary Preferences

**Table Name:** Salary Preferences

| Field Name | Field Type | Required | Configuration |
|------------|------------|----------|---------------|
| Record ID | Autonumber | Auto | Set as Primary Field |
| Applicant ID | Link to Another Record | Yes | Link to: "Applicants" table, Allow linking to multiple records: No |
| Preferred Rate | Number | Yes | Allow negative numbers: No, Precision: 2 decimal places |
| Minimum Rate | Number | No | Allow negative numbers: No, Precision: 2 decimal places |
| Currency | Single Select | Yes | Options: USD, EUR, GBP, CAD, INR |
| Availability | Number | Yes | Allow negative numbers: No, Precision: 0 decimal places |
| Start Date | Date | No | Include time: No |
| Contract Type | Single Select | No | Options: Hourly, Fixed-price, Retainer |

## Table 5: Shortlisted Leads

**Table Name:** Shortlisted Leads

| Field Name | Field Type | Required | Configuration |
|------------|------------|----------|---------------|
| Record ID | Autonumber | Auto | Set as Primary Field |
| Applicant | Link to Another Record | Yes | Link to: "Applicants" table, Allow linking to multiple records: No |
| Compressed JSON | Long Text | Yes | |
| Score Reason | Long Text | Yes | |
| Created At | Created Time | Auto | System field |
| LLM Score | Lookup | Auto | Look up field: "LLM Score" from "Applicants" table via "Applicant" link |
| Applicant Name | Lookup | Auto | Look up field: "Full Name" from "Personal Details" table via "Applicants" → "Personal Details" link |

## Setup Order

1. Create "Applicants" table first
2. Create "Personal Details" table and link to Applicants
3. Create "Work Experience" table and link to Applicants
4. Create "Salary Preferences" table and link to Applicants
5. Create "Shortlisted Leads" table last (requires other tables to exist for lookups)

## Key Requirements

- Field names must match exactly (case-sensitive)
- Primary fields must be set correctly
- Required fields must be marked as required
- Link relationships must be one-to-one for Personal Details and Salary Preferences
- Link relationship must be one-to-many for Work Experience
- Lookup fields in Shortlisted Leads require the linked tables to exist first

## Verification Steps

After creating all tables, verify:
1. All table names match exactly
2. All field names match exactly
3. All field types are correct
4. All links are properly configured
5. Lookup fields are pulling data correctly
