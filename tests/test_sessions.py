from app.services.sessions import (
    ConversationHistory,
    ProjectMetadata,
    SessionStore,
)


def test_conversation_history_trims_to_max_turns():
    history = ConversationHistory(max_turns=6)
    for i in range(8):
        history.add_turn(f"user-{i}", f"assistant-{i}")

    assert history.turn_count == 6
    messages = history.build_messages("system-prompt")
    assert messages[0] == {"role": "system", "content": "system-prompt"}
    assert len(messages) == 1 + 12
    assert messages[1]["content"] == "user-2"
    assert messages[-1]["content"] == "assistant-7"


def test_build_messages_appends_current_user_without_storing():
    history = ConversationHistory(max_turns=3)
    history.add_turn("first user", "first assistant")

    messages = history.build_messages("sys", current_user="pending user")
    assert messages[-1] == {"role": "user", "content": "pending user"}
    assert history.turn_count == 1


def test_project_metadata_has_content():
    empty = ProjectMetadata()
    assert not empty.has_content()
    filled = ProjectMetadata(project_name="Alpha")
    assert filled.has_content()


def test_session_store_create_get_delete():
    store = SessionStore()
    session_id = store.create()
    session = store.get(session_id)

    assert session is not None
    assert session.session_id == session_id
    assert isinstance(session.metadata, ProjectMetadata)
    assert session.history.turn_count == 0
    assert len(store) == 1

    assert store.delete(session_id) is True
    assert store.get(session_id) is None
    assert store.delete(session_id) is False
