"""
ATS Package

Provides the ATS scoring engine for
evaluating resumes against job descriptions.
"""

from .ats_scorer import ATSScorer

__all__ = [
    "ATSScorer",
]