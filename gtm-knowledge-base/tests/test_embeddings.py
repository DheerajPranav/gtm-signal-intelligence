import numpy as np

from gtm_kb.embeddings import HashingEmbedder, TfidfHashingEmbedder


def test_deterministic_same_text_same_vector():
    e = HashingEmbedder(dim=256)
    a = e.embed_query("Northstar competitors Clari Gong")
    b = e.embed_query("Northstar competitors Clari Gong")
    assert np.array_equal(a, b)


def test_vectors_are_l2_normalized_and_right_dim():
    e = HashingEmbedder(dim=128)
    v = e.embed_query("pipeline hygiene forecast accuracy")
    assert v.shape == (128,)
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-5


def test_empty_text_is_zero_vector_without_nan():
    e = HashingEmbedder(dim=64)
    v = e.embed_query("")
    assert v.shape == (64,)
    assert float(np.linalg.norm(v)) == 0.0
    assert not np.isnan(v).any()


def test_embed_documents_shape():
    e = HashingEmbedder(dim=100)
    mat = e.embed_documents(["alpha beta", "gamma delta epsilon"])
    assert mat.shape == (2, 100)


def test_lexical_relevance_orders_correctly():
    """A competitor-themed query should be more similar to competitor text than to
    unrelated pricing text (cosine == dot on normalized vectors)."""
    e = HashingEmbedder(dim=1024)
    q = e.embed_query("What competitors does Northstar have?")
    competitor_doc = e.embed_query("Northstar competes with Clari, Gong, Mosaic and Pigment.")
    pricing_doc = e.embed_query("Core costs 2500 dollars per month for up to 40 seats.")
    assert float(q @ competitor_doc) > float(q @ pricing_doc)


def test_tfidf_is_deterministic_after_fit():
    corpus = ["northstar pipeline forecast", "northstar clari gong competitor", "northstar pricing seats"]
    a = TfidfHashingEmbedder(dim=256).fit(corpus)
    b = TfidfHashingEmbedder(dim=256).fit(corpus)
    assert np.array_equal(a.idf, b.idf)
    assert np.array_equal(a.embed_query("clari competitor"), b.embed_query("clari competitor"))


def test_tfidf_downweights_ubiquitous_terms():
    # "northstar" appears in every doc (low idf); "clari" in one (high idf).
    corpus = ["northstar pipeline", "northstar forecast", "northstar clari competitor"]
    e = TfidfHashingEmbedder(dim=4096).fit(corpus)
    from gtm_kb.embeddings import _bucket

    idf_common = float(e.idf[_bucket("northstar", e.dim)])
    idf_rare = float(e.idf[_bucket("clari", e.dim)])
    assert idf_rare > idf_common


def test_tfidf_save_load_roundtrip(tmp_path):
    corpus = ["alpha beta", "beta gamma", "gamma delta clari"]
    e = TfidfHashingEmbedder(dim=128).fit(corpus)
    path = tmp_path / "embedder.npz"
    e.save(path)
    loaded = TfidfHashingEmbedder(dim=128).load(path)
    assert np.array_equal(e.idf, loaded.idf)
    assert np.array_equal(e.embed_query("clari"), loaded.embed_query("clari"))
