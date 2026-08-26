"""
Tests for modules/cluster_engine.py.
Validates student demand aggregation, clustering grouping logic,
average budget calculation, and quorum launch threshold gates.
"""

import pytest
import sqlite3
from config.database import init_db
from modules.auth import register_user
from modules.cluster_engine import cluster_and_evaluate_quorum, mark_demands_as_locked


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up an isolated in-memory database with registered students."""
    test_db = ":memory:"
    conn = sqlite3.connect(test_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Patch database schema & connection everywhere
    monkeypatch.setattr("modules.cluster_engine.get_connection", lambda: conn)
    monkeypatch.setattr("modules.auth.get_connection", lambda: conn)
    monkeypatch.setattr("config.database.get_connection", lambda: conn)
    
    init_db(test_db)
    
    # Seed 5 test students
    for i in range(1, 6):
        register_user(f"stu_{i}", "pass123", f"Student {i}", "student")
        
    yield conn
    conn.close()


def test_cluster_below_quorum_returns_empty(setup_test_db):
    conn = setup_test_db
    cursor = conn.cursor()
    
    # Insert 2 requests for Agentic AI (Quorum = 3)
    cursor.execute("""
        INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
        VALUES (1, 'Agentic AI Engineer', 'LangGraph, MCP', 15, 250.0, 'PENDING'),
               (2, 'Agentic AI Engineer', 'LangChain, Tools', 15, 300.0, 'PENDING')
    """)
    conn.commit()
    
    unlocked = cluster_and_evaluate_quorum(min_quorum=3)
    assert len(unlocked) == 0


def test_cluster_reaching_quorum_unlocks_program(setup_test_db):
    conn = setup_test_db
    cursor = conn.cursor()
    
    # Insert 3 matching requests for Agentic AI 15h
    cursor.execute("""
        INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
        VALUES (1, 'Agentic AI Engineer', 'LangGraph, MCP', 15, 200.0, 'PENDING'),
               (2, 'Agentic AI Engineer', 'LangGraph, Python', 15, 250.0, 'PENDING'),
               (3, 'Agentic AI Engineer', 'Multi-Agent, MCP', 15, 300.0, 'PENDING')
    """)
    conn.commit()
    
    unlocked = cluster_and_evaluate_quorum(min_quorum=3)
    
    assert len(unlocked) == 1
    prog = unlocked[0]
    assert prog["role"] == "Agentic AI Engineer"
    assert prog["duration"] == 15
    assert prog["enrolled_count"] == 3
    assert prog["budget"] == 250.0  # (200 + 250 + 300) / 3
    assert "LangGraph" in prog["skills"]
    assert "MCP" in prog["skills"]


def test_mark_demands_as_locked(setup_test_db):
    conn = setup_test_db
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO student_demands (student_id, dream_job_role, target_skills, duration_hours, budget_inr, status)
        VALUES (1, 'RAG Engineer', 'FAISS', 10, 200.0, 'PENDING'),
               (2, 'RAG Engineer', 'LlamaIndex', 10, 200.0, 'PENDING')
    """)
    conn.commit()
    
    mark_demands_as_locked([1, 2], "cluster_rag_10h")
    
    cursor.execute("SELECT status, cluster_id FROM student_demands WHERE id IN (1, 2)")
    rows = cursor.fetchall()
    for row in rows:
        assert row["status"] == "LOCKED"
        assert row["cluster_id"] == "cluster_rag_10h"
