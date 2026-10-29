"""National drought plans, emergency declarations, and response guidance.

These are the authoritative *government* documents that turn the app's
scientific drought classification (quintile Rainfall Index, PEAC 4/8-inch index,
D0–D4) into concrete national triggers and response actions.
"""

from .national_plans import NATIONAL_PLANS, fas_plans

__all__ = ["NATIONAL_PLANS", "fas_plans"]
