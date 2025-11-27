# Centre AI MCP Server - Integration Guide

## 🔌 Integration mit AI Modellen

### Ollama Integration

Der MCP Server funktioniert perfekt mit Ollama:

```python
import requests

# MCP Tools abrufen
response = requests.get(
    'http://localhost:5000/mcp/tools/list',
    headers={'X-API-Key': 'dev-api-key-12345'}
)
tools = response.json()['tools']

# Tool ausführen
response = requests.post(
    'http://localhost:5000/mcp/tools/execute',
    headers={
        'X-API-Key': 'dev-api-key-12345',
        'Content-Type': 'application/json'
    },
    json={
        'tool_name': 'text_length',
        'parameters': {'text': 'Hello World'}
    }
)
result = response.json()
```

### Claude/Anthropic Integration

```python
import anthropic
import requests

# MCP Server für Tools verwenden
def get_mcp_tools():
    response = requests.get(
        'http://localhost:5000/mcp/tools/list',
        headers={'X-API-Key': 'your-api-key'}
    )
    return response.json()['tools']

# Mit Claude verwenden
client = anthropic.Anthropic(api_key="your-key")

# Tool-Calls an MCP Server weiterleiten
def execute_tool(tool_name, parameters):
    response = requests.post(
        'http://localhost:5000/mcp/tools/execute',
        headers={'X-API-Key': 'your-api-key'},
        json={
            'tool_name': tool_name,
            'parameters': parameters
        }
    )
    return response.json()
```

### LangChain Integration

```python
from langchain.tools import Tool
import requests

class MCPTool:
    def __init__(self, api_key, base_url='http://localhost:5000'):
        self.api_key = api_key
        self.base_url = base_url

    def get_tools(self):
        """Lade alle MCP Tools als LangChain Tools"""
        response = requests.get(
            f'{self.base_url}/mcp/tools/list',
            headers={'X-API-Key': self.api_key}
        )
        mcp_tools = response.json()['tools']

        langchain_tools = []
        for tool in mcp_tools:
            langchain_tools.append(
                Tool(
                    name=tool['name'],
                    func=lambda params, t=tool['name']: self.execute(t, params),
                    description=tool['description']
                )
            )
        return langchain_tools

    def execute(self, tool_name, parameters):
        """Führe MCP Tool aus"""
        response = requests.post(
            f'{self.base_url}/mcp/tools/execute',
            headers={'X-API-Key': self.api_key},
            json={
                'tool_name': tool_name,
                'parameters': parameters
            }
        )
        return response.json()

# Verwenden
mcp = MCPTool(api_key='your-api-key')
tools = mcp.get_tools()
```

### OpenAI Function Calling

```python
import openai
import requests

# MCP Tools für OpenAI formatieren
def get_openai_functions():
    response = requests.get(
        'http://localhost:5000/mcp/tools/list',
        headers={'X-API-Key': 'your-api-key'}
    )
    tools = response.json()['tools']

    functions = []
    for tool in tools:
        functions.append({
            'name': tool['name'],
            'description': tool['description'],
            'parameters': {
                'type': 'object',
                'properties': tool['parameters'],
                'required': [
                    k for k, v in tool['parameters'].items()
                    if v.get('required', False)
                ]
            }
        })
    return functions

# Mit OpenAI verwenden
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Zähle die Zeichen in 'Hello'"}],
    functions=get_openai_functions(),
    function_call="auto"
)

# Function Call ausführen
if response.choices[0].message.get("function_call"):
    function_name = response.choices[0].message["function_call"]["name"]
    arguments = response.choices[0].message["function_call"]["arguments"]

    # An MCP Server weiterleiten
    result = requests.post(
        'http://localhost:5000/mcp/tools/execute',
        headers={'X-API-Key': 'your-api-key'},
        json={
            'tool_name': function_name,
            'parameters': json.loads(arguments)
        }
    )
```

## 🔐 Verschiedene Auth-Methoden verwenden

### API Key in Python

```python
import requests

headers = {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:5000/mcp/tools/execute',
    headers=headers,
    json={...}
)
```

### Bearer Token in Python

```python
import requests

headers = {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:5000/mcp/tools/execute',
    headers=headers,
    json={...}
)
```

