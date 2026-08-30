import sqlite3


class SqliteSearch:
    SEARCHABLE_FIELDS = [
        "request_method",
        "request_url",
        "request_params",
        "request_headers",
        "request_cookies",
        "request_mime_type",
        "request_body",
        "response_status",
        "response_result",
        "response_headers",
        "response_cookies",
        "response_mime_type",
        "response_body",
        "browser_error",
    ]

    def __init__(
        self,
        database,
        page_size=5,
        surrounding_chars=100
    ):
        self.database = database
        self.page_size = page_size
        self.surrounding_chars = surrounding_chars

        self.results = []
        self.current_page = 0

    def find(self, textToFind, field=None):
        """
        Search all records in the database.
        """
        return self._find(
            textToFind=textToFind,
            field=field,
            record_id=None
        )

    def find_with_record_id(
        self,
        record_id,
        textToFind=None,
        field=None
    ):
        """
        Search only a specific http_entries record.

        If textToFind is omitted or empty, return a summary
        of the specified record.

        Args:
            record_id:
                ID of the http_entries record.

            textToFind:
                Optional text to search for.

            field:
                Optional field to search.
                If None, all searchable fields are searched.

        Returns:
            totalRecords, results
        """

        if textToFind is None or not str(textToFind).strip():
            return self._get_record_summary(record_id)

        return self._find(
            textToFind=textToFind,
            field=field,
            record_id=record_id
        )

    def _find(
        self,
        textToFind,
        field=None,
        record_id=None
    ):
        """
        Internal search function used by find() and
        find_with_record_id().
        """

        self.results = []
        self.current_page = 0

        if textToFind is None or not str(textToFind).strip():
            return -1, {
                "error": "textToFind cannot be empty."
            }

        textToFind = str(textToFind).strip()

        if field is not None and field not in self.SEARCHABLE_FIELDS:
            return -1, {
                "error": "Invalid search field: {}".format(field),
                "searchable_fields": self.SEARCHABLE_FIELDS
            }

        print("Searching for: " + textToFind)

        if record_id is not None:
            print("Record ID: " + str(record_id))

        db = sqlite3.connect(self.database)
        db.row_factory = sqlite3.Row

        try:
            if field:
                fields = [field]
            else:
                fields = self.SEARCHABLE_FIELDS

            for search_field in fields:
                self._search_field(
                    db=db,
                    textToFind=textToFind,
                    field=search_field,
                    record_id=record_id
                )

        finally:
            db.close()

        self.results.sort(
            key=lambda result: result["har_index"]
        )

        totalRecords = len(self.results)

        print(str(totalRecords) + " records found.")

        return totalRecords, self._get_page()

    def _search_field(
        self,
        db,
        textToFind,
        field,
        record_id=None
    ):
        """
        Search one field and generate snippets.

        If record_id is supplied, only search that record.
        """

        if record_id is None:
            sql = """
                SELECT
                    id,
                    har_index,
                    request_method,
                    request_url,
                    response_status,
                    CAST({} AS TEXT) AS field_content
                FROM http_entries
                WHERE CAST({} AS TEXT) LIKE ?
                ORDER BY har_index
            """.format(field, field)

            params = (
                "%" + textToFind + "%",
            )

        else:
            sql = """
                SELECT
                    id,
                    har_index,
                    request_method,
                    request_url,
                    response_status,
                    CAST({} AS TEXT) AS field_content
                FROM http_entries
                WHERE id = ?
                  AND CAST({} AS TEXT) LIKE ?
                ORDER BY har_index
            """.format(field, field)

            params = (
                record_id,
                "%" + textToFind + "%",
            )

        cursor = db.execute(
            sql,
            params
        )

        rows = cursor.fetchall()

        for row in rows:
            content = row["field_content"]

            if content is None:
                continue

            content = str(content)

            start = 0

            while True:
                position = content.lower().find(
                    textToFind.lower(),
                    start
                )

                if position == -1:
                    break

                snippet_start = max(
                    0,
                    position - self.surrounding_chars
                )

                snippet_end = min(
                    len(content),
                    position
                    + len(textToFind)
                    + self.surrounding_chars
                )

                snippet = content[
                    snippet_start:snippet_end
                ]

                self.results.append({
                    "record_id": row["id"],
                    "har_index": row["har_index"],
                    "method": row["request_method"],
                    "url": row["request_url"],
                    "status": row["response_status"],
                    "field": field,
                    "position": position,
                    "text": snippet,
                })

                start = position + len(textToFind)

    def next(self):
        """
        Return the next page of results.
        """

        self.current_page += 1

        return self._get_page()

    def _get_page(self):
        """
        Return the current page of results.
        """

        start = self.current_page * self.page_size
        end = start + self.page_size

        return self.results[start:end]


    def _get_record_summary(self, record_id):
        """
        Return basic information about a specific HTTP record.

        Returns:
            method
            url
            status
            first 100 characters of response_body
        """

        self.results = []
        self.current_page = 0

        db = sqlite3.connect(self.database)
        db.row_factory = sqlite3.Row

        try:
            cursor = db.execute(
                """
                SELECT
                    id,
                    har_index,
                    request_method,
                    request_url,
                    response_status,
                    response_body
                FROM http_entries
                WHERE id = ?
                """,
                (record_id,)
            )

            row = cursor.fetchone()

        finally:
            db.close()

        if row is None:
            return 0, {
                "error": "Record ID {} not found.".format(record_id)
            }

        response_body = row["response_body"]

        if response_body is None:
            response_body = ""
        else:
            response_body = str(response_body)

        result = {
            "record_id": row["id"],
            "har_index": row["har_index"],
            "method": row["request_method"],
            "url": row["request_url"],
            "status": row["response_status"],
            "response_body_snippet": response_body[:300]
        }

        self.results = [result]

        return 1, self._get_page()
