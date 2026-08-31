import sqlite3
import tkinter as tk
from tkinter import ttk


class IssueViewer:
    def __init__(self, root, db_path="issues.db"):
        self.root = root
        self.db_path = db_path

        self.root.title("Issue Viewer")
        self.root.geometry("1100x750")

        self.create_widgets()
        self.load_issues()

    def create_widgets(self):
        # ------------------------------------------------------------------
        # Top table
        # ------------------------------------------------------------------

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=(10, 5)
        )

        columns = (
            "id",
            "title",
            "risk_rating",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("risk_rating", text="Risk Rating")

        self.tree.column("id", width=80, anchor=tk.CENTER)
        self.tree.column("title", width=700)
        self.tree.column("risk_rating", width=150, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_issue_selected
        )

        # ------------------------------------------------------------------
        # Record viewer
        # ------------------------------------------------------------------

        detail_frame = ttk.LabelFrame(
            self.root,
            text="Issue Details"
        )

        detail_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=(5, 10)
        )

        # ID
        ttk.Label(
            detail_frame,
            text="ID:"
        ).grid(
            row=0,
            column=0,
            sticky="nw",
            padx=5,
            pady=5
        )

        self.id_text = self.create_readonly_text(
            detail_frame,
            height=1
        )

        self.id_text.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        # Title
        ttk.Label(
            detail_frame,
            text="Title:"
        ).grid(
            row=1,
            column=0,
            sticky="nw",
            padx=5,
            pady=5
        )

        self.title_text = self.create_readonly_text(
            detail_frame,
            height=2
        )

        self.title_text.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        # Risk
        ttk.Label(
            detail_frame,
            text="Risk Rating:"
        ).grid(
            row=2,
            column=0,
            sticky="nw",
            padx=5,
            pady=5
        )

        self.risk_text = self.create_readonly_text(
            detail_frame,
            height=1
        )

        self.risk_text.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        # Details
        ttk.Label(
            detail_frame,
            text="Details:"
        ).grid(
            row=3,
            column=0,
            sticky="nw",
            padx=5,
            pady=5
        )

        details_container = ttk.Frame(detail_frame)
        details_container.grid(
            row=3,
            column=1,
            sticky="nsew",
            padx=5,
            pady=5
        )

        self.details_text = self.create_readonly_text(
            details_container,
            height=12,
            wrap=tk.WORD
        )

        details_scrollbar = ttk.Scrollbar(
            details_container,
            orient=tk.VERTICAL,
            command=self.details_text.yview
        )

        self.details_text.configure(
            yscrollcommand=details_scrollbar.set
        )

        self.details_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        details_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        # Notes
        ttk.Label(
            detail_frame,
            text="Notes:"
        ).grid(
            row=3,
            column=0,
            sticky="nw",
            padx=5,
            pady=5
        )

        notes_container = ttk.Frame(detail_frame)
        notes_container.grid(
            row=3,
            column=1,
            sticky="nsew",
            padx=5,
            pady=5
        )

        self.notes_text = self.create_readonly_text(
            notes_container,
            height=12,
            wrap=tk.WORD
        )

        notes_scrollbar = ttk.Scrollbar(
            notes_container,
            orient=tk.VERTICAL,
            command=self.notes_text.yview
        )

        self.notes_text.configure(
            yscrollcommand=notes_scrollbar.set
        )

        self.notes_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        notes_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )


        detail_frame.columnconfigure(
            1,
            weight=1
        )

        detail_frame.rowconfigure(
            4,
            weight=1
        )

    def create_readonly_text(
        self,
        parent,
        height=1,
        wrap=tk.NONE
    ):
        """
        Create a Text widget which the user can select/copy from,
        but cannot edit.
        """

        widget = tk.Text(
            parent,
            height=height,
            wrap=wrap
        )

        # Prevent normal keyboard editing while still allowing
        # selection and copying.
        widget.bind(
            "<Key>",
            self.prevent_edit
        )

        # Right-click context menu.
        widget.bind(
            "<Button-3>",
            self.show_context_menu
        )

        return widget

    def prevent_edit(self, event):
        """
        Allow Ctrl+C but block other keyboard input.
        """

        # Ctrl+C
        if (
            event.state & 0x4
            and event.keysym.lower() == "c"
        ):
            return

        return "break"

    def show_context_menu(self, event):
        widget = event.widget

        menu = tk.Menu(
            self.root,
            tearoff=0
        )

        menu.add_command(
            label="Copy",
            command=lambda: self.copy_selection(widget)
        )

        try:
            menu.tk_popup(
                event.x_root,
                event.y_root
            )
        finally:
            menu.grab_release()

    def copy_selection(self, widget):
        try:
            selected_text = widget.get(
                tk.SEL_FIRST,
                tk.SEL_LAST
            )
        except tk.TclError:
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(selected_text)

    def set_text(self, widget, value):
        """
        Replace the contents of a Text widget.
        """

        widget.delete(
            "1.0",
            tk.END
        )

        if value is not None:
            widget.insert(
                "1.0",
                str(value)
            )

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def load_issues(self):
        """
        Load the records used by the table.
        """

        query = """
            SELECT
                id,
                title,
                risk_rating
            FROM issues
            ORDER BY risk_rating DESC
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query)

            for row in cursor.fetchall():
                self.tree.insert(
                    "",
                    tk.END,
                    values=row
                )

    def on_issue_selected(self, event):
        selected_items = self.tree.selection()

        if not selected_items:
            return

        item = self.tree.item(selected_items[0])

        issue_id = item["values"][0]

        self.load_issue(issue_id)

    def load_issue(self, issue_id):
        """
        Load the full issue when a table row is selected.
        """

        query = """
            SELECT
                id,
                title,
                risk_rating,
                details,
                notes
            FROM issues
            WHERE id = ?
        """

        with self.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                query,
                (issue_id,)
            )

            issue = cursor.fetchone()

        if issue is None:
            return

        issue_id, title, risk_rating, details, notes = issue

        self.set_text(
            self.id_text,
            issue_id
        )

        self.set_text(
            self.title_text,
            title
        )

        self.set_text(
            self.risk_text,
            risk_rating
        )

        self.set_text(
            self.details_text,
            details
        )

        self.set_text(
            self.notes_text,
            notes
        )


if __name__ == "__main__":
    root = tk.Tk()

    app = IssueViewer(
        root,
        db_path="issues.db"
    )

    root.mainloop()
