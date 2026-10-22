import pytest

from helpdesk_bot.database import Database

G = 111


@pytest.fixture()
def db(tmp_path):
    d = Database(str(tmp_path / "test.db"))
    d.init()
    return d


def test_create_and_get(db):
    tid = db.create_ticket(G, 1, "VPN down", "Cannot connect", "High")
    t = db.get_ticket(G, tid)
    assert t["title"] == "VPN down" and t["status"] == "Open" and t["assigned_to"] is None


def test_invalid_priority_rejected(db):
    with pytest.raises(ValueError):
        db.create_ticket(G, 1, "x", "y", "Urgent")


def test_tickets_are_scoped_per_guild(db):
    tid = db.create_ticket(G, 1, "a", "b", "Low")
    assert db.get_ticket(222, tid) is None
    assert db.set_status(222, tid, "Closed") is False


def test_status_assign_and_stats(db):
    tid = db.create_ticket(G, 1, "a", "b", "Low")
    assert db.set_status(G, tid, "In Progress")
    assert db.assign(G, tid, 42)
    assert db.get_ticket(G, tid)["assigned_to"] == "42"
    assert db.stats(G)["In Progress"] == 1
    with pytest.raises(ValueError):
        db.set_status(G, tid, "Bogus")


def test_missing_ticket_returns_false(db):
    assert db.set_status(G, 999, "Closed") is False
    assert db.assign(G, 999, 1) is False


def test_replies_ordered(db):
    tid = db.create_ticket(G, 1, "a", "b", "Low")
    db.add_reply(tid, 1, "first")
    db.add_reply(tid, 2, "second")
    assert [r["message"] for r in db.get_replies(tid)] == ["first", "second"]


def test_list_filters(db):
    a = db.create_ticket(G, 1, "a", "b", "Low")
    db.create_ticket(G, 1, "c", "d", "Low")
    db.set_status(G, a, "Closed")
    assert len(db.list_tickets(G)) == 2
    assert [t["id"] for t in db.list_tickets(G, status="Closed")] == [a]


def test_settings_upsert(db):
    assert db.get_setting(G, "log_channel_id") is None
    db.set_setting(G, "log_channel_id", "1")
    db.set_setting(G, "log_channel_id", "2")
    assert db.get_setting(G, "log_channel_id") == "2"
