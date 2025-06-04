#!/usr/bin/env python3
"""
Convert egglog rewrite rules and rules to LaTeX inference rule representations.

This module parses egglog rewrite rules and regular rules, converting them to
LaTeX-formatted inference rules for mathematical display.

Usage:
    from egglog_to_inference import to_latex
    latex = to_latex(egglog_rule_string)
"""

import re
from typing import Tuple, List, Optional


def clean_expression(expr: str) -> str:
    """Clean and format an expression for LaTeX display."""
    expr = expr.strip()

    def format_identifier(word: str) -> str:
        """Format a single identifier for LaTeX."""
        if word.isdigit() or (len(word) == 1 and word.isalpha()):
            return word
        formatted = word.replace('_', '\\_')
        return f"\\text{{{formatted}}}"

    def parse_expression(text: str) -> str:
        """Parse and format expressions recursively."""
        text = text.strip()

        # If no parentheses, just format identifiers
        if not text.startswith('('):
            words = text.split()
            return ' '.join(format_identifier(word) for word in words)

        # Remove outer parentheses and parse content
        inner = text[1:-1].strip()
        parts = []
        current = ""
        depth = 0

        for char in inner:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ' ' and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                    current = ""
                continue
            current += char

        if current.strip():
            parts.append(current.strip())

        if not parts:
            return ""

        # Format as function call
        func_name = format_identifier(parts[0])
        if len(parts) == 1:
            return f"({func_name})"

        # Format arguments recursively
        formatted_args = [parse_expression(arg) for arg in parts[1:]]
        return f"{func_name}({', '.join(formatted_args)})"

    # Check if this is a function call
    if expr.startswith('(') and expr.endswith(')'):
        inner = expr[1:-1]
        parts = inner.split()
        if len(parts) > 1 and parts[0].replace('_', '').replace('-', '').isalnum():
            # This is a function call, parse it
            return parse_expression(expr)
        else:
            # Not a function call, remove outer parentheses
            expr = inner

    return parse_expression(expr)


def extract_balanced_content(text: str, start: int = 0) -> Tuple[Optional[str], int]:
    """Extract balanced parentheses content starting from position."""
    while start < len(text) and text[start] != '(':
        start += 1

    if start >= len(text):
        return None, start

    paren_count = 0
    content_start = start + 1

    for i in range(start, len(text)):
        if text[i] == '(':
            paren_count += 1
        elif text[i] == ')':
            paren_count -= 1
            if paren_count == 0:
                return text[content_start:i].strip(), i + 1

    return None, start


def parse_rule(rule_text: str) -> Tuple[List[str], List[str]]:
    """Parse an egglog rule into conditions and conclusions."""
    rule_text = rule_text.strip()
    if rule_text.startswith('(rule'):
        rule_text = rule_text[5:].strip()
    if rule_text.endswith(')'):
        rule_text = rule_text[:-1].strip()

    # Extract conditions (first parentheses group)
    conditions_content, pos = extract_balanced_content(rule_text, 0)
    conclusions_content, _ = extract_balanced_content(rule_text, pos)

    def parse_sexp_list(content: str) -> List[str]:
        """Parse multiple s-expressions."""
        if not content:
            return []

        expressions = []
        pos = 0

        while pos < len(content):
            while pos < len(content) and content[pos].isspace():
                pos += 1
            if pos >= len(content):
                break

            if content[pos] == '(':
                expr_content, new_pos = extract_balanced_content(content, pos)
                if expr_content is not None:
                    expressions.append(f"({expr_content})")
                    pos = new_pos
                else:
                    pos += 1
            else:
                start = pos
                while pos < len(content) and not content[pos].isspace() and content[pos] not in '()':
                    pos += 1
                if pos > start:
                    expressions.append(content[start:pos])

        return expressions

    conditions = parse_sexp_list(conditions_content or "")
    conclusions = parse_sexp_list(conclusions_content or "")

    return conditions, conclusions


