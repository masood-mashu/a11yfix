"""
Violation detection module for A11yFix.

NOTE:
We intentionally DO NOT include fix instructions in violations.
Agents must infer the correct fix from violation type.
"""

PLACEHOLDER_TEXT_VALUES = {
    "a",
    "aa",
    "aaa",
    "fix",
    "fixed",
    "placeholder",
    "test",
    "todo",
    "value",
    "label",
    "button",
    "image",
    "input",
    "name",
    "n/a",
}


def _normalized_text(value):
    return str(value or "").strip()


def _is_meaningful_text(value, *, min_length=3):
    normalized = _normalized_text(value)
    if len(normalized) < min_length:
        return False
    return normalized.lower() not in PLACEHOLDER_TEXT_VALUES


def _is_valid_lang(value):
    normalized = _normalized_text(value).lower()
    if normalized in PLACEHOLDER_TEXT_VALUES:
        return False
    parts = normalized.split("-")
    if not parts or any(not part.isalpha() or len(part) < 2 for part in parts):
        return False
    return True

def detect_violations(elements):
    """
    Detect accessibility violations in a simplified JSON DOM.
    """
    violations = []

    for el in elements:
        element_id = el.get("id")
        element_type = el.get("type")
        attributes = el.get("attributes", {})

        if element_type == "img":
            violations += check_missing_alt(element_id, attributes)

        elif element_type == "input":
            violations += check_input_labels(element_id, attributes)

        elif element_type == "button":
            violations += check_button_name(element_id, attributes)

    # Evaluate document-level language rule once per snapshot.
    violations += check_lang(elements)

    return violations


# ---------- VIOLATION CHECKS ----------

def check_missing_alt(element_id, attributes):
    if not _is_meaningful_text(attributes.get("alt")):
        return [{
            "type": "missing_alt",
            "element_id": element_id
        }]
    return []


def check_input_labels(element_id, attributes):
    has_label = _is_meaningful_text(attributes.get("aria-label")) or _is_meaningful_text(
        attributes.get("aria-labelledby")
    )

    if not has_label:
        return [{
            "type": "missing_label",
            "element_id": element_id
        }]
    return []


def check_button_name(element_id, attributes):
    has_text = _is_meaningful_text(attributes.get("text"))
    has_aria_label = _is_meaningful_text(attributes.get("aria-label"))
    has_aria_labelledby = _is_meaningful_text(attributes.get("aria-labelledby"))

    # Accessible name can come from visible text or ARIA name attributes.
    if not (has_text or has_aria_label or has_aria_labelledby):
        return [{
            "type": "missing_button_name",
            "element_id": element_id
        }]

    return []


def check_lang(elements):
    for el in elements:
        if el["type"] == "html":
            if not _is_valid_lang(el.get("attributes", {}).get("lang")):
                return [{
                    "type": "missing_lang",
                    "element_id": el["id"]
                }]
    return []
