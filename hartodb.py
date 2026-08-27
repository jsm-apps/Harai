import json
import sqlite3
import argparse

from utils.harfile import HarFile


#HAR_FILENAME = "browser_traffic.har"
#DB_FILENAME = "browser_traffic.db"


def create_database(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS http_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            har_index INTEGER,

            request_method TEXT,
            request_url TEXT,
            request_params TEXT,
            request_headers TEXT,
            request_cookies TEXT,
            request_mime_type TEXT,
            request_body TEXT,

            response_status INTEGER,
            response_result TEXT,
            response_headers TEXT,
            response_cookies TEXT,
            response_mime_type TEXT,
            response_body TEXT,

            browser_error TEXT
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_http_entries_url
        ON http_entries(request_url)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_http_entries_status
        ON http_entries(response_status)
    """)

    db.commit()


def save_entry(db, data):
    db.execute("""
        INSERT INTO http_entries (
            har_index,

            request_method,
            request_url,
            request_params,
            request_headers,
            request_cookies,
            request_mime_type,
            request_body,

            response_status,
            response_result,
            response_headers,
            response_cookies,
            response_mime_type,
            response_body,

            browser_error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["har_index"],

        data["request_method"],
        data["request_url"],
        json.dumps(data["request_params"]),
        json.dumps(data["request_headers"]),
        json.dumps(data["request_cookies"]),
        data["request_mime_type"],
        data["request_body"],

        data["response_status"],
        data["response_result"],
        json.dumps(data["response_headers"]),
        json.dumps(data["response_cookies"]),
        data["response_mime_type"],
        data["response_body"],

        data["browser_error"],
    ))


def main(HAR_FILENAME, DB_FILENAME):
    print("HAR input file:", HAR_FILENAME)
    print("DB output file:", DB_FILENAME)
    
    har = HarFile(HAR_FILENAME)

    print("Total entries:", len(har))

    db = sqlite3.connect(DB_FILENAME)

    create_database(db)


    for index, entry in enumerate(har):
        request = entry.get("request", {})
        response = entry.get("response", {})

        # ---------------------------------------------------------
        # Request
        # ---------------------------------------------------------

        request_url = request.get("url", "")
        request_method = request.get("method", "")

        request_params = request.get("queryString", [])

        # HAR already provides parsed cookies
        request_cookies = request.get("cookies", [])

        # Remove Cookie header
        request_headers = [
            header
            for header in request.get("headers", [])
            if header.get("name", "").lower() != "cookie"
        ]

        # Request body
        post_data = request.get("postData", {})

        request_mime_type = post_data.get("mimeType", "")
        request_body = post_data.get("text", "")

        # ---------------------------------------------------------
        # Response
        # ---------------------------------------------------------

        response_status = response.get("status")

        response_content = response.get("content", {})

        response_mime_type = response_content.get("mimeType", "")
        response_body = response_content.get("text", "")

        # HAR already provides parsed cookies
        response_cookies = response.get("cookies", [])

        # Remove Set-Cookie headers
        response_headers = [
            header
            for header in response.get("headers", [])
            if header.get("name", "").lower() != "set-cookie"
        ]

        browser_error = response.get("_failureText")

        # ---------------------------------------------------------
        # Result
        # ---------------------------------------------------------

        if response_status == -1:
            response_result = "failed"
        elif response_status is not None and response_status >= 400:
            response_result = "http_error"
        else:
            response_result = "success"

        # ---------------------------------------------------------
        # Store in database
        # ---------------------------------------------------------

        data = {
            "har_index": index,

            "request_method": request_method,
            "request_url": request_url,
            "request_params": request_params,
            "request_headers": request_headers,
            "request_cookies": request_cookies,
            "request_mime_type": request_mime_type,
            "request_body": request_body,

            "response_status": response_status,
            "response_result": response_result,
            "response_headers": response_headers,
            "response_cookies": response_cookies,
            "response_mime_type": response_mime_type,
            "response_body": response_body,

            "browser_error": browser_error,
        }

        save_entry(db, data)

        print(
            "{} {} {} -> {} ({})".format(
                index,
                request_method,
                request_url,
                response_status,
                response_result,
            )
        )


    db.commit()
    db.close()

    print("Saved to:", DB_FILENAME)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process a HAR file and store results in SQLite DB file."
    )

    parser.add_argument(
        "har_filename",
        help="HAR file to process"
    )

    parser.add_argument(
        "db_filename",
        nargs="?",
        default="har.db",
        help="SQLite database filename (default: har.db)"
    )

    args = parser.parse_args()

    main(args.har_filename, args.db_filename)
