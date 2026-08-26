"""
LangChain RAG Syllabus Compiler powered by Groq LLMs and FAISS.
Uses centralized config.settings driven by st.secrets.
"""

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config.settings import settings


def get_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_dir = settings.FAISS_INDEX_PATH

    if os.path.exists(vector_dir):
        return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True)

    # Seed baseline pedagogical reference corpus
    seeds = [
        Document(
            page_content="NBA and NAAC accredited FDPs require continuous assessment, hands-on lab mapping, and Outcome-Based Education (OBE) metrics.",
            metadata={"type": "academic_compliance"},
        ),
        Document(
            page_content="Agentic AI curricula should cover LangChain, LangGraph state machines, Model Context Protocol (MCP), and Multi-Agent consensus.",
            metadata={"type": "tech_standard"},
        ),
        Document(
            page_content="VLSI and TinyML engineering tracks cover RISC-V RTL simulation, Verilog testbenches, and microcontroller quantization.",
            metadata={"type": "tech_standard"},
        ),
        Document(
            page_content="Production RAG involves dense retrieval, BM25 hybrid search, cross-encoders, and vector indices like FAISS.",
            metadata={"type": "tech_standard"},
        ),
    ]
    vs = FAISS.from_documents(seeds, embeddings)
    os.makedirs(os.path.dirname(os.path.abspath(vector_dir)), exist_ok=True)
    vs.save_local(vector_dir)
    return vs


def compile_academic_syllabus(
    role_or_scope: str, skills: str, duration: int, program_type: str = "Bootcamp"
) -> dict:
    vs = get_vector_store()
    retrieved = vs.as_retriever(search_kwargs={"k": 2}).invoke(f"{role_or_scope} {skills}")
    grounding_context = "\n".join([doc.page_content for doc in retrieved])

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.1,
    )

    system_prompt = """
    You are the PragyanAI Academic Program Compiler.
    Convert inputs into a validated syllabus matching NBA/NAAC and industry rigor.
    Output ONLY valid JSON matching this schema:
    {{
        "title": "Course Name",
        "program_type": "{program_type}",
        "duration_hours": {duration},
        "target_audience": "Audience description",
        "modules": [
            {{"unit": 1, "topic": "Name", "concepts": ["C1", "C2"], "lab_deliverable": "Lab 1"}}
        ],
        "case_studies": ["Case 1", "Case 2"],
        "capstone_project": "Project title & overview",
        "recommended_quorum": 50
    }}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "user",
            "Requirement: {role_or_scope}\nSkills: {skills}\nDuration: {duration} Hours\nStandards:\n{grounding_context}",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()
    return chain.invoke({
        "role_or_scope": role_or_scope,
        "skills": skills,
        "duration": duration,
        "program_type": program_type,
        "grounding_context": grounding_context,
    })
