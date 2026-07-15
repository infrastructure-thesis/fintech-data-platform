def test_sample_transaction(sample_transaction):
    """Test sample transaction fixture"""
    assert sample_transaction["id"] == "tx_001"
    assert sample_transaction["amount"] == 100.50
    assert sample_transaction["region"] == "EU"
