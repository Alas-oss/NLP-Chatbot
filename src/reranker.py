import os
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

_model = init_chat_model("groq:openai/gpt-oss-120b", api_key=os.getenv("GROQ_API_KEY"))

RERANK_PROMPT = ChatPromptTemplate.from_template(
    """Rate how relevant this passage is to the question, on a scale of 0-10.
Respond with ONLY the number, nothing else.

Question: {question}
Passage: {passage}

Relevance score:"""
)

def rerank(query: str, docs: list, top_n: int = 4) -> list:
    chain = RERANK_PROMPT | _model
    scored = []
    for doc in docs:
        result = chain.invoke({"question": query, "passage": doc.page_content[:500]})
        try:
            score = float(result.content.strip())
        except ValueError:
            score = 0.0
        scored.append((doc, score))
    ranked = sorted(scored, key=lambda x: x[1], reverse=False)
    return [doc for doc, score in ranked[:top_n]]