def parse_rewrite(rule_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse an egglog rewrite rule into LHS and RHS."""
    rule_text = rule_text.strip()

    # Handle direct egglog format: (rewrite lhs rhs ...)
    if rule_text.startswith('(rewrite'):
        content = rule_text[8:].strip()
        if content.endswith(')'):
            content = content[:-1].strip()

        lhs, pos = extract_balanced_content(content, 0)
        rhs, _ = extract_balanced_content(content, pos)

        if lhs and rhs:
            return f"({lhs})", f"({rhs})"

    return None, None


def format_multiline(items: List[str]) -> str:
    """Format multiple items with array environment if needed."""
    if len(items) > 1:
        content = ' \\\\ '.join(items)
        return f"\\begin{{array}}{{l}} {content} \\end{{array}}"
    elif len(items) == 1:
        return items[0]
    else:
        return "\\text{true}"


def clean_equation(expr: str) -> str:
    """Clean equation expressions, handling (= lhs rhs) format."""
    expr = expr.strip()

    if expr.startswith('(= '):
        content = expr[3:]
        if content.endswith(')'):
            content = content[:-1]

        # Split into lhs and rhs
        parts = []
        current = ""
        paren_count = 0

        for char in content:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ' ' and paren_count == 0 and current:
                parts.append(current)
                current = ""
                continue
            current += char

        if current:
            parts.append(current)

        if len(parts) >= 2:
            lhs = clean_expression(parts[0])
            rhs = clean_expression(' '.join(parts[1:]))
            return f"{lhs} = {rhs}"

    return clean_expression(expr)


def to_latex(egglog_rule: str) -> str:
    """
    Convert egglog rule(s) to LaTeX inference rule format.

    Args:
        egglog_rule: The egglog rule string or multiple rules

    Returns:
        LaTeX-formatted inference rule(s)
    """
    egglog_rule = egglog_rule.strip()

    # Handle multiple rules
    total_rules = egglog_rule.count('(rule') + egglog_rule.count('(rewrite')
    if total_rules > 1:
        # Extract and convert all rules
        rules = []
        pos = 0
        text = egglog_rule

        while pos < len(text):
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text):
                break

            if text[pos:pos+6] == '(rule ' or text[pos:pos+9] == '(rewrite ':
                paren_count = 0
                start = pos

                while pos < len(text):
                    if text[pos] == '(':
                        paren_count += 1
                    elif text[pos] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            rules.append(text[start:pos+1])
                            pos += 1
                            break
                    pos += 1
            else:
                pos += 1

        if rules:
            latex_rules = []
            for i, rule in enumerate(rules, 1):
                converted = to_latex(rule)
                latex_rules.append(f"% Rule {i}\n{converted}")
            return '\n\n'.join(latex_rules)

    # Handle single rule
    if egglog_rule.startswith('(rewrite'):
        # Rewrite rule
        lhs_expr, rhs_expr = parse_rewrite(egglog_rule)
        if not lhs_expr or not rhs_expr:
            return "Error: Could not parse rewrite rule"

        lhs_clean = clean_expression(lhs_expr)
        rhs_clean = clean_expression(rhs_expr)

        numerator = f"expr = {lhs_clean}"
        denominator = f"expr \\to {rhs_clean}"
        return f"\\frac{{{numerator}}}{{{denominator}}}"

    elif egglog_rule.startswith('(rule'):
        # Regular rule
        conditions, conclusions = parse_rule(egglog_rule)

        if not conditions and not conclusions:
            return "Error: Could not parse rule"

        # Format conditions
        condition_strs = [clean_equation(cond) for cond in conditions]
        numerator = format_multiline(condition_strs)

        # Format conclusions
        conclusion_strs = [clean_expression(concl) for concl in conclusions]
        denominator = format_multiline(conclusion_strs)

        return f"\\frac{{{numerator}}}{{{denominator}}}"

    else:
        return "Error: Unrecognized rule format"
