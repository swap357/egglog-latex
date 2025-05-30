#!/usr/bin/env python3
"""
Convert egglog rewrite rules to LaTeX inference rule representations.

This module parses egglog rewrite rules and converts them to LaTeX-formatted
inference rules for mathematical display.

Usage:
    from egglog_to_inference import convert_rule
    latex = convert_rule(egglog_rule_string)
"""

import re
from typing import Tuple, List, Optional


def extract_balanced_expr(text: str, start_token: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract the first balanced parenthesis expression after start_token.

    Args:
        text: Input text containing the expression
        start_token: Token to search for (e.g., 'rewrite(' or '.to(')

    Returns:
        Tuple of (extracted_expression, remaining_text) or (None, None) if not found
    """
    start_idx = text.find(start_token)
    if start_idx == -1:
        return None, None

    start_idx += len(start_token)
    remaining_text = text[start_idx:]

    # For rewrite() calls, we need special handling to extract just the first expression
    if start_token == 'rewrite(':
        # Find the first expression before any comma at the rewrite() level
        paren_count = 0
        bracket_count = 0
        expr = ''

        for i, char in enumerate(remaining_text):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            elif char == ',' and paren_count == 0 and bracket_count == 0:
                # This is a comma at the top level of rewrite() - stop here
                return expr.strip(), text[start_idx + i:]

            expr += char

            # If we hit the closing paren of rewrite(), we're done
            if paren_count == -1:
                # Remove the trailing )
                expr = expr[:-1]
                return expr.strip(), text[start_idx + i:]

        # If we got here, return what we have
        if expr.strip():
            return expr.strip(), text[start_idx + len(expr):]

    # For other tokens like .to(, use the original logic
    # Look for function call pattern: function_name(args)
    # First, find the opening parenthesis
    first_paren = remaining_text.find('(')
    if first_paren != -1:
        # Extract the function name (everything before the first '(')
        func_name = remaining_text[:first_paren].strip()

        # Now extract the balanced parentheses starting from the first '('
        paren_count = 0
        expr_start = first_paren
        expr = func_name  # Start with function name

        for i, char in enumerate(remaining_text[expr_start:]):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1

            expr += char

            if paren_count == 0:
                return expr.strip(), text[start_idx + expr_start + i + 1:]

    # If no parentheses found, extract until comma, newline, or end
    simple_expr = ''
    paren_depth = 0

    for i, char in enumerate(remaining_text):
        if char == '(':
            paren_depth += 1
        elif char == ')':
            if paren_depth == 0:
                # This is the closing paren of the .to() - stop here
                break
            paren_depth -= 1
        elif char == ',' and paren_depth == 0:
            # Comma at top level - stop here
            break
        elif char == '\n' and paren_depth == 0:
            # Newline at top level - might be end of expression
            break

        simple_expr += char

    if simple_expr.strip():
        return simple_expr.strip(), text[start_idx + len(simple_expr):]

    return None, None


def extract_conditions(egglog_rule: str) -> List[str]:
    """
    Extract condition clauses from the .to() section of an egglog rule.

    Args:
        egglog_rule: The complete egglog rewrite rule

    Returns:
        List of condition strings
    """
    to_index = egglog_rule.find('.to(')
    if to_index == -1:
        return []

    after_to = egglog_rule[to_index:]
    lines = [line.strip().rstrip(',)') for line in after_to.splitlines() if line.strip()]

    conditions = []
    start_collecting = False

    for line in lines:
        if line.startswith('.to('):
            start_collecting = True
            continue

        if start_collecting and line and not line.startswith(')'):
            # Check if this line contains a condition (comparison operators)
            if any(op in line for op in ['>=', '<=', '==', '!=', '<', '>']):
                conditions.append(line)

    return conditions


def clean_expression(expr: str) -> str:
    """
    Clean and format an expression for LaTeX display.

    Args:
        expr: Raw expression string

    Returns:
        Cleaned expression string
    """
    expr = expr.strip()

    # Don't remove parentheses if this looks like a function call
    if expr.startswith('(') and expr.endswith(')'):
        inner = expr[1:-1]
        if not (any(c.isalpha() for c in inner.split('(')[0]) and '(' in inner):
            expr = inner

    # Be more selective about underscore escaping
    def escape_selective(match):
        word = match.group(0)
        # Don't escape underscores in common patterns
        if any(pattern in word.lower() for pattern in ['npy_', 'lit64', 'literalf64', 'term.', '_float', '_int']):
            return word
        # Escape other underscores
        return word.replace('_', '\\_')

    # Find words that contain underscores and apply selective escaping
    expr = re.sub(r'\b\w*_\w*\b', escape_selective, expr)

    return expr


def format_conditions_latex(conditions: List[str]) -> str:
    """
    Format conditions for LaTeX display.

    Args:
        conditions: List of condition strings

    Returns:
        LaTeX-formatted condition string
    """
    latex_conditions = []

    for cond in conditions:
        cond = cond.replace('_', '\\_')
        cond = cond.replace('>=', '\\geq')
        cond = cond.replace('<=', '\\leq')
        cond = cond.replace('==', '=')
        cond = cond.replace('!=', '\\neq')
        latex_conditions.append(cond)

    return ' \\land '.join(latex_conditions)


def convert_rule(egglog_rule: str) -> str:
    """
    Convert an egglog rewrite rule to LaTeX inference rule format.

    Args:
        egglog_rule: The egglog rewrite rule string

    Returns:
        LaTeX-formatted inference rule
    """
    # Extract LHS from rewrite(...)
    lhs_expr, _ = extract_balanced_expr(egglog_rule, 'rewrite(')
    if not lhs_expr:
        return "Error: Could not extract LHS expression"

    # Extract RHS from .to(...)
    to_index = egglog_rule.find('.to(')
    if to_index == -1:
        return "Error: Could not find .to() clause"

    rhs_expr, _ = extract_balanced_expr(egglog_rule[to_index:], '.to(')
    if not rhs_expr:
        return "Error: Could not extract RHS expression"

    # Extract conditions
    conditions = extract_conditions(egglog_rule)

    # Clean expressions for LaTeX
    lhs_clean = clean_expression(lhs_expr)
    rhs_clean = clean_expression(rhs_expr)

    # Format as inference rule
    if conditions:
        cond_latex = format_conditions_latex(conditions)
        numerator = f"expr = {lhs_clean}, {cond_latex}"
    else:
        numerator = f"expr = {lhs_clean}"

    denominator = f"expr \\to {rhs_clean}"
    return f"\\frac{{{numerator}}}{{{denominator}}}"
