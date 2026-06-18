from app.sessions.metadata_extractor import merge_metadata
from app.services.sessions import ProjectMetadata


def test_merge_metadata_is_additive():
    existing = ProjectMetadata(project_name="Alpha", mentioned_technologies=["React"])
    update = ProjectMetadata(
        project_name="Alpha",
        assumed_team_size=5,
        mentioned_technologies=["React", "PostgreSQL"],
        explicit_constraints=["Must include SSO"],
    )
    merged = merge_metadata(existing, update)
    assert merged.project_name == "Alpha"
    assert merged.assumed_team_size == 5
    assert merged.mentioned_technologies == ["React", "PostgreSQL"]
    assert merged.explicit_constraints == ["Must include SSO"]


def test_merge_metadata_coerces_list_agreed_scope_to_string():
    existing = ProjectMetadata()
    update = ProjectMetadata(
        agreed_scope=["vendor catalogue", "RFQ workflow", "basic dashboards"],  # type: ignore[arg-type]
    )
    merged = merge_metadata(existing, update)
    assert isinstance(merged.agreed_scope, str)
    assert "vendor catalogue" in merged.agreed_scope
    assert "RFQ workflow" in merged.agreed_scope
