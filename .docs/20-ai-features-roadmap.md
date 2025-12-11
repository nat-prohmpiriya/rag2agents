# AI Features Roadmap

## Document Info

| | |
|--|--|
| **Version** | 1.0 |
| **Date** | December 2025 |
| **Status** | Planning |
| **Reference** | Industry Standards (ChatGPT, Claude, Gemini) |

---

## Current Status Overview

### Features Comparison with Industry Leaders

| Category | Feature | ChatGPT | Claude | Gemini | **Our App** |
|----------|---------|---------|--------|--------|-------------|
| **Core Chat** | Text conversation | ✅ | ✅ | ✅ | ✅ |
| | Streaming response | ✅ | ✅ | ✅ | ✅ |
| | Multi-turn context | ✅ | ✅ | ✅ | ✅ |
| | System prompts | ✅ | ✅ | ✅ | ✅ |
| **Multi-Model** | Switch models | ✅ | ✅ | ✅ | ✅ |
| | Model comparison | ✅ | - | ✅ | ❌ |
| **RAG/Documents** | Upload documents | ✅ | ✅ | ✅ | ✅ |
| | PDF/DOCX/TXT | ✅ | ✅ | ✅ | ✅ |
| | Chat with docs | ✅ | ✅ | ✅ | ✅ |
| | Source citations | ✅ | ✅ | ✅ | ✅ |
| **Agents/Tools** | Function calling | ✅ | ✅ | ✅ | ✅ |
| | Custom agents | ✅ | ✅ | - | ✅ |
| | RAG search tool | ✅ | ✅ | ✅ | ✅ |
| | Calculator | ✅ | ✅ | ✅ | ✅ |
| | Web search | ✅ | ✅ | ✅ | ❌ |
| | Code execution | ✅ | ✅ | ✅ | ❌ |
| **Multimodal** | Image analysis | ✅ | ✅ | ✅ | ❌ |
| | Image generation | ✅ | - | ✅ | ❌ |
| | Voice input (STT) | ✅ | - | ✅ | ❌ |
| | Voice output (TTS) | ✅ | - | ✅ | ❌ |
| **Deep Research** | Long-form research | ✅ | ✅ | ✅ | ❌ |
| | Multiple sources | ✅ | ✅ | ✅ | ❌ |
| **Workspace** | Projects/Folders | ✅ | ✅ | ✅ | ✅ |
| | Artifacts/Canvas | ✅ | ✅ | - | ❌ |
| | Export results | ✅ | ✅ | ✅ | ❌ |
| **Analytics** | Token usage | ✅ | ✅ | ✅ | ✅ |
| | Cost tracking | ✅ | ✅ | ✅ | ✅ |
| **Memory** | Conversation history | ✅ | ✅ | ✅ | ✅ |
| | Long-term memory | ✅ | ✅ | ✅ | ❌ |

---

## Features We Have (Ready to Showcase)

### 1. RAG Pipeline ✅
- Document upload (PDF, DOCX, TXT, MD, CSV)
- Text chunking with recursive splitter
- Embedding via LiteLLM (Gemini text-embedding-004)
- Vector storage with pgvector
- Semantic search with cosine similarity
- Source citations in responses

### 2. Multi-Model Support ✅
- OpenAI (GPT-3.5, GPT-4, GPT-4o)
- Google (Gemini 1.5 Flash, Gemini 1.5 Pro)
- Anthropic (Claude 3 Haiku, Sonnet, Opus)
- Groq (Llama 3.1, Mixtral)
- Model selector with pricing info

### 3. AI Agents ✅
- AgentEngine with tool execution
- Built-in tools: `rag_search`, `calculator`, `summarize`
- Custom agents (user-defined)
- YAML-based agent configuration
- AgentThinking visualization

### 4. Analytics ✅
- Token usage tracking
- Request count by type
- Cost calculation per model
- Usage breakdown charts

### 5. Project Organization ✅
- Project CRUD
- Document assignment to projects
- RAG filtering by project scope

---

## Features to Add (Priority Order)

### Phase 1: Quick Wins (1-2 days each)

#### 1.1 Image Analysis (Vision)
**Description:** Analyze images using Vision models

**Implementation:**
- Use Gemini 1.5 Pro Vision or GPT-4V
- Accept image upload in chat
- Support: JPG, PNG, GIF, WebP
- Use cases: describe image, extract text (OCR), analyze charts

**Backend:**
```python
# app/services/vision.py
async def analyze_image(image_data: bytes, prompt: str, model: str) -> str:
    # Convert to base64
    # Send to LiteLLM with image content
    pass
```

**Frontend:**
- Add image upload button in chat input
- Display image preview in message
- Show analysis result

---

#### 1.2 Image Generation
**Description:** Generate images from text prompts

**Implementation:**
- Use OpenAI DALL-E 3 or Google Imagen 3
- Support different sizes and styles
- Save generated images

**Backend:**
```python
# app/services/image_gen.py
async def generate_image(prompt: str, size: str, style: str) -> ImageResult:
    # Call DALL-E or Imagen API
    # Save to storage
    # Return URL
    pass
```

**Frontend:**
- Image generation page
- Prompt input with style options
- Gallery of generated images
- Download/save options

