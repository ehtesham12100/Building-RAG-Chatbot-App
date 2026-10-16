import os
from typing import List, Dict, Any, Optional
from app.config import settings

class LLMService:
    def __init__(self):
        pass

    def _get_gemini_client(self, api_key: Optional[str] = None):
        from google import genai
        key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if not key:
            raise ValueError(
                "Gemini API Key is missing! Please provide it in your .env file, "
                "set GEMINI_API_KEY environment variable, or pass it in the request."
            )
        return genai.Client(api_key=key)

    def _get_groq_client(self, api_key: Optional[str] = None):
        from groq import Groq
        key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        if not key:
            raise ValueError(
                "Groq API Key is missing! Please provide it in your .env file, "
                "set GROQ_API_KEY environment variable, or pass it in the request."
            )
        return Groq(api_key=key)

    def generate_rag_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded response using modern Google GenAI SDK or Groq based on context chunks and chat history.
        """
        selected_provider = (provider or settings.DEFAULT_LLM_PROVIDER).lower()

        # Build context string with explicit citations
        context_blocks = []
        for i, chunk in enumerate(context_chunks):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("document_title", "Document")
            page_num = meta.get("page_number", "Unknown")
            context_blocks.append(
                f"[Source {i+1} | Document: {doc_name} | Page: {page_num}]\n{chunk.get('text', '')}"
            )

        context_str = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant document chunks found."

        system_instruction = (
            "You are an expert document analysis assistant and RAG chatbot. "
            "Your task is to answer the user's questions accurately and concisely based ONLY on the provided document excerpts.\n\n"
            "Guidelines:\n"
            "1. Answer strictly based on the provided sources. Do not hallucinate facts.\n"
            "2. Whenever you state a claim or fact, cite the source in brackets, e.g., '[Document Name, Page X]'.\n"
            "3. If the answer cannot be found in the provided excerpts, clearly state that the provided documents do not contain enough information to answer the question, but summarize any partially related details if available.\n"
            "4. Format your answer nicely using Markdown (bullet points, bold text, code blocks where appropriate)."
        )

        if selected_provider == "gemini":
            try:
                from google.genai import types
                client = self._get_gemini_client(api_key)

                # Prioritize gemini-3.8-flash, then fallback to gemini-2.5-flash / gemini-1.5-flash
                candidate_models = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                if settings.GEMINI_MODEL and settings.GEMINI_MODEL not in candidate_models:
                    candidate_models.insert(0, settings.GEMINI_MODEL)

                # Format chat history
                contents = []
                if chat_history:
                    for msg in chat_history[-6:]:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append(types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=msg.get("content", ""))]
                        ))

                user_prompt = f"Retrieved Document Context:\n{context_str}\n\nUser Question:\n{query}"
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)]
                ))

                gen_config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=2048,
                )

                last_error = None
                for model_candidate in candidate_models:
                    try:
                        response = client.models.generate_content(
                            model=model_candidate,
                            contents=contents,
                            config=gen_config
                        )
                        return {
                            "answer": response.text,
                            "model_used": model_candidate,
                            "provider": "gemini"
                        }
                    except Exception as err:
                        last_error = err
                        err_str = str(err).lower()
                        # If 404 or model not found / retired, try next candidate
                        if "404" in err_str or "not found" in err_str or "not available" in err_str:
                            continue
                        else:
                            raise err

                if last_error:
                    raise last_error

            except Exception as e:
                # If Gemini fails and Groq key is present, fallback gracefully
                groq_key = os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
                if groq_key and selected_provider != "groq":
                    print(f"Gemini error: {e}. Falling back to Groq...")
                    selected_provider = "groq"
                else:
                    raise e

        if selected_provider == "groq":
            groq_client = self._get_groq_client(api_key)
            model_name = settings.GROQ_MODEL

            messages = [{"role": "system", "content": system_instruction}]

            if chat_history:
                for msg in chat_history[-6:]:
                    messages.append({
                        "role": "user" if msg.get("role") == "user" else "assistant",
                        "content": msg.get("content", "")
                    })

            messages.append({
                "role": "user",
                "content": f"Document Context:\n{context_str}\n\nQuestion: {query}"
            })

            completion = groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=2048
            )

            return {
                "answer": completion.choices[0].message.content,
                "model_used": model_name,
                "provider": "groq"
            }

        raise ValueError(f"Unsupported LLM provider: {selected_provider}")

llm_service = LLMService()
