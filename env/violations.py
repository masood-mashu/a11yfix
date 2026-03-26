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

        elif element_type == "html":
            violations += check_lang(elements)

    return violations


# ---------- VIOLATION CHECKS ----------

def check_missing_alt(element_id, attributes):
    if not attributes.get("alt"):
        return [{
            "type": "missing_alt",
            "element_id": element_id,
            "fix": {
                "action": "set_attribute",
                "attr": "alt"
            }
        }]
    return []


def check_input_labels(element_id, attributes):
    has_label = attributes.get("aria-label") or attributes.get("aria-labelledby")

    if not has_label:
        return [{
            "type": "missing_label",
            "element_id": element_id,
            "fix": {
                "action": "set_attribute",
                "attr": "aria-label"
            }
        }]
    return []


def check_button_name(element_id, attributes):
    has_text = attributes.get("text", "").strip()

    # Dependency: ONLY text resolves violation
    if not has_text:
        return [{
            "type": "missing_button_name",
            "element_id": element_id,
            "fix": {
                "action": "set_attribute",
                "attr": "text"
            }
        }]

    return []

def check_lang(elements):
    for el in elements:
        if el["type"] == "html":
            if not el.get("attributes", {}).get("lang"):
                return [{
                    "type": "missing_lang",
                    "element_id": el["id"],
                    "fix": {
                        "action": "set_attribute",
                        "attr": "lang"
                    }
                }]
    return []

if __name__ == "__main__":
    elements = [
        {"id": "img1", "type": "img", "attributes": {}},
        {"id": "input1", "type": "input", "attributes": {}},
        {"id": "btn1", "type": "button", "attributes": {}}
    ]

    violations = detect_violations(elements)

    print("Violations:")
    for v in violations:
        print(v)