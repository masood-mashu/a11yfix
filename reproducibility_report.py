import json
from typing import Any

from baseline_inference import run_baseline
from tasks.easy import get_easy_elements
from tasks.hard import get_hard_elements
from tasks.medium import get_medium_elements


def _variant_signature(elements: list[dict[str, Any]]) -> list[str]:
    return [f"{element['type']}:{element['id']}" for element in elements]


def build_reproducibility_report(num_runs: int = 5, seed_samples: tuple[int, ...] = (0, 1, 2)) -> dict[str, Any]:
    baseline_runs = [run_baseline() for _ in range(num_runs)]
    baseline_summaries = [run["summary"] for run in baseline_runs]
    first_summary = baseline_summaries[0]

    seeded_variants = {
        "easy": {str(seed): _variant_signature(get_easy_elements(seed=seed)) for seed in seed_samples},
        "medium": {str(seed): _variant_signature(get_medium_elements(seed=seed)) for seed in seed_samples},
        "hard": {str(seed): _variant_signature(get_hard_elements(seed=seed)) for seed in seed_samples},
    }

    return {
        "baseline_runs": num_runs,
        "baseline_deterministic": all(summary == first_summary for summary in baseline_summaries),
        "baseline_summary": first_summary,
        "seeded_variant_support": seeded_variants,
        "seeded_variants_distinct": {
            difficulty: len(set(tuple(signature) for signature in variants.values())) > 1
            for difficulty, variants in seeded_variants.items()
        },
    }


def main() -> None:
    print(json.dumps(build_reproducibility_report(), indent=2))


if __name__ == "__main__":
    main()
