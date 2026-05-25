# servicenow-incidents

A FastAPI web application that searches ServiceNow incidents by number or short description.

## Features

- `GET /search?q=<term>` — search incidents where `number={q}` OR `short_description LIKE {q}`
- Simple HTML frontend with a search box
- ServiceNow Table API integration via `requests`
- Credentials loaded from environment variables

## Prerequisites

- Python 3.10+
- A ServiceNow instance with REST API access
- A ServiceNow user with permission to read the `incident` table

## Setup

1. Clone or copy this project and enter the directory:

   ```bash
   cd servicenow-incidents
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy the example environment file and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```env
   SN_INSTANCE=your-instance
   SN_USER=your-username
   SN_PASSWORD=your-password
   ```

   `SN_INSTANCE` can be:
   - An instance name such as `dev12345`
   - A hostname such as `dev12345.service-now.com`
   - A full URL such as `https://dev12345.service-now.com`

## Run the application

```bash
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to use the search UI.

Interactive API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API usage

Search incidents:

```bash
curl "http://127.0.0.1:8000/search?q=INC0010001"
```

Example response:

```json
{
  "query": "INC0010001",
  "count": 1,
  "incidents": [
    {
      "number": "INC0010001",
      "short_description": "Network outage in building A",
      "state": "In Progress",
      "priority": "2 - High",
      "sys_id": "abc123..."
    }
  ]
}
```

## Error handling

The API returns clear HTTP errors for common issues:

- `401` — invalid ServiceNow credentials
- `403` — user lacks access to incidents
- `500` — missing environment variables
- `502` / `504` — ServiceNow connectivity or response errors

## Project structure

```text
servicenow-incidents/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
└── static/
    └── index.html
```
