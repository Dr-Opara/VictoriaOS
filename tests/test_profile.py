from backend.profile.profile import UserProfile


def test_parse_preference_command():
    result = UserProfile.parse_preference_command("remember my favorite airline is United")
    assert result == ("favorite airline", "United")


def test_parse_preference_command_ignores_non_matching_text():
    assert UserProfile.parse_preference_command("what's the weather today") is None


def test_set_and_get_preference():
    profile = UserProfile()
    profile.set_preference("Hotel Chain", "Marriott")

    assert profile.get_preference("hotel chain") == "Marriott"


def test_set_preference_updates_existing_value():
    profile = UserProfile()
    profile.set_preference("coffee", "Starbucks")
    profile.set_preference("coffee", "Peet's")

    assert profile.get_preference("coffee") == "Peet's"
    assert len(profile.all_preferences()) == 1
