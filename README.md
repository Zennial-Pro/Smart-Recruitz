# Smart Recruitz - AI Interview Validation Pipeline
## Overview
The Smart Recruitz automated interview validation pipeline evaluates candidate interview transcripts in real-time. It leverages an orchestrated AI state machine to analyze responses against structured rubrics, outputting standard readiness scores and talent pool decisions.
## Architecture Structure
The project was built incrementally following a structured, scalable approach:
### Day 1: Foundational Models & Enums
- Established strict Pydantic schemas representing the domain (Candidates, Interviews).
- Defined core enums for system states (`ReadinessLevel`, `TalentPoolAction`).
### Day 2: The Core LangGraph Architecture
- Designed the `InterviewValidationState` to serve as the single source of truth for the pipeline payload.
- Built the foundational workflow structure (`workflow.py`).
### Day 3: AI Node Implementations
- Implemented the actual AI scoring node using Anthropic's Claude 3.5 Sonnet.
- Developed business logic gateways (`compute_score.py`, `talent_pool_gate.py`).
- Completed a mocked E2E integration test suite for local verification without API costs.
## Local Development Setup
### 1. Environment
Ensure you have the `smartrecruitz` conda environment active.
```bash
conda activate smartrecruitz
```
### 2. Testing
Test the core LangGraph logic using the mock AI adapter:
```bash
python Day3/test_integration.py
```