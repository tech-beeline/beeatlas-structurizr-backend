#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from pathlib import Path
from urllib import error, request


def post_json(url: str, payload: dict, timeout: int) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Connection error for {url}: {exc.reason}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Runs chained test: POST /api/v1/workspace/conversion2doc "
            "then POST /api/v1/workspace/{docId}/fdm on localhost."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Service base URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--dsl-file",
        default="workspace.dsl",
        help="Path to DSL file to upload (default: workspace.dsl)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60)",
    )
    args = parser.parse_args()

    dsl_path = Path(args.dsl_file)
    if not dsl_path.exists():
        raise RuntimeError(f"DSL file not found: {dsl_path}")

    dsl_text = dsl_path.read_text(encoding="utf-8")
    workspace_b64 = base64.b64encode(dsl_text.encode("utf-8")).decode("ascii")

    conversion_url = f"{args.base_url.rstrip('/')}/api/v1/workspace/conversion2doc"
    print(f"[1/2] POST {conversion_url}")
    status_1, body_1 = post_json(conversion_url, {"workspace": workspace_b64}, args.timeout)
    print(f"Status: {status_1}")
    print(f"Body: {json.dumps(body_1, ensure_ascii=False)}")

    doc_id = body_1.get("doc_id") or body_1.get("docId")
    if not doc_id:
        raise RuntimeError("doc_id not found in conversion2doc response")


    #fdm_url = f"{args.base_url.rstrip('/')}/api/v1/workspace/{doc_id}/fdm"
    pipelineId = 90011
    fdm_url = f"{args.base_url.rstrip('/')}/api/v1/fitness-function/local/{doc_id}?pipelineId={pipelineId}"
    print(f"[2/2] POST {fdm_url}")
    status_2, body_2 = post_json(fdm_url, {}, args.timeout)
    print(f"Status: {status_2}")
    print(f"Body: {json.dumps(body_2, ensure_ascii=False)}")

    if status_2 not in (200, 201):
        raise RuntimeError(f"fdm endpoint returned unexpected status: {status_2}")

    print("Done: chained test completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
