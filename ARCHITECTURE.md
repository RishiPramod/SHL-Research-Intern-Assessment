# System Architecture

## Overview

The SHL Assessment Recommendation System is a semantic similarity-based recommendation engine that matches job descriptions to relevant SHL Individual Test Solutions assessments using state-of-the-art NLP techniques.

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser] -->|HTTP Request| B[FastAPI Server]
        C[API Client] -->|JSON Request| B
    end
    
    subgraph "API Layer"
        B --> D[Request Handler]
        D --> E[Input Validation]
        E --> F[Query Processor]
    end
    
    subgraph "Business Logic Layer"
        F --> G[Text Extraction]
        G -->|URL?| H[URL Text Extractor]
        G -->|Text| I[Query Embedder]
        H --> I
        I --> J[Similarity Engine]
        J --> K[Filtering & Ranking]
        K --> L[Balanced Selection]
    end
    
    subgraph "Data Layer"
        M[Assessment Catalogue<br/>CSV: 377+ assessments] --> N[Catalogue Loader]
        N --> O[Pre-computed Embeddings<br/>384-dim vectors]
        O --> J
        P[Sentence Transformer Model<br/>all-MiniLM-L6-v2] --> I
        P --> O
    end
    
    subgraph "Response Layer"
        L --> Q[Response Formatter]
        Q --> R[JSON Response]
        R --> B
        B --> A
        B --> C
    end
    
    style B fill:#4a90e2
    style J fill:#50c878
    style O fill:#ff6b6b
    style P fill:#ffa500
```

## Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Server
    participant Engine as Recommendation Engine
    participant Model as Embedding Model
    participant Catalogue as Assessment Catalogue
    
    Client->>API: POST /recommend<br/>{query: "Java developer"}
    API->>API: Validate Request
    API->>Engine: recommend_assessments()
    
    Engine->>Engine: Extract text from URL (if applicable)
    Engine->>Model: Encode query text
    Model-->>Engine: Query embedding (384-dim)
    
    Engine->>Catalogue: Get pre-computed embeddings
    Catalogue-->>Engine: Assessment embeddings matrix
    
    Engine->>Engine: Compute cosine similarity
    Engine->>Engine: Apply filters (duration, type)
    Engine->>Engine: Infer test types from query
    Engine->>Engine: Bucket by test type
    Engine->>Engine: Balanced round-robin selection
    Engine->>Engine: Sort by relevance score
    
    Engine-->>API: DataFrame with top 5-10 assessments
    API->>API: Format response
    API-->>Client: JSON response with recommendations
```

## Component Architecture

```mermaid
graph LR
    subgraph "api.py"
        A1[FastAPI App] --> A2[Startup Handler]
        A1 --> A3[Health Endpoint]
        A1 --> A4[Web UI Endpoint]
        A1 --> A5[Recommend Endpoint]
    end
    
    subgraph "recommender/engine.py"
        B1[recommend_assessments] --> B2[_maybe_expand_query_text]
        B1 --> B3[_infer_needed_test_types]
        B1 --> B4[_bucket_by_test_type]
        B1 --> B5[_balanced_select]
    end
    
    subgraph "models/embedding_model.py"
        C1[load_embedding_model] --> C2[SentenceTransformer]
    end
    
    subgraph "data/catalogue.py"
        D1[load_catalogue] --> D2[_parse_test_type]
        D1 --> D3[_add_derived_fields]
    end
    
    subgraph "utils/text_utils.py"
        E1[extract_text_from_url] --> E2[BeautifulSoup]
        E3[is_likely_url] --> E4[URL Regex]
    end
    
    A5 --> B1
    B1 --> C2
    B1 --> D1
    B2 --> E1
    B2 --> E3
    
    style A1 fill:#4a90e2
    style B1 fill:#50c878
    style C2 fill:#ffa500
    style D1 fill:#ff6b6b
```

## Recommendation Algorithm Flow

