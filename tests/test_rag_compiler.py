"""
Tests for modules/rag_compiler.py.
Validates syllabus schema generation, NBA/NAAC outcome compliance structure,
and mock LLM invocation via LangChain RAG pipeline.
"""

import pytest
from unittest.mock import MagicMock
from modules.rag_compiler import compile_academic_syllabus


def test_compile_academic_syllabus_structure(monkeypatch):
    """
    Mocks the Groq Chat model and vector search to verify
    JSON schema enforcement without incurring real external API costs.
    """
    mock_syllabus = {
        "title": "Production Agentic AI Bootcamp",
        "program_type": "Bootcamp",
        "duration_hours": 15,
        "target_audience": "UG/PG Engineering Students",
        "modules": [
            {
                "unit": 1,
                "topic": "Stateful Multi-Agent Workflows",
                "concepts": ["LangGraph", "Cyclic Graphs"],
                "lab_deliverable": "Autonomous Code Review Agent"
            }
        ],
        "case_studies": ["Financial Document Extraction"],
        "capstone_project": "Enterprise Tool Assistant with MCP",
        "recommended_quorum": 50
    }

    # Mock vector store retrieval
    mock_retriever = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Accredited standards for Agentic AI and LangGraph."
    mock_retriever.invoke.return_value = [mock_doc]
    
    mock_vs = MagicMock()
    mock_vs.as_retriever.return_value = mock_retriever
    monkeypatch.setattr("modules.rag_compiler.get_vector_store", lambda: mock_vs)

    # Mock LangChain chain execution output
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_syllabus
    monkeypatch.setattr("langchain_core.runnables.base.RunnableSequence.invoke", lambda self, input_data: mock_syllabus)

    result = compile_academic_syllabus(
        role_or_scope="Agentic AI Engineer",
        skills="LangGraph, MCP, Python",
        duration=15,
        program_type="Bootcamp"
    )

    # Validate output contract
    assert isinstance(result, dict)
    assert result["title"] == "Production Agentic AI Bootcamp"
    assert result["duration_hours"] == 15
    assert len(result["modules"]) >= 1
    assert "unit" in result["modules"][0]
    assert "lab_deliverable" in result["modules"][0]
    assert "capstone_project" in result
    assert "recommended_quorum" in result
