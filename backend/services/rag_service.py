import os
import re
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader # pyre-ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter # pyre-ignore
from langchain_huggingface import HuggingFaceEmbeddings # pyre-ignore
from langchain_community.vectorstores import FAISS # pyre-ignore

from backend.config import ( # pyre-ignore
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    LLM_PROVIDER,
    VECTOR_STORE_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    CHAT_MODEL_OPENAI,
    CHAT_MODEL_GEMINI,
    RETRIEVER_K,
)

logger = logging.getLogger(__name__)

# Set API keys in environment for LangChain
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ── Globals & Prompts ────────────────────────────────────────────────
_embeddings = None
_vector_store: FAISS | None = None

DEFAULT_RAG_PROMPT = """You are an expert insurance policy assistant. Answer the user's question using ONLY the provided policy excerpts.

RULES:
1. Start with a direct "🧠 **AI Answer:**" section. Be highly concise.
2. If asking for specific details (like name, number, date), use structured fields (e.g., Policy Name: X).
3. **Bold** key numbers, amounts, and limits.
4. Keep the answer under visually 2 lines. Do NOT write paragraphs.
5. If unsure, state that the information is missing from the provided documents.

Context:
{context}

Question: {question}

Answer:"""

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
        
        # Fallback to a dummy embedding if all else fails (to allow server to start)
        logger.warning("No embeddings available. Using mock embeddings.")
        _embeddings = MockEmbeddings()
        return _embeddings


_llm_chain: list = []


def _build_llm_chain() -> list:
    """Build an ordered list of available LLMs — Gemini first, OpenAI second."""
    global _llm_chain
    if _llm_chain:
        return _llm_chain

    llms = []

    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI # pyre-ignore
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
            from langchain_openai import ChatOpenAI # pyre-ignore
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
    from langchain_core.prompts import PromptTemplate # pyre-ignore
    from langchain_core.output_parsers import StrOutputParser # pyre-ignore

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
                continue   # try next LLM
            else:
                logger.warning("%s failed (%s) — trying next provider", name, str(e)[:80])
                continue

    logger.warning("All LLM providers failed — falling back to extractive QA")
    return None  # triggers extractive fallback


def _store_path() -> str:
    return os.path.abspath(VECTOR_STORE_PATH)


def get_vector_store() -> FAISS | None:
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    index_dir = _store_path()
    index_file = os.path.join(index_dir, "index.faiss")
    if os.path.exists(index_file):
        logger.info("Loading existing FAISS index from %s", index_dir)
        _vector_store = FAISS.load_local(
            index_dir, get_embeddings(), allow_dangerous_deserialization=True
        )
    return _vector_store


def ingest_file(file_path: str) -> int:
    global _vector_store

    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
    elif ext in (".txt", ".md"):
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        logger.warning("No chunks produced from %s", file_path)
        return 0

    if _vector_store is None:
        _vector_store = FAISS.from_documents(chunks, get_embeddings())
    else:
        _vector_store.add_documents(chunks)

    store_dir = _store_path()
    os.makedirs(store_dir, exist_ok=True)
    _vector_store.save_local(store_dir)
    logger.info("Ingested %d chunks from %s", len(chunks), file_path)

    return len(chunks)


# ── Answer Formatting Helpers ────────────────────────────────────────


def _extract_section_info(text: str) -> str:
    """Try to extract a section/heading reference from a chunk of text."""
    # Match patterns like "Section 2", "2.1 Inpatient", "SECTION 3 – COVERAGE"
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
    # Money amounts like $10,000 or ₹5,00,000
    money = re.findall(r'[\$₹]\s?[\d,]+(?:\.\d+)?', text)
    highlights.extend(money)
    # Percentages
    pcts = re.findall(r'\d+(?:\.\d+)?%', text)
    highlights.extend(pcts)
    # Durations like "180 days", "30 days", "12 months"
    durations = re.findall(r'\d+\s+(?:days?|months?|years?|hours?)', text, re.IGNORECASE)
    highlights.extend(durations)
    return list(set(highlights))


def _calculate_confidence(question: str, docs: list, scores: list[float] | None = None) -> str:
    """Estimate answer confidence based on exact/partial matches in retrieval."""
    if not docs:
        return "Low"
    
    # Clean question
    clean_q = question.lower().strip().replace('?', '')
    doc_text = docs[0].page_content.lower()
    
    # Exact phrase match gives immediate high confidence
    if clean_q in doc_text:
        return "High"

    q_words = set(re.findall(r'\w+', clean_q))
    stop_words = {"what", "is", "the", "my", "a", "an", "does", "do", "how", "much", 
                  "many", "can", "i", "in", "for", "of", "to", "and", "or", "are", "this"}
    q_keywords = q_words - stop_words

    if not q_keywords:
        return "Low"

    match_count = sum(1 for kw in q_keywords if kw in doc_text)
    ratio = match_count / len(q_keywords)

    if ratio >= 0.8:
        return "High"
    elif ratio >= 0.4:
        return "Medium"
    else:
        return "Low"


