AI-Based Data Acquisition Agent - Internship Use-Case Document

Background: 
This use-case represents a core foundational task within a broader AI Data Engineering and Intelligent Agent Program.

Objective: 
Develop an AI-based Data Acquisition Agent that:
•	Takes a landing URL (e.g., a government or open-data website)
•	Scans through the page, understands its structure, and hops recursively up to 2–3 levels
•	Identifies and downloads all relevant data files (e.g., .csv, .xlsx, .json, .zip, .pdf)
•	Captures metadata about each discovered dataset — such as source URL, crawl depth, file type, and timestamp
•	Optionally integrates AI reasoning to evaluate which links or pages are likely to contain valuable datasets

Scope of Work
1.	Core Tasks
•	Build a web crawler that:
o	Accepts a landing URL as input
o	Extracts and follows links up to a configurable depth (2–3 levels)
o	Detects downloadable data file links and fetches them automatically
o	Store every discovered dataset and related metadata locally or in a database
o	Handle exceptions gracefully (broken links, network failures, file naming conflicts, etc.)

2.	AI Layer (Optional / Bonus)
•	Use an LLM reasoning module (OpenAI GPT-4o, Mistral, Claude, or Llama) to prioritize crawling pages that are semantically “data-rich” or “statistically relevant”
•	Example prompt usage: “Given this HTML snippet, identify whether this page likely contains downloadable data files or statistical reports”

3.	Metadata Enrichment
•	For each downloaded file, 
o	Extract & store file_name, url, depth, content_type, file_size, timestamp
o	Add optional tagging (keywords such as GDP, CPI, Inflation, MSME, Agriculture, etc.) using embeddings or keyword extraction. 

Component Suggested Tools / Libraries Description
Crawler Engine 
aiohttp, requests, beautifulsoup4
Fetch and parse HTML pages

Link Resolver
urllib.parse, urlextract
Normalize and join relative URLs

File Detector
mimetypes, magic, tika
Detect valid data file types 

AI Reasoner
openai, litellm, transformers 
Prioritize or score relevance

Database Layer
psycopg2, sqlalchemy
Store crawl metadata

CLI Interface 
typer, argparse, rich.progress
Command-line interface with progress feedback

CREATE TABLE acquisition_metadata (
run_id SERIAL PRIMARY KEY,   
url TEXT,   
file_name TEXT,   
depth INT,   
content_type TEXT,   
file_size_kb NUMERIC,   
ai_score FLOAT,   
timestamp TIMESTAMP DEFAULT NOW()
);


Outcome
Selected candidates will demonstrate their ability to:
•	Build autonomous, intelligent data acquisition pipelines.
•	Combine Python engineering with AI reasoning.
•	Contribute to next-generation AI-driven data platforms
