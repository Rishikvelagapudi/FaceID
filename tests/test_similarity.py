from PIL import Image
from app.image.similarity import _histogram_embedding, _cosine

def test_histogram_cosine():
    a = Image.new("RGB", (64, 64), "white")
    b = Image.new("RGB", (64, 64), "white")
    score = _cosine(_histogram_embedding(a), _histogram_embedding(b))
    assert score > 0.99
