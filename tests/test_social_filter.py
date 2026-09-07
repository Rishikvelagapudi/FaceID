from app.reverse_search.social_filter import classify_social_url, annotate_trust_signals

def test_classify_instagram_reel():
    url = "https://www.instagram.com/reel/DXGaS1lDMC1/"
    res = classify_social_url(url)
    assert res["is_specific_post"] is True
    assert res["platform"] == "Instagram"
    assert res["post_type"] == "Reel"
    assert res["post_id"] == "DXGaS1lDMC1"

def test_classify_twitter_status():
    url = "https://twitter.com/user/status/1234567890"
    res = classify_social_url(url)
    assert res["is_specific_post"] is True
    assert res["platform"] == "X / Twitter"
    assert res["post_type"] == "Status"
    assert res["post_id"] == "1234567890"

def test_classify_generic_portal():
    url = "https://www.instagram.com/explore"
    res = classify_social_url(url)
    assert res["is_specific_post"] is False
    assert res["platform"] == "Instagram"

def test_trust_signals_video_detection():
    item = {
        "title": "Viral Face Reel Video",
        "link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
    signals = annotate_trust_signals(item)
    assert signals["platform"] == "YouTube"
    assert signals["is_specific_post"] is True
    assert signals["is_video"] is True
