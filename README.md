# Spendify - AI-Powered Receipt Processing System

## Overview

Spendify is a comprehensive receipt processing and classification system that combines Discord bot integration, Google Cloud AI services, and multi-agent AI pipelines to automatically categorize and analyze receipt data.

## Architecture

```
Discord Bot → Main API → GCP Document AI → Receipt Classifier Agents → Firebase Storage
```

## Key Features

- **Discord Integration**: Upload receipts directly through Discord
- **OCR Processing**: Extract text and entities using Google Cloud Document AI
- **AI Classification**: Multi-agent pipeline for intelligent item categorization
- **Data Validation**: Automatic validation with receipt total reconciliation
- **Cloud Storage**: Structured data storage in Firebase Firestore
- **Multi-format Support**: Handles various receipt formats and layouts

## System Components

### 1. Entry Points

#### Discord Bot (`bot.py`)
- Accepts image uploads from Discord users
- Handles user registration and authentication
- Manages file uploads and session tracking
- Provides real-time feedback to users

#### Main API (`main_api.py`)
- Central Flask API server
- Orchestrates the entire processing pipeline
- Handles user management and data flow
- Integrates all system components

### 2. Data Processing

#### GCP Document AI (`gcp_docai.py`)
- Extracts structured data from receipt images
- Identifies line items, totals, taxes, and merchant information
- Provides entity recognition and text extraction

#### Firebase Storage (`firebase_store.py`)
- Manages all data persistence operations
- Stores user data, sessions, raw OCR data, and classifications
- Provides structured data organization across collections

### 3. AI Classification Pipeline

#### ADK Client (`gcp_adk_classification.py`)
- HTTP client for Google Agent Development Kit
- Handles communication with multi-agent systems
- Manages session creation and event streaming

#### Receipt Classifier Agents (`receipt_classifier/`)
Multi-agent system with sequential processing:

1. **Initial Classifier**: Categorizes line items (Groceries, Fast Food, etc.)
2. **Grouping Agent**: Groups items by category with totals
3. **Validation Loop**: 
   - **Reviewer**: Validates classification accuracy
   - **Refiner**: Corrects misclassifications
4. **Response Agent**: Generates final summary and saves to Firebase

## Data Flow

1. User uploads receipt image via Discord
2. Bot saves image locally and calls API
3. API processes image through GCP Document AI
4. OCR extracts entities (items, totals, taxes)
5. Raw data stored in Firebase
6. Classification pipeline triggered via ADK
7. Multi-agent system processes receipt:
   - Classifies items by category
   - Groups and calculates totals
   - Validates against receipt total
   - Refines if validation fails
8. Final classified data saved to Firebase

## Usage

### Starting the System

1. **Start the Main API**:
```bash
python main_api.py
```

2. **Start the Discord Bot**:
```bash
python bot.py
```

3. **Start the ADK Server**
```bash
adk web
```

4. **Upload Receipts**:
   - Send image attachments to the Discord bot
   - Bot will process and classify automatically
   - Results stored in Firebase collections

### API Endpoints
#### main_api.py
- `POST /register` - Register new user
- `GET /get_primary` - Get user's primary ID
- `POST /upload` - Process receipt image
#### adk web
- refer to /docs on the web.


### Discord Commands

- Upload any image attachment to trigger processing
- Bot handles registration flow automatically
- Provides session tracking and status updates

## Data Storage Structure

### Firebase Collections

```
USERDATA/
├── {primary_id}/
│   ├── sources/
│   │   └── {source}: {identifier}
│   └── metadata

SESSIONS/
├── {session_id}/
│   ├── timestamp
│   ├── user_id
│   └── source

DATA/
├── RAW_DATA/
│   └── {date}/
│       └── {session_id}: raw_ocr_data
├── RECEIPTS/
│   └── {date}/
│       └── {session_id}: extracted_entities
└── SUMMARIES/
    └── {date}/
        └── {session_id}: classified_data
```

## Agent Pipeline Details

### Validation Process
1. Calculate total from classified items
2. Compare with receipt total
3. If mismatch > threshold, trigger refinement
4. Refiner adjusts classifications to match total
5. Final validation before saving

## Error Handling

- Automatic fallback for OCR failures
- Retry logic for API calls
- Graceful degradation for classification errors
- Comprehensive logging throughout pipeline

## Development

### Project Structure
```
Spendify/
├── bot.py                      # Discord bot
├── main_api.py                 # Main API server
├── gcp_docai.py               # OCR processing
├── firebase_store.py          # Data storage
├── gcp_adk_classification.py  # ADK client
├── receipt_classifier/        # Agent pipeline
│   ├── agent.py              # Root agent
│   ├── subagents/            # Individual agents
│   └── schemas/              # Data schemas
├── img_content/              # Local image storage
├── uploads/                  # API uploads
└── requirements.txt          # Dependencies
```

### Adding New Features

1. **New Classification Categories**: Update agent schemas and prompts
2. **Additional Data Sources**: Extend bot.py with new integrations
3. **Enhanced Validation**: Modify reviewer/refiner agents
4. **Custom Storage**: Update firebase_store.py collections

## Monitoring and Logging

- Comprehensive logging across all components
- Session tracking for debugging
- Error capture and reporting
- Performance metrics collection

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

![SPENDIFY Process Flow](process.png)