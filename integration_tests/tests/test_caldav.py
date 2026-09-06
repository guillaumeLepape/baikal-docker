import httpx2

from http import HTTPStatus

EVENT_ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//baikal-docker//integration-test//EN
BEGIN:VEVENT
UID:{uid}@baikal-docker-tests
DTSTAMP:20260101T000000Z
DTSTART:20260101T100000Z
DTEND:20260101T110000Z
SUMMARY:{summary}
END:VEVENT
END:VCALENDAR
"""

CALENDAR_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop><d:getetag/></d:prop>
  <c:filter>
    <c:comp-filter name="VCALENDAR">
      <c:comp-filter name="VEVENT"/>
    </c:comp-filter>
  </c:filter>
</c:calendar-query>
"""


def _calendar_url(server):
    return f"{server['base_url']}/dav.php/calendars/{server['username']}/default/"


def _auth(server):
    return (server["username"], server["password"])


def test_default_calendar_is_discoverable(baikal_server):
    resp = httpx2.request(
        "PROPFIND",
        f"{baikal_server['base_url']}/dav.php/calendars/{baikal_server['username']}/",
        auth=_auth(baikal_server),
        headers={"Depth": "1", "Content-Type": "application/xml"},
        content=(
            '<?xml version="1.0"?><propfind xmlns="DAV:"><prop><resourcetype/></prop></propfind>'
        ),
    )
    assert resp.status_code == HTTPStatus.MULTI_STATUS
    assert "default/" in resp.text


def test_put_and_get_event_round_trips(baikal_server):
    event_url = _calendar_url(baikal_server) + "roundtrip.ics"
    body = EVENT_ICS.format(uid="roundtrip", summary="Integration Test Event")

    put_resp = httpx2.put(
        event_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/calendar; charset=utf-8"},
        content=body,
    )
    assert put_resp.status_code in (HTTPStatus.CREATED, HTTPStatus.NO_CONTENT)

    get_resp = httpx2.get(event_url, auth=_auth(baikal_server))
    assert get_resp.status_code == HTTPStatus.OK
    assert "SUMMARY:Integration Test Event" in get_resp.text
    assert "UID:roundtrip@baikal-docker-tests" in get_resp.text


def test_calendar_query_report_finds_event(baikal_server):
    event_url = _calendar_url(baikal_server) + "queryable.ics"
    body = EVENT_ICS.format(uid="queryable", summary="Queryable Event")
    put_resp = httpx2.put(
        event_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/calendar; charset=utf-8"},
        content=body,
    )
    assert put_resp.status_code in (HTTPStatus.CREATED, HTTPStatus.NO_CONTENT)

    report_resp = httpx2.request(
        "REPORT",
        _calendar_url(baikal_server),
        auth=_auth(baikal_server),
        headers={"Depth": "1", "Content-Type": "application/xml"},
        content=CALENDAR_QUERY,
    )
    assert report_resp.status_code == HTTPStatus.MULTI_STATUS
    assert "queryable.ics" in report_resp.text


def test_delete_event(baikal_server):
    event_url = _calendar_url(baikal_server) + "deleteme.ics"
    body = EVENT_ICS.format(uid="deleteme", summary="Delete Me")
    httpx2.put(
        event_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/calendar; charset=utf-8"},
        content=body,
    ).raise_for_status()

    delete_resp = httpx2.delete(event_url, auth=_auth(baikal_server))
    assert delete_resp.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)

    get_resp = httpx2.get(event_url, auth=_auth(baikal_server))
    assert get_resp.status_code == HTTPStatus.NOT_FOUND


def test_unauthenticated_request_is_rejected(baikal_server):
    resp = httpx2.get(_calendar_url(baikal_server))
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
