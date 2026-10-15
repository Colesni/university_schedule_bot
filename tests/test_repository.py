from database.repository import UserGroupRepository


def test_user_group_lifecycle(tmp_path):
    repository = UserGroupRepository(tmp_path / "users.sqlite3")
    assert repository.get_selected_group(7) is None
    repository.save_selected_group(7, "G1")
    assert repository.get_selected_group(7) == "G1"
    repository.save_selected_group(7, "G2")
    assert repository.get_selected_group(7) == "G2"
    repository.close()
