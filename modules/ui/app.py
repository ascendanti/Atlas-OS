"""
Atlas Personal OS - Desktop Demo UI

Tkinter app with Tasks and Audit tabs.
Demonstrates the Event Spine architecture: UI is a lens over events.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json

from modules.core.database import get_database
from modules.core.event_store import get_event_store
from modules.life.task_tracker import TaskTracker, TaskPriority


class AtlasApp:
    """Main Atlas desktop application."""

    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("Atlas Personal OS")
        self.root.geometry("900x600")

        # Initialize modules (uses shared database)
        self.db = get_database()
        self.event_store = get_event_store()
        self.task_tracker = TaskTracker(db=self.db, event_store=self.event_store)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.tasks_frame = ttk.Frame(self.notebook)
        self.audit_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.tasks_frame, text="Tasks")
        self.notebook.add(self.audit_frame, text="Audit")

        self._setup_tasks_tab()
        self._setup_audit_tab()

        # Bind tab change to refresh
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _setup_tasks_tab(self):
        """Set up the Tasks tab."""
        # Top frame: Add task form
        form_frame = ttk.LabelFrame(self.tasks_frame, text="Add Task")
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(form_frame, text="Title:").grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = ttk.Entry(form_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Priority:").grid(row=0, column=2, padx=5, pady=5)
        self.priority_var = tk.StringVar(value="MEDIUM")
        priority_combo = ttk.Combobox(form_frame, textvariable=self.priority_var,
                                       values=["LOW", "MEDIUM", "HIGH", "URGENT"], width=10)
        priority_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Category:").grid(row=0, column=4, padx=5, pady=5)
        self.category_entry = ttk.Entry(form_frame, width=15)
        self.category_entry.grid(row=0, column=5, padx=5, pady=5)

        add_btn = ttk.Button(form_frame, text="Add Task", command=self._add_task)
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        # Middle frame: Tasks table
        table_frame = ttk.Frame(self.tasks_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "title", "status", "priority", "category", "due_date")
        self.tasks_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("title", text="Title")
        self.tasks_tree.heading("status", text="Status")
        self.tasks_tree.heading("priority", text="Priority")
        self.tasks_tree.heading("category", text="Category")
        self.tasks_tree.heading("due_date", text="Due Date")

        self.tasks_tree.column("id", width=40)
        self.tasks_tree.column("title", width=300)
        self.tasks_tree.column("status", width=100)
        self.tasks_tree.column("priority", width=80)
        self.tasks_tree.column("category", width=100)
        self.tasks_tree.column("due_date", width=100)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)

        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom frame: Action buttons
        action_frame = ttk.Frame(self.tasks_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        complete_btn = ttk.Button(action_frame, text="Complete Selected", command=self._complete_task)
        complete_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(action_frame, text="Refresh", command=self._refresh_tasks)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        self._refresh_tasks()

    def _setup_audit_tab(self):
        """Set up the Audit tab."""
        # Events table
        table_frame = ttk.Frame(self.audit_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("timestamp", "event_type", "entity_type", "entity_id")
        self.events_tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.events_tree.heading("timestamp", text="Timestamp")
        self.events_tree.heading("event_type", text="Event Type")
        self.events_tree.heading("entity_type", text="Entity Type")
        self.events_tree.heading("entity_id", text="Entity ID")

        self.events_tree.column("timestamp", width=180)
        self.events_tree.column("event_type", width=150)
        self.events_tree.column("entity_type", width=100)
        self.events_tree.column("entity_id", width=80)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=scrollbar.set)

        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Detail pane for payload
        detail_frame = ttk.LabelFrame(self.audit_frame, text="Event Payload")
        detail_frame.pack(fill=tk.X, padx=5, pady=5)

        self.payload_text = tk.Text(detail_frame, height=6, wrap=tk.WORD)
        self.payload_text.pack(fill=tk.X, padx=5, pady=5)

        # Bind selection
        self.events_tree.bind("<<TreeviewSelect>>", self._on_event_select)

        # Store event data
        self.events_data = {}

        # Refresh button
        refresh_btn = ttk.Button(self.audit_frame, text="Refresh", command=self._refresh_events)
        refresh_btn.pack(anchor=tk.W, padx=5, pady=5)

    def _add_task(self):
        """Add a new task."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Warning", "Please enter a task title.")
            return

        priority = TaskPriority[self.priority_var.get()]
        category = self.category_entry.get().strip()

        self.task_tracker.add(title=title, priority=priority, category=category)

        # Clear form
        self.title_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)

        self._refresh_tasks()
        messagebox.showinfo("Success", f"Task '{title}' added.")

    def _complete_task(self):
        """Complete the selected task."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to complete.")
            return

        item = self.tasks_tree.item(selection[0])
        task_id = item["values"][0]

        self.task_tracker.complete(task_id)
        self._refresh_tasks()
        messagebox.showinfo("Success", f"Task {task_id} completed.")

    def _refresh_tasks(self):
        """Refresh the tasks list."""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        tasks = self.task_tracker.list(limit=100)

        if not tasks:
            self.tasks_tree.insert("", tk.END, values=("", "No tasks found", "", "", "", ""))
            return

        for task in tasks:
            priority_names = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "URGENT"}
            self.tasks_tree.insert("", tk.END, values=(
                task["id"],
                task["title"],
                task["status"],
                priority_names.get(task["priority"], "MEDIUM"),
                task["category"] or "",
                task["due_date"] or ""
            ))

    def _refresh_events(self):
        """Refresh the events list."""
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)

        self.events_data.clear()
        events = self.event_store.query(limit=100)

        if not events:
            self.events_tree.insert("", tk.END, values=("", "No events found", "", ""))
            return

        for event in events:
            item_id = self.events_tree.insert("", tk.END, values=(
                event["timestamp"],
                event["event_type"],
                event["entity_type"],
                event["entity_id"]
            ))
            self.events_data[item_id] = event

    def _on_event_select(self, event):
        """Handle event selection to show payload."""
        selection = self.events_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        event_data = self.events_data.get(item_id)

        self.payload_text.delete(1.0, tk.END)
        if event_data and "payload" in event_data:
            payload = event_data["payload"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    pass
            formatted = json.dumps(payload, indent=2)
            self.payload_text.insert(1.0, formatted)

    def _on_tab_change(self, event):
        """Handle tab change to refresh data."""
        tab_name = self.notebook.tab(self.notebook.select(), "text")
        if tab_name == "Audit":
            self._refresh_events()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


def launch():
    """Launch the Atlas desktop app."""
    app = AtlasApp()
    app.run()


if __name__ == "__main__":
    launch()
