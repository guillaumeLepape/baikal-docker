import httpx2

from http import HTTPStatus

CONTACT_VCF = """BEGIN:VCARD
VERSION:3.0
UID:{uid}
FN:{fn}
N:{fn};;;;
EMAIL:{uid}@example.com
END:VCARD
"""

ADDRESSBOOK_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<c:addressbook-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
  <d:prop><d:getetag/></d:prop>
</c:addressbook-query>
"""


def _addressbook_url(server):
    return f"{server['base_url']}/dav.php/addressbooks/{server['username']}/default/"


def _auth(server):
    return (server["username"], server["password"])


def test_default_addressbook_is_discoverable(baikal_server):
    resp = httpx2.request(
        "PROPFIND",
        f"{baikal_server['base_url']}/dav.php/addressbooks/{baikal_server['username']}/",
        auth=_auth(baikal_server),
        headers={"Depth": "1", "Content-Type": "application/xml"},
        content=(
            '<?xml version="1.0"?><propfind xmlns="DAV:"><prop><resourcetype/></prop></propfind>'
        ),
    )
    assert resp.status_code == HTTPStatus.MULTI_STATUS
    assert "default/" in resp.text


def test_put_and_get_contact_round_trips(baikal_server):
    contact_url = _addressbook_url(baikal_server) + "roundtrip.vcf"
    body = CONTACT_VCF.format(uid="roundtrip", fn="Round Trip")

    put_resp = httpx2.put(
        contact_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/vcard; charset=utf-8"},
        content=body,
    )
    assert put_resp.status_code in (HTTPStatus.CREATED, HTTPStatus.NO_CONTENT)

    get_resp = httpx2.get(contact_url, auth=_auth(baikal_server))
    assert get_resp.status_code == HTTPStatus.OK
    assert "FN:Round Trip" in get_resp.text
    assert "UID:roundtrip" in get_resp.text


def test_addressbook_query_report_finds_contact(baikal_server):
    contact_url = _addressbook_url(baikal_server) + "queryable.vcf"
    body = CONTACT_VCF.format(uid="queryable", fn="Queryable Contact")
    put_resp = httpx2.put(
        contact_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/vcard; charset=utf-8"},
        content=body,
    )
    assert put_resp.status_code in (HTTPStatus.CREATED, HTTPStatus.NO_CONTENT)

    report_resp = httpx2.request(
        "REPORT",
        _addressbook_url(baikal_server),
        auth=_auth(baikal_server),
        headers={"Depth": "1", "Content-Type": "application/xml"},
        content=ADDRESSBOOK_QUERY,
    )
    assert report_resp.status_code == HTTPStatus.MULTI_STATUS
    assert "queryable.vcf" in report_resp.text


def test_delete_contact(baikal_server):
    contact_url = _addressbook_url(baikal_server) + "deleteme.vcf"
    body = CONTACT_VCF.format(uid="deleteme", fn="Delete Me")
    httpx2.put(
        contact_url,
        auth=_auth(baikal_server),
        headers={"Content-Type": "text/vcard; charset=utf-8"},
        content=body,
    ).raise_for_status()

    delete_resp = httpx2.delete(contact_url, auth=_auth(baikal_server))
    assert delete_resp.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)

    get_resp = httpx2.get(contact_url, auth=_auth(baikal_server))
    assert get_resp.status_code == HTTPStatus.NOT_FOUND


def test_unauthenticated_request_is_rejected(baikal_server):
    resp = httpx2.get(_addressbook_url(baikal_server))
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