### Basic Auth in Python

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    'http://localhost:5000/mcp/tools/execute',
    auth=HTTPBasicAuth('admin', 'password'),
    json={...}
)
```

## 💾 Memory System verwenden

### Konversations-Gedächtnis

```python
class ConversationMemory:
    def __init__(self, api_key, base_url='http://localhost:5000'):
        self.api_key = api_key
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())

    def store_message(self, role, content):
        """Speichere Nachricht"""
        requests.post(
            f'{self.base_url}/mcp/memory/store',
            headers={'X-API-Key': self.api_key},
            json={
                'key': f'{self.session_id}_{role}_{time.time()}',
                'value': {'role': role, 'content': content},
                'tags': [self.session_id, role, 'conversation']
            }
        )

    def get_history(self):
        """Lade Konversations-Historie"""
        response = requests.get(
            f'{self.base_url}/mcp/memory/retrieve',
            headers={'X-API-Key': self.api_key},
            params={'tags': [self.session_id, 'conversation']}
        )
        return response.json()['results']
```

### Context Caching

```python
def cache_context(key, data, ttl=3600):
    """Cache Kontext für wiederholte Verwendung"""
    requests.post(
        'http://localhost:5000/mcp/memory/store',
        headers={'X-API-Key': 'your-api-key'},
        json={
            'key': key,
            'value': data,
            'tags': ['cache'],
            'ttl': ttl  # 1 Stunde
        }
    )

def get_cached_context(key):
    """Lade gecachten Kontext"""
    response = requests.get(
        'http://localhost:5000/mcp/memory/retrieve',
        headers={'X-API-Key': 'your-api-key'},
        params={'key': key}
    )
    return response.json()['value']
```

## 🚀 Production Deployment

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Mit SSL (Let's Encrypt)

```bash
# Certbot installieren
apt-get install certbot python3-certbot-nginx

# SSL Zertifikat erhalten
certbot --nginx -d your-domain.com

# Auto-Renewal
certbot renew --dry-run
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: centre-ai-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: centre-ai:latest
        ports:
        - containerPort: 5000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: secret-key
```

## 📊 Monitoring

### Prometheus Integration

```python
# In app.py hinzufügen
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

## 🔒 Sicherheit Best Practices

1. **API Keys rotieren**: Ändere regelmäßig die API Keys
2. **HTTPS verwenden**: Nur verschlüsselte Verbindungen
3. **Rate Limiting**: Begrenze Anfragen pro Nutzer
4. **Input Validation**: Validiere alle Eingaben
5. **Logs monitoren**: Überwache verdächtige Aktivitäten

## 📝 Beispiel-Integration

Vollständiges Beispiel:

```python
import requests
from typing import List, Dict, Any

class CentreAIMCP:
    def __init__(self, api_key: str, base_url: str = 'http://localhost:5000'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })

    def list_tools(self) -> List[Dict[str, Any]]:
        response = self.session.get(f'{self.base_url}/mcp/tools/list')
        response.raise_for_status()
        return response.json()['tools']

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f'{self.base_url}/mcp/tools/execute',
            json={
                'tool_name': tool_name,
                'parameters': parameters
            }
        )
        response.raise_for_status()
        return response.json()

    def store_memory(self, key: str, value: Any, tags: List[str] = None):
        response = self.session.post(
            f'{self.base_url}/mcp/memory/store',
            json={
                'key': key,
                'value': value,
                'tags': tags or []
            }
        )
        response.raise_for_status()
        return response.json()

    def get_memory(self, key: str) -> Any:
        response = self.session.get(
            f'{self.base_url}/mcp/memory/retrieve',
            params={'key': key}
        )
        response.raise_for_status()
        return response.json()['value']

# Verwenden
mcp = CentreAIMCP(api_key='your-api-key')

# Tools auflisten
tools = mcp.list_tools()
print(f"Verfügbare Tools: {len(tools)}")

# Tool ausführen
result = mcp.execute_tool('text_length', {'text': 'Hello'})
print(f"Ergebnis: {result}")

# Memory verwenden
mcp.store_memory('user_context', {'name': 'John', 'preference': 'dark_mode'})
context = mcp.get_memory('user_context')
print(f"Kontext: {context}")
```
