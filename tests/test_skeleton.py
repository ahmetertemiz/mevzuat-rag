from mevzuat_rag import config


def test_belgeler_mevcut():
    """Kayıttaki her PDF docs_raw içinde bulunmalı."""
    for d in config.DOCS:
        assert (config.DOCS_RAW / d.dosya).is_file(), d.dosya


def test_belge_idleri_benzersiz():
    ids = [d.belge_id for d in config.DOCS]
    assert len(ids) == len(set(ids))
