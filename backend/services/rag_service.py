import os
import re
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader  # pyre-ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # pyre-ignore
from langchain_huggingface import HuggingFaceEmbeddings  # pyre-ignore
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)

from backend.config import (  # pyre-ignore
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    LLM_PROVIDER,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    CHAT_MODEL_OPENAI,
    CHAT_MODEL_GEMINI,
    RETRIEVER_K,
    QDRANT_URL,
    QDRANT_COLLECTION,
)

logger = logging.getLogger(__name__)

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ── Globals & Prompts ─────────────────────────────────────────────────
_embeddings = None
_qdrant: QdrantClient | None = None

INSURANCE_TYPES = {"motor", "health", "travel", "crop", "general"}

DEFAULT_RAG_PROMPT = """You are an expert insurance policy assistant.
Answer the user's question using ONLY the provided policy excerpts.

RULES:
1. Start with "🧠 **AI Answer:**". Be highly concise.
2. For specific details use structured fields (Policy Name: X).
3. **Bold** key numbers, amounts, and limits.
4. Keep under 2 lines. No paragraphs.
5. If unsure, say the information is missing from the documents.

Context:
{context}

Question: {question}

Answer:"""


# ── Embeddings ────────────────────────────────────────────────────────

class MockEmbeddings:
    """Mock embeddings for when no internet is available."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]
    def embed_query(self, text: str) -> list[float]:
        return [0.0] * 384


def get_embeddings():
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    try:
        logger.info("Initializing HuggingFace embeddings...")
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return _embeddings
    except Exception as e:
        logger.warning("HuggingFace embeddings failed: %s. Trying Gemini...", e)
        if GOOGLE_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                _embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=GOOGLE_API_KEY
                )
                logger.info("Gemini embeddings initialized.")
                return _embeddings
            except Exception as ge:
                logger.error("Gemini embeddings also failed: %s", ge)

        logger.warning(
            "⚠️ MockEmbeddings active — similarity search non-functional. "
            "Check internet or GOOGLE_API_KEY."
        )
        _embeddings = MockEmbeddings()
        return _embeddings


# ── Qdrant client ─────────────────────────────────────────────────────

def get_qdrant() -> QdrantClient | None:
    """Get or create the Qdrant client. Returns None if Qdrant is unreachable."""
    global _qdrant
    if _qdrant is not None:
        return _qdrant

    try:
        client = QdrantClient(url=QDRANT_URL, timeout=5)
        # Test connectivity
        existing = [c.name for c in client.get_collections().collections]
        if QDRANT_COLLECTION not in existing:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection: %s", QDRANT_COLLECTION)
        else:
            logger.info("Connected to existing Qdrant collection: %s", QDRANT_COLLECTION)
        _qdrant = client
        return _qdrant
    except Exception as e:
        logger.error(
            "⚠️ Cannot connect to Qdrant at %s: %s. "
            "Make sure Docker is running: docker run -d -p 6333:6333 qdrant/qdrant",
            QDRANT_URL, e
        )
        return None


# ── LLM chain ─────────────────────────────────────────────────────────

_llm_chain: list = []


def _build_llm_chain() -> list:
    """Build an ordered list of available LLMs — Gemini first, OpenAI second."""
    global _llm_chain
    if _llm_chain:
        return _llm_chain

    llms = []

    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # pyre-ignore
            llms.append({
                "name": "Gemini",
                "llm": ChatGoogleGenerativeAI(
                    model=CHAT_MODEL_GEMINI,
                    temperature=0,
                    google_api_key=GOOGLE_API_KEY,
                    max_retries=1,
                    timeout=30,
                )
            })
            logger.info("Gemini added to LLM chain")
        except Exception as e:
            logger.warning("Could not init Gemini: %s", e)

    if OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI  # pyre-ignore
            llms.append({
                "name": "OpenAI",
                "llm": ChatOpenAI(
                    model=CHAT_MODEL_OPENAI,
                    temperature=0,
                    max_retries=1,
                    request_timeout=30,
                )
            })
            logger.info("OpenAI added to LLM chain")
        except Exception as e:
            logger.warning("Could not init OpenAI: %s", e)

    _llm_chain = llms
    return _llm_chain


def reset_llm_chain():
    global _llm_chain
    _llm_chain = []


def _is_rate_limit_error(e: Exception) -> bool:
    """Check if an exception is a rate limit / quota error."""
    err = str(e).lower()
    return any(word in err for word in [
        "quota", "rate", "limit", "429", "too many",
        "resource_exhausted", "exceeded"
    ])


def _try_llm_chain(context: str, question: str, prompt_template: str | None = None) -> str | None:
    """
    Try each LLM in the chain in order.
    Returns answer string or None if all fail.
    """
    from langchain_core.prompts import PromptTemplate  # pyre-ignore
    from langchain_core.output_parsers import StrOutputParser  # pyre-ignore

    template = prompt_template or DEFAULT_RAG_PROMPT
    prompt = PromptTemplate.from_template(template)

    for provider in _build_llm_chain():
        name = provider["name"]
        llm  = provider["llm"]
        try:
            chain  = prompt | llm | StrOutputParser()
            answer = chain.invoke({"context": context, "question": question})
            logger.info("Answer generated by %s", name)
            return answer

        except Exception as e:
            if _is_rate_limit_error(e):
                logger.warning("%s rate limited — trying next provider", name)
            else:
                logger.warning("%s failed (%s) — trying next provider", name, str(e)[:80])
            continue

    logger.warning("All LLM providers failed — falling back to extractive QA")
    return None


# ── Ingestion ─────────────────────────────────────────────────────────

def ingest_file(file_path: str, insurance_type: str = "general") -> int:
    """
    Ingest a document into Qdrant, tagged with insurance_type.
    insurance_type: motor | health | travel | crop | general
    """
    client = get_qdrant()
    if client is None:
        logger.error("Qdrant unavailable — cannot ingest %s", file_path)
        return 0

    insurance_type = insurance_type.lower()
    if insurance_type not in INSURANCE_TYPES:
        insurance_type = "general"

    path = Path(file_path)
    ext  = path.suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
    elif ext in (".txt", ".md"):
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()
    splitter  = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        logger.warning("No chunks from %s", file_path)
        return 0

    emb = get_embeddings()

    # Get current max ID for offset
    count  = client.count(collection_name=QDRANT_COLLECTION).count
    points = []

    for i, chunk in enumerate(chunks):
        vector = emb.embed_query(chunk.page_content)
        points.append(PointStruct(
            id      = count + i + 1,
            vector  = vector,
            payload = {
                "text":           chunk.page_content,
                "source":         str(path.name),
                "insurance_type": insurance_type,
                "page":           chunk.metadata.get("page", 0),
            }
        ))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    logger.info("Ingested %d chunks [%s] from %s", len(chunks), insurance_type, file_path)
    return len(chunks)


# ── Retrieval ─────────────────────────────────────────────────────────

def _retrieve(question: str, insurance_type: str | None = None, k: int = RETRIEVER_K) -> list:
    """
    Retrieve top-k chunks. If insurance_type given, filter to that type only.
    Falls back to unfiltered search if filtered results are empty.
    """
    client = get_qdrant()
    if client is None:
        return []

    emb    = get_embeddings()
    vector = emb.embed_query(question)

    search_filter = None
    if insurance_type and insurance_type.lower() in INSURANCE_TYPES:
        search_filter = Filter(
            must=[FieldCondition(
                key="insurance_type",
                match=MatchValue(value=insurance_type.lower())
            )]
        )

    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vector,
        limit=k,
        query_filter=search_filter,
        with_payload=True,
    )

    # Fallback: if no results with filter, search without
    if not results and search_filter:
        logger.warning("No %s docs found — falling back to unfiltered search", insurance_type)
        results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=k,
            with_payload=True,
        )

    return results


# ── Answer helpers ────────────────────────────────────────────────────

def _extract_section_info(text: str) -> str:
    """Try to extract a section/heading reference from a chunk of text."""
    patterns = [
        r'(SECTION\s+\d+[^═\n]{0,60})',
        r'(\d+\.\d+\s+[A-Z][^\n]{3,50})',
        r'(Article\s+\d+[^\n]{0,50})',
        r'(Part\s+[A-Z0-9]+[^\n]{0,50})',
        r'(Chapter\s+\d+[^\n]{0,50})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip('═ ')
    return ""


def _extract_key_values(text: str) -> list[str]:
    """Extract key numerical/monetary values from text for bold highlighting."""
    highlights = []
    highlights.extend(re.findall(r'[\$₹]\s?[\d,]+(?:\.\d+)?', text))
    highlights.extend(re.findall(r'\d+(?:\.\d+)?%', text))
    highlights.extend(re.findall(r'\d+\s+(?:days?|months?|years?|hours?)', text, re.IGNORECASE))
    return list(set(highlights))


def _calculate_confidence(question: str, results: list) -> str:
    """Estimate answer confidence based on exact/partial matches in retrieval."""
    if not results:
        return "Low"

    doc_text = results[0].payload.get("text", "").lower()
    clean_q  = question.lower().strip().replace('?', '')

    if clean_q in doc_text:
        return "High"

    stop_words = {"what", "is", "the", "my", "a", "an", "does", "do", "how", "much",
                  "many", "can", "i", "in", "for", "of", "to", "and", "or", "are", "this"}
    q_keywords = set(re.findall(r'\w+', clean_q)) - stop_words

    if not q_keywords:
        return "Low"

    ratio = sum(1 for kw in q_keywords if kw in doc_text) / len(q_keywords)
    return "High" if ratio >= 0.8 else "Medium" if ratio >= 0.4 else "Low"


def _build_source_info(result) -> dict:
    """Build a structured source info dict from a Qdrant search result."""
    payload = result.payload
    text    = str(payload.get("text", ""))[:200].replace("\n", " ").strip()
    section = _extract_section_info(payload.get("text", ""))
    page    = f"Page {payload.get('page', 0) + 1}"
    return {
        "text":           text,
        "section":        section,
        "page":           page,
        "insurance_type": payload.get("insurance_type", "general"),
        "source":         payload.get("source", ""),
    }


def _format_extractive_answer(question: str, results: list) -> str:
    """Produce a concise, well-formatted answer from retrieved chunks."""
    if not results:
        return (
            "⚠️ **Service temporarily unavailable**\n\n"
            "All AI providers are currently rate limited. "
            "Please try again in a minute."
        )

    content   = results[0].payload.get("text", "").strip()
    sentences = re.split(r'(?<=[.!?])\s+', content)

    stop_words = {"what", "is", "the", "my", "a", "an", "does", "do", "how", "much",
                  "many", "can", "i", "in", "for", "of", "to", "and", "or", "are", "this"}
    q_words = set(re.findall(r'\w+', question.lower())) - stop_words

    scored: list[tuple[float, str]] = []
    for s in sentences:
        score = sum(1.0 for w in q_words if w in s.lower())
        if re.search(r'\d+', s):
            score += 0.5
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    best = [s for sc, s in scored[:2] if sc > 0]

    if not best:
        answer = sentences[0] if sentences else content[:200]
    else:
        best.sort(key=lambda s: content.find(s))
        answer = " ".join(best)

    for val in _extract_key_values(answer):
        answer = answer.replace(val, f"**{val}**")

    answer = re.sub(r'\s+', ' ', answer).strip()
    answer = re.sub(r'═+', '', answer).strip()
    if answer and answer[0].islower():
        answer = answer[0].upper() + answer[1:]
    if len(answer) > 250:
        answer = answer[:247] + "..."

    return (
        "⚠️ **AI providers are busy — showing best match from documents:**\n\n"
        f"{answer}\n\n"
        "_This is an automated extract. Try again for a full AI answer._"
    )


# ── Main query entry point ────────────────────────────────────────────

def query_rag(question: str, insurance_type: str | None = None) -> dict:
    """
    RAG query with optional insurance_type filtering.
    Returns answer, sources, confidence, degraded.
    """
    client = get_qdrant()
    if client is None:
        return {
            "answer": (
                "⚠️ **Vector database unavailable**\n\n"
                "Qdrant is not running. Start it with:\n"
                "`docker run -d -p 6333:6333 qdrant/qdrant`\n\n"
                "Then restart the backend server."
            ),
            "sources": [],
            "confidence": "Low",
            "degraded": True,
        }

    # Check if collection has any documents
    count = client.count(collection_name=QDRANT_COLLECTION).count
    if count == 0:
        return {
            "answer": "⚠️ Please upload a policy document first.",
            "sources": [],
            "confidence": "Low",
            "degraded": False,
        }

    results = _retrieve(question, insurance_type)

    if not results:
        return {
            "answer": "⚠️ No relevant documents found for your query.",
            "sources": [],
            "confidence": "Low",
            "degraded": False,
        }

    sources    = [_build_source_info(r) for r in results]
    confidence = _calculate_confidence(question, results)
    context    = "\n\n".join([r.payload.get("text", "") for r in results])

    answer   = _try_llm_chain(context, question)
    degraded = False

    if answer is None:
        answer   = _format_extractive_answer(question, results)
        degraded = True

    return {
        "answer":     answer,
        "sources":    sources,
        "confidence": confidence,
        "degraded":   degraded,
    }
