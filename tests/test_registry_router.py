from robin.registry import load_agents, load_skills, validate
from robin.router import Router


def test_registry_valid():
    assert validate() == []


def test_every_department_has_agent_and_skills():
    agents = load_agents()
    depts = {a.department for a in agents.values() if a.kind == "department"}
    assert {"executive", "product", "marketing", "market-research", "data", "sales-bd", "customer-support",
            "operations", "engineering", "finance", "people", "legal-compliance"} <= depts
    for a in agents.values():
        assert a.skills, a.name


def test_restricted_agents_marked():
    agents = load_agents()
    for name in ("finance-analyst", "people-partner", "compliance-officer"):
        assert agents[name].sensitivity == "restricted"


def test_router_examples_route_home():
    """Each agent's own examples must route to it (sanity, not the eval)."""
    router = Router(active=None)
    for a in load_agents().values():
        if a.kind != "department":
            continue
        for ex in a.examples:
            assert router.route(ex).agents[0].name == a.name, (ex, router.route(ex).agents)


def test_low_confidence_falls_back_to_chief_of_staff():
    assert Router().route("hello").agent == "chief-of-staff"


def test_shortlist_prompt_block():
    block = Router().route("Why did FTD drop in Mexico?").as_prompt()
    assert block.startswith("<routing_shortlist>") and "data-analyst" in block


def test_skills_have_examples():
    for s in load_skills().values():
        assert len(s.examples) >= 2


def test_inactive_department_goes_to_chief_of_staff():
    r = Router(active={"product", "market-research", "data", "marketing"}).route(
        "Write a job description for a senior backend engineer")
    assert r.agent == "chief-of-staff" and r.inactive == "people"
    assert "inactive department: people" in r.as_prompt()
    assert all(m.name in {"product-lead", "research-lead", "data-analyst", "marketing-lead"} for m in r.agents)


def test_active_department_routes_normally():
    r = Router(active={"product", "market-research", "data", "marketing"}).route("Why did FTD drop in Mexico?")
    assert r.agent == "data-analyst" and r.inactive is None


def test_config_activates_four_departments():
    from robin.router import active_departments
    assert active_departments() == {"product", "market-research", "data", "marketing"}
