"""
Policy Engine — Phase 3 Security Architecture

Enforces security policies for all LLM interactions.
Determines what operations are allowed based on role, data sensitivity, and context.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PolicyRule:
    """A single security policy rule."""
    name: str
    description: str
    enabled: bool = True
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    action: str = "block"  # block, warn, log_only

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description,
                "enabled": self.enabled, "severity": self.severity,
                "action": self.action}


class PolicyEngine:
    """
    Security policy engine for LLM interactions.

    Enforces:
    - What data can be sent to LLMs
    - What operations are allowed per role
    - PHI handling requirements
    - Output restrictions
    - Audit requirements
    """

    DEFAULT_POLICIES = {
        "phi_never_to_llm": PolicyRule(
            name="PHI Never to LLM",
            description="Protected health information must never be sent to external LLMs without redaction",
            severity="CRITICAL",
            action="block",
        ),
        "require_injection_check": PolicyRule(
            name="Require Injection Check",
            description="All prompts must be scanned for injection attacks before sending",
            severity="HIGH",
            action="block",
        ),
        "require_output_filter": PolicyRule(
            name="Require Output Filter",
            description="All LLM outputs must be filtered for PHI leaks",
            severity="HIGH",
            action="block",
        ),
        "max_prompt_size": PolicyRule(
            name="Max Prompt Size",
            description="Prompts must not exceed maximum size limit",
            severity="MEDIUM",
            action="block",
        ),
        "require_audit_logging": PolicyRule(
            name="Require Audit Logging",
            description="All LLM interactions must be logged for audit",
            severity="HIGH",
            action="block",
        ),
        "restrict_phi_storage": PolicyRule(
            name="Restrict PHI Storage",
            description="PHI must not be stored in plaintext",
            severity="CRITICAL",
            action="block",
        ),
        "require_role_isolation": PolicyRule(
            name="Require Role Isolation",
            description="Users must only access data permitted by their role",
            severity="HIGH",
            action="block",
        ),
        "log_failed_access": PolicyRule(
            name="Log Failed Access",
            description="All failed access attempts must be logged",
            severity="MEDIUM",
            action="log_only",
        ),
        "encrypt_at_rest": PolicyRule(
            name="Encrypt at Rest",
            description="All stored PHI must be encrypted",
            severity="CRITICAL",
            action="block",
        ),
        "minimal_data_principle": PolicyRule(
            name="Minimal Data Principle",
            description="Only send minimal necessary data to LLMs",
            severity="HIGH",
            action="warn",
        ),
    }

    def __init__(self, policies: Optional[Dict[str, PolicyRule]] = None,
                 strict_mode: bool = True):
        self.policies = policies or dict(self.DEFAULT_POLICIES)
        self.strict_mode = strict_mode

    def check_policy(self, policy_name: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Check if an operation violates a specific policy.

        Args:
            policy_name: Name of the policy to check.
            context: Optional context for the check.

        Returns:
            Tuple of (allowed, message).
        """
        policy = self.policies.get(policy_name)
        if not policy:
            return (True, f"Unknown policy '{policy_name}' — allowed by default")

        if not policy.enabled:
            return (True, f"Policy '{policy.name}' is disabled")

        if policy.action == "log_only":
            return (True, f"Policy '{policy.name}' — logged only")

        if policy.action == "warn":
            return (True, f"Policy '{policy.name}' — warning")

        return (False, f"Blocked by policy: {policy.name} — {policy.description}")

    def check_batch(self, checks: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, bool, str]]:
        """
        Check multiple policies at once.

        Args:
            checks: List of (policy_name, context) tuples.

        Returns:
            List of (policy_name, allowed, message) tuples.
        """
        results = []
        for policy_name, context in checks:
            allowed, message = self.check_policy(policy_name, context)
            results.append((policy_name, allowed, message))
        return results

    def allow_llm_interaction(self, prompt: str, role: str,
                              has_phi: bool = False) -> Tuple[bool, List[str]]:
        """
        Check if an LLM interaction is allowed.

        Args:
            prompt: The prompt text.
            role: The role making the request.
            has_phi: Whether the prompt contains PHI.

        Returns:
            Tuple of (allowed, list of violation messages).
        """
        violations = []

        # Check PHI policy
        if has_phi:
            allowed, msg = self.check_policy("phi_never_to_llm")
            if not allowed:
                violations.append(msg)

        # Check role-based restrictions
        if role == "readonly_user":
            violations.append("Read-only users cannot send prompts to LLM")

        return (len(violations) == 0, violations)

    def get_enabled_policies(self) -> List[PolicyRule]:
        """Get all enabled policies."""
        return [p for p in self.policies.values() if p.enabled]

    def get_critical_policies(self) -> List[PolicyRule]:
        """Get all CRITICAL severity policies."""
        return [p for p in self.policies.values() if p.severity == "CRITICAL" and p.enabled]

    def enable_policy(self, policy_name: str) -> bool:
        """Enable a policy by name."""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = True
            return True
        return False

    def disable_policy(self, policy_name: str) -> bool:
        """Disable a policy by name."""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = False
            return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get policy engine summary."""
        total = len(self.policies)
        enabled = len(self.get_enabled_policies())
        critical = len(self.get_critical_policies())
        return {
            "total_policies": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "critical": critical,
            "strict_mode": self.strict_mode,
        }
