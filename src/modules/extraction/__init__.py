"""Extraction — correction candidates from Claude Code session transcripts.

See MODULE.md for the contract and ADR-0002 for the boundary decision: this module only
reads transcripts, scores human turns by keyword weighting, and renders a candidate list
for human and AI triage. It never writes to the transcripts or the vault.
"""
