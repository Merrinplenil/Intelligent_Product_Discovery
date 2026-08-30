# 🛋️ Intelligent Product Discovery System

An AI-powered product discovery system that combines **SQL filtering** and **vector semantic search** to understand natural language product queries and retrieve relevant products intelligently.

## Features
- Natural language product search
- SQL-based structured filtering
- Vector-based semantic search
- Hybrid retrieval strategies
- AI-powered query planning
- Result evaluation with confidence scores
- Streamlit-based user interface

## 🔍 Execution Plans

### SQL_ONLY
Used for exact or structured constraints.
```text
living room furniture under $200
```

### VECTOR_ONLY
Used for primarily semantic or descriptive queries.
```text
cosy furniture for a reading corner
```

### SQL_TO_VECTOR
SQL filters structured constraints first, then vector search ranks candidates semantically.
```text
modern sofa under $500
```

### VECTOR_TO_SQL
Vector search retrieves semantically relevant products first, then SQL applies exact constraints.
```text
something warm and inviting for a peaceful corner under $300
```

##  Project Architecture
```text
User Query
    ↓
Query Planner
    ↓
Execution Plan Selection
    ↓
SQL Search / Vector Search / Hybrid Search
    ↓
Result Evaluator
    ↓
Product Results
```

## Technologies Used
- Python
- Streamlit
- LangChain
- Groq
- ChromaDB
- Sentence Transformers
- MySQL
- Hugging Face Embeddings

##  Project Structure
```text
intelligent_product_discovery/
├── data/
│   ├── ikea_products_cleaned.csv
│   ├── ikea_products_embedding_ready.csv
│   ├── ikea_sample_file.json
│   └── chroma_db/                  # Generated locally
├── src/
│   ├── database/
│   │   ├── connection.py
│   │   ├── load_products.py
│   │   └── sql_retriever.py
│   ├── embeddings/
│   │   ├── generate_embeddings.py
│   │   ├── prepare_text.py
│   │   └── vector_retriever.py
│   ├── execution_engine.py
│   ├── query_planner.py
│   ├── response_formatter.py
│   └── result_evaluator.py
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

##  Installation

```bash
git clone https://github.com/Merrinplenil/Intelligent_Product_Discovery.git
cd Intelligent_Product_Discovery
python -m venv .venv
```

Activate on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

##  Environment Variables

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_api_key_here
```

Do not upload the `.env` file to GitHub.

##  ChromaDB Setup

The `data/chroma_db/` folder is not included in the repository because it is a large generated vector database.

The repository includes the embedding-ready product dataset through Git LFS.

To generate the ChromaDB vector database, run:

```bash
python src/embeddings/generate_embeddings.py
```

This script generates vector embeddings and creates the ChromaDB database inside:

```text
data/chroma_db/
```

After this step, the vector search functionality is ready to use.

> **Note:** If the embedding-ready dataset needs to be regenerated, first run:

```bash
python src/embeddings/prepare_text.py
```

## ▶️ Run the Application

```bash
streamlit run app.py
```

The Streamlit application will open in your browser.

##  Sample Queries

**SQL_ONLY**
```text
living room furniture under $200
```

**VECTOR_ONLY**
```text
cosy furniture for a reading corner
```

**SQL_TO_VECTOR**
```text
modern sofa under $500
```

**VECTOR_TO_SQL**
```text
something warm and inviting for a peaceful corner under $300
```

##  Project Goal

The goal of this project is to demonstrate how structured database retrieval and semantic vector search can be combined to build a more intelligent product discovery system.

The system analyzes a natural language query, separates structured and semantic constraints, selects an appropriate execution plan, retrieves relevant products, and evaluates the final results.

##  Author

Merrin 
