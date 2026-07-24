from pathlib import Path

from customer_harm.extraction.mappings import MappingRegistry, base_product_label


def test_measurement_qualifier_is_removed_only_for_product_lookup() -> None:
    assert base_product_label("Home finance (per 1,000 sales)") == "Home finance"


def test_reviewed_insurance_labels_share_a_canonical_group() -> None:
    registry = MappingRegistry.load(Path("data/mappings"))
    assert registry.product_group("Insurance & protection") == "insurance_and_pure_protection"
    assert registry.product_group("Insurance & pure protection") == "insurance_and_pure_protection"


def test_context_header_maps_without_losing_measurement_qualifier() -> None:
    registry = MappingRegistry.load(Path("data/mappings"))
    assert registry.product_group("Home finance (per 1,000 balances outstanding)") == "home_finance"