def _build_source_info(doc) -> dict:
    """Build a structured source info dict from a document."""
    text = str(doc.page_content[:200]).replace("\n", " ").strip()
    section = _extract_section_info(doc.page_content)

    # Try to get page number from metadata
    page = ""
    if hasattr(doc, "metadata"):
        if "page" in doc.metadata:
            page = f"Page {doc.metadata['page'] + 1}"
        elif "source" in doc.metadata:
            source_file = Path(doc.metadata["source"]).stem
            page = source_file.replace("_", " ").title()

    return {"text": text, "section": section, "page": page}


def _format_extractive_answer(question: str, docs: list) -> str:
    """Produce a concise, well-formatted answer from retrieved chunks."""
    if not docs:
        return (
            "⚠️ **Service temporarily unavailable**\n\n"
            "All AI providers are currently rate limited. "
            "Please try again in a minute."
        )

    primary_doc = docs[0]
    content = primary_doc.page_content.strip()
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    q_lower_set = set(re.findall(r'\w+', question.lower()))
    stop_words = {"what", "is", "the", "my", "a", "an", "does", "do", "how", "much", 
                  "many", "can", "i", "in", "for", "of", "to", "and", "or", "are", "this"}
    q_words = q_lower_set - stop_words

    # Score sentences based on keyword overlap and presence of numbers (often answers)
    scored: list[tuple[float, str]] = []
    for s in sentences:
        s_lower = s.lower()
        score = sum(1.0 for w in q_words if w in s_lower)
        # Boost sentences that contain numbers/amounts since they usually answer "how much/many"
        if re.search(r'\d+', s):
            score += 0.5
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    
    # Pick the top 1-2 sentences
    best_sentences = [s for score, s in scored[:2] if score > 0] # pyre-ignore
    
    if not best_sentences:
        answer = sentences[0] if sentences else str(content[:200]) # pyre-ignore
    else:
        # Re-order the top sentences as they appeared in the text for coherence
        best_sentences.sort(key=lambda s: content.find(s))
        answer = " ".join(best_sentences)

    # Bold key values
    key_values = _extract_key_values(answer)
    for val in key_values:
        answer = answer.replace(val, f"**{val}**")

    # Clean up formatting of the base answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    answer = re.sub(r'═+', '', answer).strip()
    
    # Capitalize first letter if needed
    if answer and answer[0].islower():
        # pyre-ignore
        answer = answer[0].upper() + answer[1:]

    # If the user asked for structured data (name, number), try to extract them as fields
    q_lower = question.lower()
    lines: list[str] = []
    if "policy name" in q_lower or "policy number" in q_lower:
         if "name" in q_lower:
             name_match = re.search(r'([A-Z\s]+POLICY)', content)
             if name_match:
                 val = re.sub(r'\s+', ' ', name_match.group(1)).strip()
                 lines.append(f"**Policy Name:** {val}")
         if "number" in q_lower:
             # Find alphanumeric sequences with dashes
             nums = re.findall(r'[A-Z]+-[A-Z]+-\d{4}-\d+', content)
             if nums:
                 lines.append(f"**Policy Number:** {nums[0]}")
         if lines:
             answer = "\n\n".join(lines)
             
    # Enforce strict maximum length (2 lines max visually)
    if not lines and len(answer) > 250:
        # pyre-ignore
        answer = str(answer[:247]) + "..."
             
    final_output = (
        "⚠️ **AI providers are busy — showing best match from documents:**\n\n"
        f"{answer}\n\n"
        "_This is an automated extract, not a full AI answer. "
        "Try again in a moment for a better response._"
    )
    return final_output


def query_rag(question: str) -> dict:
    """
    Run a RAG query: retrieve relevant chunks → format answer → return
    with structured source info and confidence.
    """
    store = get_vector_store()
    if store is None:
        return {
            "answer": "⚠️ Please upload a policy document first.",
            "sources": [],
            "confidence": "Low",
            "degraded": False,
        }

    retriever = store.as_retriever(search_kwargs={"k": RETRIEVER_K})
    source_docs = retriever.invoke(question)

    # Build structured sources
    sources = [_build_source_info(doc) for doc in source_docs]

    # Calculate confidence
    confidence = _calculate_confidence(question, source_docs)
    context = "\n\n".join([doc.page_content for doc in source_docs])

    # Try Gemini → OpenAI → extractive (automatic cascade)
    answer = _try_llm_chain(context, question)
    degraded = False

    if answer is None:
        answer = _format_extractive_answer(question, source_docs)
        degraded = True          # flag it

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "degraded": degraded,
    }