```mermaid
flowchart TD
    Start([Job Description Input]) --> CheckURL{Is URL?}
    CheckURL -->|Yes| Extract[Extract Text from URL]
    CheckURL -->|No| Embed[Generate Query Embedding]
    Extract --> Embed
    
    Embed --> Similarity[Compute Cosine Similarity<br/>vs All Assessments]
    Similarity --> Filter{Duration/Type<br/>Filters?}
    
    Filter -->|Yes| ApplyFilter[Apply Filters]
    Filter -->|No| InferTypes[Infer Test Types<br/>from Query]
    ApplyFilter --> InferTypes
    
    InferTypes --> Bucket[Bucket Assessments<br/>by Test Type]
    Bucket --> Balance[Round-Robin Selection<br/>across Types]
    
    Balance --> CheckCount{Count >= 5?}
    CheckCount -->|No| Fallback[Fallback to<br/>Similarity-based]
    Fallback --> Limit[Limit to Max 10]
    CheckCount -->|Yes| Limit
    
    Limit --> Sort[Sort by Relevance Score]
    Sort --> Format[Format Response]
    Format --> End([Return Recommendations])
    
    style Embed fill:#4a90e2
    style Similarity fill:#50c878
    style Balance fill:#ffa500
    style End fill:#ff6b6b
```

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend"
        A[HTML/CSS/JavaScript<br/>Jinja2 Templates]
    end
    
    subgraph "Backend Framework"
        B[FastAPI<br/>Python 3.10+]
    end
    
    subgraph "ML/NLP"
        C[Sentence Transformers<br/>all-MiniLM-L6-v2]
        D[scikit-learn<br/>Cosine Similarity]
    end
    
    subgraph "Data Processing"
        E[pandas<br/>DataFrames]
        F[numpy<br/>Array Operations]
    end
    
    subgraph "Utilities"
        G[BeautifulSoup<br/>HTML Parsing]
        H[requests<br/>HTTP Client]
    end
    
    A --> B
    B --> C
    B --> D
    B --> E
    C --> F
    B --> G
    G --> H
    
    style B fill:#4a90e2
    style C fill:#50c878
    style E fill:#ff6b6b
```

## Performance Optimization Strategy

```mermaid
graph LR
    A[Baseline: On-demand Embedding] -->|~800-1200ms| B[Slow Response]
    
    C[Optimization 1:<br/>Pre-compute Embeddings] -->|85-90% reduction| D[~50-150ms]
    
    E[Optimization 2:<br/>Normalized Embeddings] -->|Better Accuracy| D
    
    F[Optimization 3:<br/>Balanced Selection] -->|Diversity| D
    
    G[Optimization 4:<br/>Efficient Text Processing] -->|Robustness| D
    
    D --> H[Fast Response<br/>Production Ready]
    
    style C fill:#50c878
    style D fill:#4a90e2
    style H fill:#ff6b6b
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        A[Local Machine] -->|python start.py| B[Uvicorn Server<br/>localhost:8000]
    end
    
    subgraph "Production - Railway"
        C[GitHub Repository] -->|Auto Deploy| D[Railway Platform]
        D --> E[Build Process]
        E --> F[Install Dependencies]
        F --> G[Load Model & Catalogue]
        G --> H[Pre-compute Embeddings]
        H --> I[Start API Server]
        I --> J[Public URL<br/>HTTPS]
    end
    
    K[Client Requests] --> J
    J --> I
    
    style D fill:#4a90e2
    style J fill:#50c878
    style I fill:#ffa500
```

## Data Pipeline

```mermaid
graph LR
    A[SHL Website<br/>Product Catalog] -->|Web Scraping| B[Raw HTML Data]
    B -->|Parse & Extract| C[Assessment Metadata]
    C -->|Structure| D[CSV Catalogue<br/>377+ assessments]
    
    D -->|Load| E[Catalogue Loader]
    E -->|Process| F[Combined Text Fields]
    F -->|Embed| G[384-dim Embeddings]
    G -->|Store in Memory| H[Pre-computed Embeddings<br/>numpy array]
    
    I[Query Input] -->|Embed| J[Query Embedding]
    J -->|Compare| H
    H -->|Similarity Search| K[Ranked Results]
    
    style D fill:#ff6b6b
    style G fill:#ffa500
    style H fill:#50c878
    style K fill:#4a90e2
```

## Key Design Decisions

1. **Pre-computation**: All assessment embeddings computed at startup (trade-off: 2-3s startup for 50-150ms queries)
2. **Normalized Embeddings**: Unit vectors for reliable cosine similarity
3. **Balanced Selection**: Round-robin across test types for diversity
4. **Fallback Strategy**: Ensures minimum 5 recommendations even if filters are too restrictive
5. **URL Support**: Automatic text extraction from job description URLs
