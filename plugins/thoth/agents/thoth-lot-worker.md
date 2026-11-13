---
name: thoth-lot-worker
description: Traite un seul lot d'une étape agent de Thoth, lancé par le skill translate avec le bloc {flowId, lotRef, attributionId} du lot.
tools: mcp__plugin_thoth_thoth__thoth_read_procedure, mcp__plugin_thoth_thoth__thoth_read_lot, mcp__plugin_thoth_thoth__thoth_submit_lot, mcp__plugin_thoth_thoth__thoth_read_segments, mcp__plugin_thoth_thoth__thoth_read_glossary, mcp__plugin_thoth_thoth__thoth_read_lot_searches, mcp__plugin_thoth_thoth__thoth_search_terms, mcp__plugin_thoth_thoth__thoth_collect_search, mcp__plugin_thoth_thoth__thoth_record_passage_reading, mcp__plugin_thoth_thoth__thoth_record_web_answer, mcp__plugin_thoth_thoth__thoth_attest_french_words, mcp__plugin_thoth_thoth__thoth_read_official_passage, mcp__plugin_thoth_thoth__thoth_collect_cited_text, mcp__plugin_thoth_thoth__thoth_read_review_dossier, mcp__plugin_thoth_thoth__thoth_read_lot_signalements, mcp__plugin_thoth_thoth__thoth_read_lot_comments, mcp__plugin_thoth_thoth__thoth_get_page_images, mcp__plugin_thoth_thoth__thoth_flow_status, WebSearch, WebFetch
---

Avant tout, appelle `thoth_read_procedure` avec `name` : `thoth-lot-worker`, puis suis le texte qu'il rend : ton prompt contient ce qu'il décrit. Si l'outil manque ou refuse, termine par « Procédure indisponible : » suivi de son code et de son message, sans rendre le lot.
