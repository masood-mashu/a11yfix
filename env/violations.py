"""
Violation detection module for A11yFix.

NOTE:
We intentionally DO NOT include fix instructions in violations.
Agents must infer the correct fix from violation type.
"""

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
    if not attributes.get("alt"):
        return [{
            "type": "missing_alt",
            "element_id": element_id
        }]
    return []


def check_input_labels(element_id, attributes):
    has_label = attributes.get("aria-label") or attributes.get("aria-labelledby")

    if not has_label:
        return [{
            "type": "missing_label",
            "element_id": element_id
        }]
    return []


def check_button_name(element_id, attributes):
    has_text = attributes.get("text", "").strip()
    has_aria_label = attributes.get("aria-label", "").strip()
    has_aria_labelledby = attributes.get("aria-labelledby", "").strip()

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
            if not el.get("attributes", {}).get("lang"):
                return [{
                    "type": "missing_lang",
                    "element_id": el["id"]
                }]
    return []
