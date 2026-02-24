from crowe_codex.cloud.marketplace import (
    StrategyMarketplace,
    StrategyListing,
    MarketplaceIndex,
    BUILTIN_STRATEGIES,
)
from crowe_codex.strategies.consensus import Consensus


def test_strategy_listing_creation():
    listing = StrategyListing(
        name="custom_strategy",
        display_name="Custom Strategy",
        description="A custom strategy",
        author="test-user",
        version="0.1.0",
        tags=["custom", "testing"],
    )
    assert listing.name == "custom_strategy"
    assert listing.downloads == 0


def test_strategy_listing_serialization():
    listing = StrategyListing(
        name="test", display_name="Test",
        description="desc", author="me", version="1.0",
    )
    d = listing.to_dict()
    l2 = StrategyListing.from_dict(d)
    assert l2.name == "test"
    assert l2.author == "me"


def test_strategy_listing_from_strategy():
    strategy = Consensus()
    listing = StrategyListing.from_strategy(
        strategy, author="crowe-codex", description="Consensus mode"
    )
    assert listing.name == "consensus"
    assert listing.author == "crowe-codex"
    assert len(listing.stages_required) > 0


def test_marketplace_index_empty():
    index = MarketplaceIndex()
    assert index.total_listings == 0
    assert index.categories == []


def test_marketplace_index_search():
    listings = [
        StrategyListing(name="adversarial", display_name="Adversarial",
                       description="Attack/defend", author="a", version="1.0",
                       tags=["security"], downloads=100),
        StrategyListing(name="consensus", display_name="Consensus",
                       description="Compare outputs", author="b", version="1.0",
                       tags=["comparison"], downloads=200),
    ]
    index = MarketplaceIndex(listings=listings)
    results = index.search(query="attack")
    assert len(results) == 1
    assert results[0].name == "adversarial"


def test_marketplace_index_search_by_tags():
    listings = [
        StrategyListing(name="a", display_name="A", description="x",
                       author="a", version="1.0", tags=["security"]),
        StrategyListing(name="b", display_name="B", description="y",
                       author="b", version="1.0", tags=["testing"]),
    ]
    index = MarketplaceIndex(listings=listings)
    results = index.search(tags=["security"])
    assert len(results) == 1
    assert results[0].name == "a"


def test_marketplace_index_sorted_by_downloads():
    listings = [
        StrategyListing(name="low", display_name="Low", description="x",
                       author="a", version="1.0", downloads=10),
        StrategyListing(name="high", display_name="High", description="y",
                       author="b", version="1.0", downloads=1000),
    ]
    index = MarketplaceIndex(listings=listings)
    results = index.search()
    assert results[0].name == "high"


def test_marketplace_index_categories():
    listings = [
        StrategyListing(name="a", display_name="A", description="x",
                       author="a", version="1.0", tags=["security", "testing"]),
        StrategyListing(name="b", display_name="B", description="y",
                       author="b", version="1.0", tags=["optimization"]),
    ]
    index = MarketplaceIndex(listings=listings)
    cats = index.categories
    assert "security" in cats
    assert "optimization" in cats


def test_builtin_strategies_defined():
    assert len(BUILTIN_STRATEGIES) == 7


def test_marketplace_has_builtins(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    assert mp.total_listings >= 7


def test_marketplace_browse(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    results = mp.browse()
    assert len(results) >= 7


def test_marketplace_browse_with_query(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    results = mp.browse(query="adversarial")
    assert any(r.name == "adversarial" for r in results)


def test_marketplace_browse_by_tag(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    results = mp.browse(tags=["security"])
    assert all(any("security" in r.tags for r in [r]) for r in results)


def test_marketplace_get_listing(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    listing = mp.get_listing("consensus")
    assert listing is not None
    assert listing.name == "consensus"


def test_marketplace_get_missing(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    assert mp.get_listing("nonexistent") is None


def test_marketplace_publish(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    custom = StrategyListing(
        name="my_custom",
        display_name="My Custom Strategy",
        description="Does custom things",
        author="test-user",
        version="0.1.0",
        tags=["custom"],
    )
    mp.publish(custom)
    assert mp.get_listing("my_custom") is not None


def test_marketplace_rate(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    assert mp.rate("adversarial", 5.0) is True
    listing = mp.get_listing("adversarial")
    assert listing is not None
    assert listing.rating == 5.0
    assert listing.rating_count == 1


def test_marketplace_rate_average(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    mp.rate("consensus", 4.0)
    mp.rate("consensus", 2.0)
    listing = mp.get_listing("consensus")
    assert listing is not None
    assert listing.rating == 3.0
    assert listing.rating_count == 2


def test_marketplace_rate_nonexistent(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    assert mp.rate("nonexistent", 5.0) is False


def test_marketplace_persistence(tmp_path):
    path = tmp_path / "index.json"
    mp1 = StrategyMarketplace(persist_path=path)
    mp1.publish(StrategyListing(
        name="custom", display_name="Custom",
        description="x", author="a", version="1.0",
    ))

    mp2 = StrategyMarketplace(persist_path=path)
    assert mp2.get_listing("custom") is not None


def test_marketplace_categories(tmp_path):
    path = tmp_path / "index.json"
    mp = StrategyMarketplace(persist_path=path)
    cats = mp.categories
    assert "security" in cats
    assert "verification" in cats
