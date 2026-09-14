"""Share an episode Slides file with a collaborator by email — no browser.

Uses the same Drive OAuth token as push_deck.py (full drive scope; the
claude.ai Drive connector cannot change sharing). Idempotent: if the person
already holds the role, Drive just returns the existing permission.

    python share_deck.py --file-id <driveFileId> --email credds19@gmail.com --role writer
    python share_deck.py --file-id <driveFileId> --list

Roles: writer (editor) | commenter | reader. A notification email goes out
unless --no-notify.
"""

import argparse
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

import certifi

from push_deck import EP4_FILE_ID, get_credentials

COREY = "credds19@gmail.com"


def _call(method, url, creds, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Drive API {e.code}: {e.read().decode('utf-8', 'replace')}")


def list_permissions(file_id, creds):
    url = (f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
           "?fields=permissions(id,type,role,emailAddress,displayName)")
    return _call("GET", url, creds).get("permissions", [])


def share(file_id, email, role, creds, notify=True, message=None):
    url = (f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
           f"?sendNotificationEmail={'true' if notify else 'false'}"
           "&fields=id,type,role,emailAddress")
    if notify and message:
        url += "&emailMessage=" + urllib.parse.quote(message)
    body = {"type": "user", "role": role, "emailAddress": email}
    return _call("POST", url, creds, body)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file-id", default=EP4_FILE_ID)
    ap.add_argument("--email", default=COREY)
    ap.add_argument("--role", default="writer", choices=["writer", "commenter", "reader"])
    ap.add_argument("--message", default=None, help="text for the notification email")
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--list", action="store_true", help="only list current permissions")
    args = ap.parse_args()
    creds = get_credentials()
    if not args.list:
        p = share(args.file_id, args.email, args.role, creds,
                  notify=not args.no_notify, message=args.message)
        print(f"shared: {p.get('emailAddress')} as {p.get('role')} (permission {p.get('id')})")
    for p in list_permissions(args.file_id, creds):
        print(f"  {p.get('role'):10s} {p.get('type'):6s} {p.get('emailAddress') or ''} {p.get('displayName') or ''}")


if __name__ == "__main__":
    main()