---

### Phase 2: Medium Priority (3-5 days each)

#### 2.1 Web Search Tool
**Description:** Search the web for real-time information

**Implementation:**
- Use Tavily API or Serper API
- Add as agent tool
- Return structured results with sources

**Backend:**
```python
# app/agents/tools/web_search.py
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information"

    async def execute(self, query: str) -> ToolResult:
        # Call search API
        # Format results
        pass
```

**Use Cases:**
- Current events
- Latest documentation
- Real-time data (stock prices, weather)

---

#### 2.2 Artifacts/Canvas
**Description:** Display code, diagrams, documents in separate panel

**Implementation:**
- Side panel component
- Support: Code, Markdown, HTML preview, Mermaid diagrams
- Edit and iterate

**Frontend:**
```svelte
<!-- ArtifactPanel.svelte -->
<script>
  let { artifact } = $props();
  // Render based on type: code, markdown, html, diagram
</script>
```

**Use Cases:**
- Code generation with preview
- Document drafting
- Diagram creation

---

#### 2.3 Export Results
**Description:** Export conversations and artifacts

**Formats:**
- Markdown (.md)
- PDF
- JSON (raw data)

**Implementation:**
- Export button in conversation
- Select format dialog
- Generate and download

---

### Phase 3: Advanced Features (1+ week each)

#### 3.1 Code Execution (Sandbox)
**Description:** Execute Python/JavaScript code safely

**Implementation:**
- Docker sandbox with resource limits
- Timeout: 30 seconds
- Memory limit: 256MB
- No network access (optional)

**Backend:**
```python
# app/services/code_executor.py
async def execute_code(code: str, language: str) -> ExecutionResult:
    # Run in Docker container
    # Capture stdout/stderr
    # Return result
    pass
```

**Security:**
- Isolated container per execution
- No persistent storage
- Whitelist allowed packages

---

#### 3.2 Voice Input/Output
**Description:** Speech-to-text and text-to-speech

**Implementation:**
- STT: Whisper API or Google Speech
- TTS: OpenAI TTS or Google TTS

**Frontend:**
- Microphone button for voice input
- Speaker button for TTS playback
- Audio visualization

---

#### 3.3 Deep Research Mode
**Description:** Generate comprehensive research reports

**Implementation:**
- Multi-step research process
- Search multiple sources
- Synthesize into structured report
- Include citations

**Workflow:**
1. User provides topic
2. Agent breaks down into sub-questions
3. Search web + documents for each
4. Synthesize findings
5. Generate report with sources

---

#### 3.4 Long-term Memory
**Description:** Remember user preferences across conversations

**Implementation:**
- Memory model (key-value pairs)
- Extract facts from conversations
- Inject relevant memories into context

**Backend:**
```python
# app/models/memory.py
class UserMemory(Base):
    id: uuid
    user_id: uuid
    key: str
    value: str
    confidence: float
    created_at: datetime
```

---

### Phase 4: Future (Roadmap)

#### 4.1 Multi-Agent Orchestration
- Multiple agents collaborate
- Task delegation
- Result aggregation

#### 4.2 Workflow Automation
- Visual workflow builder
- Trigger-based execution
- Scheduled tasks

#### 4.3 API Integration Tool
- Connect external APIs
- OAuth support
- Custom integrations

#### 4.4 Text-to-SQL
- Natural language to SQL
- Schema linking
- Safe query execution

---

## Implementation Priority for Portfolio

### Must Have (Proves AI App Developer Skills)
1. ✅ Multi-model Chat
2. ✅ RAG Pipeline
3. ✅ AI Agents + Tools
4. ✅ Analytics
5. ⬜ Image Analysis (Vision)
6. ⬜ Image Generation

### Nice to Have (Differentiators)
7. ⬜ Web Search Tool
8. ⬜ Artifacts/Canvas
9. ⬜ Code Execution

### Advanced (Impressive but Optional)
10. ⬜ Voice I/O
11. ⬜ Deep Research
12. ⬜ Long-term Memory

---

## Technical Stack for New Features

| Feature | API/Service | Cost |
|---------|-------------|------|
| Image Analysis | Gemini 1.5 Pro Vision | $0.00025/image |
| Image Generation | DALL-E 3 | $0.04-0.12/image |
| Image Generation | Imagen 3 | $0.02/image |
| Web Search | Tavily API | $5/1000 searches |
| Web Search | Serper API | Free tier available |
| Code Execution | Docker | Self-hosted |
| STT | Whisper API | $0.006/minute |
| TTS | OpenAI TTS | $0.015/1K chars |

---

## References

- [ChatGPT vs Claude vs Gemini 2025](https://creatoreconomy.so/p/chatgpt-vs-claude-vs-gemini-the-best-ai-model-for-each-use-case-2025)
- [LLM Comparison 2025](https://vertu.com/lifestyle/top-8-ai-models-ranked-gemini-3-chatgpt-5-1-grok-4-claude-4-5-more/)
- [AI Platform Comparison for Business](https://aloa.co/ai/comparisons/llm-comparison/chatgpt-vs-claude-vs-gemini)

---

*Last updated: December 4, 2024*
