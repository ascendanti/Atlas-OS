#!/usr/bin/env python3
"""
Atlas Personal OS - Main CLI Entry Point

Usage:
    python main.py --help
    python main.py task list
    python main.py task add "Buy groceries"
    python main.py finance portfolio
    python main.py life contacts list
    python main.py life habits today
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click
from datetime import datetime, date

# Version
__version__ = "0.1.0"

# Directories
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Atlas Personal OS - Local-first automation system"""
    pass


# ============================================================================
# TASK COMMANDS
# ============================================================================

@cli.group()
def task():
    """Task management commands"""
    pass


@task.command("list")
@click.option("--status", "-s", type=click.Choice(["pending", "in_progress", "completed", "cancelled"]), help="Filter by status")
@click.option("--category", "-c", help="Filter by category")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all tasks including completed")
def task_list(status, category, show_all):
    """List all tasks"""
    from modules.life.task_tracker import TaskTracker, TaskStatus

    tracker = TaskTracker()
    status_filter = None
    if status:
        status_filter = TaskStatus(status)
    elif not show_all:
        status_filter = TaskStatus.PENDING

    tasks = tracker.list(status=status_filter, category=category)

    if not tasks:
        click.echo("No tasks found.")
        return

    click.echo(f"\n{'ID':<4} {'Priority':<8} {'Status':<12} {'Due':<12} {'Title'}")
    click.echo("-" * 70)

    priority_symbols = {1: "LOW", 2: "MED", 3: "HIGH", 4: "URGENT"}

    for t in tasks:
        priority = priority_symbols.get(t["priority"], "MED")
        status_display = t["status"].replace("_", " ").title()
        due = t["due_date"] or "-"
        title = t["title"][:40] + "..." if len(t["title"]) > 40 else t["title"]
        click.echo(f"{t['id']:<4} {priority:<8} {status_display:<12} {due:<12} {title}")

    click.echo(f"\nTotal: {len(tasks)} task(s)")


@task.command("add")
@click.argument("title")
@click.option("--description", "-d", default="", help="Task description")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high", "urgent"]), default="medium")
@click.option("--category", "-c", default="", help="Task category")
@click.option("--due", help="Due date (YYYY-MM-DD)")
def task_add(title, description, priority, category, due):
    """Add a new task"""
    from modules.life.task_tracker import TaskTracker, TaskPriority
    from modules.core.utils import parse_date

    tracker = TaskTracker()
    priority_map = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM, "high": TaskPriority.HIGH, "urgent": TaskPriority.URGENT}

    due_date = None
    if due:
        try:
            due_date = parse_date(due)
        except ValueError:
            click.echo(f"Error: Invalid date format: {due}")
            return

    task_id = tracker.add(title=title, description=description, priority=priority_map[priority], category=category, due_date=due_date)
    click.echo(f"Created task #{task_id}: {title}")


@task.command("complete")
@click.argument("task_id", type=int)
def task_complete(task_id):
    """Mark a task as completed"""
    from modules.life.task_tracker import TaskTracker

    tracker = TaskTracker()
    task = tracker.get(task_id)
    if not task:
        click.echo(f"Error: Task #{task_id} not found.")
        return
    if tracker.complete(task_id):
        click.echo(f"Completed task #{task_id}: {task['title']}")


@task.command("delete")
@click.argument("task_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def task_delete(task_id, yes):
    """Delete a task"""
    from modules.life.task_tracker import TaskTracker

    tracker = TaskTracker()
    task = tracker.get(task_id)
    if not task:
        click.echo(f"Error: Task #{task_id} not found.")
        return

    if not yes:
        click.confirm(f"Delete task '{task['title']}'?", abort=True)

    if tracker.delete(task_id):
        click.echo(f"Deleted task #{task_id}")


@task.command("show")
@click.argument("task_id", type=int)
def task_show(task_id):
    """Show task details"""
    from modules.life.task_tracker import TaskTracker

    tracker = TaskTracker()
    task = tracker.get(task_id)
    if not task:
        click.echo(f"Error: Task #{task_id} not found.")
        return

    priority_names = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}
    click.echo(f"\nTask #{task['id']}")
    click.echo("-" * 40)
    click.echo(f"Title:       {task['title']}")
    click.echo(f"Description: {task['description'] or '-'}")
    click.echo(f"Status:      {task['status'].replace('_', ' ').title()}")
    click.echo(f"Priority:    {priority_names.get(task['priority'], 'Medium')}")
    click.echo(f"Category:    {task['category'] or '-'}")
    click.echo(f"Due Date:    {task['due_date'] or '-'}")
    click.echo(f"Created:     {task['created_at']}")


@task.command("due")
def task_due():
    """Show tasks due today and overdue"""
    from modules.life.task_tracker import TaskTracker

    tracker = TaskTracker()
    overdue = tracker.get_overdue()
    due_today = tracker.get_due_today()

    if overdue:
        click.echo("\nOVERDUE:")
        for t in overdue:
            click.echo(f"  #{t['id']} {t['title']} (due: {t['due_date']})")

    if due_today:
        click.echo("\nDUE TODAY:")
        for t in due_today:
            click.echo(f"  #{t['id']} {t['title']}")

    if not overdue and not due_today:
        click.echo("No tasks due today or overdue.")


# ============================================================================
# LIFE COMMANDS
# ============================================================================

@cli.group()
def life():
    """Life management commands"""
    pass


# --- Contacts ---
@life.group()
def contacts():
    """Contact management (Rolodex)"""
    pass


@contacts.command("list")
@click.option("--category", "-c", type=click.Choice(["family", "friend", "colleague", "professional", "acquaintance", "other"]))
def contacts_list(category):
    """List all contacts"""
    from modules.life.contact_manager import ContactManager, ContactCategory

    manager = ContactManager()
    cat_filter = ContactCategory(category) if category else None
    contact_list = manager.list(category=cat_filter)

    if not contact_list:
        click.echo("No contacts found.")
        return

    click.echo(f"\n{'ID':<4} {'Name':<25} {'Category':<12} {'Email'}")
    click.echo("-" * 70)

    for c in contact_list:
        name = manager.full_name(c)[:24]
        cat = c["category"] or "-"
        email = c["email"] or "-"
        click.echo(f"{c['id']:<4} {name:<25} {cat:<12} {email}")

    click.echo(f"\nTotal: {len(contact_list)} contact(s)")


@contacts.command("add")
@click.argument("first_name")
@click.option("--last", "-l", default="", help="Last name")
@click.option("--email", "-e", default="", help="Email address")
@click.option("--phone", "-p", default="", help="Phone number")
@click.option("--category", "-c", type=click.Choice(["family", "friend", "colleague", "professional", "acquaintance", "other"]), default="other")
def contacts_add(first_name, last, email, phone, category):
    """Add a new contact"""
    from modules.life.contact_manager import ContactManager, ContactCategory

    manager = ContactManager()
    contact_id = manager.add(
        first_name=first_name,
        last_name=last,
        email=email,
        phone=phone,
        category=ContactCategory(category)
    )
    click.echo(f"Created contact #{contact_id}: {first_name} {last}".strip())


@contacts.command("show")
@click.argument("contact_id", type=int)
def contacts_show(contact_id):
    """Show contact details"""
    from modules.life.contact_manager import ContactManager

    manager = ContactManager()
    contact = manager.get(contact_id)
    if not contact:
        click.echo(f"Error: Contact #{contact_id} not found.")
        return

    click.echo(f"\nContact #{contact['id']}")
    click.echo("-" * 40)
    click.echo(f"Name:     {manager.full_name(contact)}")
    click.echo(f"Email:    {contact['email'] or '-'}")
    click.echo(f"Phone:    {contact['phone'] or '-'}")
    click.echo(f"Category: {contact['category']}")
    click.echo(f"Company:  {contact['company'] or '-'}")
    click.echo(f"Birthday: {contact['birthday'] or '-'}")
    if contact['last_contact']:
        click.echo(f"Last Contact: {contact['last_contact']}")


@contacts.command("birthdays")
@click.option("--days", "-d", default=30, help="Days to look ahead")
def contacts_birthdays(days):
    """Show upcoming birthdays"""
    from modules.life.contact_manager import ContactManager

    manager = ContactManager()
    upcoming = manager.get_upcoming_birthdays(days)

    if not upcoming:
        click.echo(f"No birthdays in the next {days} days.")
        return

    click.echo(f"\nUpcoming Birthdays (next {days} days):")
    click.echo("-" * 40)
    for c in upcoming:
        name = manager.full_name(c)
        click.echo(f"  {c['days_until_birthday']:>3}d - {name} ({c['birthday']})")


@contacts.command("touch")
@click.argument("contact_id", type=int)
def contacts_touch(contact_id):
    """Record that you contacted someone today"""
    from modules.life.contact_manager import ContactManager

    manager = ContactManager()
    contact = manager.get(contact_id)
    if not contact:
        click.echo(f"Error: Contact #{contact_id} not found.")
        return

    manager.record_contact(contact_id)
    click.echo(f"Recorded contact with {manager.full_name(contact)}")


# --- Habits ---
@life.group()
def habits():
    """Habit tracking"""
    pass


@habits.command("list")
def habits_list():
    """List all habits"""
    from modules.life.habit_tracker import HabitTracker

    tracker = HabitTracker()
    habit_list = tracker.list_habits()

    if not habit_list:
        click.echo("No habits defined. Add one with: life habits add <name>")
        return

    click.echo(f"\n{'ID':<4} {'Habit':<30} {'Frequency':<10} {'Target'}")
    click.echo("-" * 60)

    for h in habit_list:
        click.echo(f"{h['id']:<4} {h['name']:<30} {h['frequency']:<10} {h['target_count']}")


@habits.command("add")
@click.argument("name")
@click.option("--description", "-d", default="", help="Habit description")
@click.option("--frequency", "-f", type=click.Choice(["daily", "weekly", "weekdays", "weekends"]), default="daily")
@click.option("--target", "-t", type=int, default=1, help="Times per day")
def habits_add(name, description, frequency, target):
    """Add a new habit to track"""
    from modules.life.habit_tracker import HabitTracker, HabitFrequency

    tracker = HabitTracker()
    habit_id = tracker.add_habit(
        name=name,
        description=description,
        frequency=HabitFrequency(frequency),
        target_count=target
    )
    click.echo(f"Created habit #{habit_id}: {name}")


@habits.command("done")
@click.argument("habit_id", type=int)
@click.option("--count", "-c", type=int, default=1, help="Number of completions")
def habits_done(habit_id, count):
    """Mark a habit as done for today"""
    from modules.life.habit_tracker import HabitTracker

    tracker = HabitTracker()
    habit = tracker.get_habit(habit_id)
    if not habit:
        click.echo(f"Error: Habit #{habit_id} not found.")
        return

    tracker.complete_habit(habit_id, count=count)
    streak = tracker.get_streak(habit_id)
    click.echo(f"Completed '{habit['name']}' - Streak: {streak} days")


@habits.command("today")
def habits_today():
    """Show today's habit status"""
    from modules.life.habit_tracker import HabitTracker

    tracker = HabitTracker()
    status = tracker.get_today_status()

    if not status:
        click.echo("No habits defined.")
        return

    click.echo(f"\nToday's Habits ({date.today()}):")
    click.echo("-" * 50)

    for h in status:
        done = "[x]" if h["completed_today"] else "[ ]"
        streak = f"({h['current_streak']}d streak)" if h["current_streak"] > 0 else ""
        click.echo(f"  {done} #{h['id']} {h['name']} {streak}")


@habits.command("streak")
@click.argument("habit_id", type=int)
def habits_streak(habit_id):
    """Show streak info for a habit"""
    from modules.life.habit_tracker import HabitTracker

    tracker = HabitTracker()
    habit = tracker.get_habit(habit_id)
    if not habit:
        click.echo(f"Error: Habit #{habit_id} not found.")
        return

    current = tracker.get_streak(habit_id)
    longest = tracker.get_longest_streak(habit_id)
    rate = tracker.get_completion_rate(habit_id, 30)

    click.echo(f"\n{habit['name']}")
    click.echo("-" * 30)
    click.echo(f"Current Streak:  {current} days")
    click.echo(f"Longest Streak:  {longest} days")
    click.echo(f"30-day Rate:     {rate*100:.1f}%")


# --- Goals ---
@life.group()
def goals():
    """Goal tracking (Event-sourced)"""
    pass


@goals.command("define")
@click.argument("title")
@click.option("--description", "-d", default="", help="Goal description")
def goals_define(title, description):
    """Define a new goal"""
    from modules.life.goal_manager import GoalManager

    manager = GoalManager()
    goal_id = manager.define(title, description)
    click.echo(f"Defined goal #{goal_id}: {title}")


@goals.command("set-target")
@click.argument("goal_id", type=int)
@click.argument("target_date")
@click.option("--value", "-v", type=int, default=100, help="Target value (default 100)")
def goals_set_target(goal_id, target_date, value):
    """Set target date for a goal"""
    from modules.life.goal_manager import GoalManager
    from modules.core.utils import parse_date

    manager = GoalManager()
    try:
        parsed_date = parse_date(target_date)
    except ValueError:
        click.echo(f"Error: Invalid date format: {target_date}")
        return

    if manager.set_target(goal_id, parsed_date, value):
        click.echo(f"Set target for goal #{goal_id}: {target_date} (value={value})")
    else:
        click.echo(f"Error: Goal #{goal_id} not found.")


@goals.command("update")
@click.argument("goal_id", type=int)
@click.argument("current_value", type=int)
@click.option("--note", "-n", default="", help="Progress note")
def goals_update(goal_id, current_value, note):
    """Update progress on a goal"""
    from modules.life.goal_manager import GoalManager

    manager = GoalManager()
    if manager.update_progress(goal_id, current_value, note):
        progress = manager.progress(goal_id)
        click.echo(f"Updated goal #{goal_id}: {progress['percentage']:.1f}% complete")
    else:
        click.echo(f"Error: Goal #{goal_id} not found.")


@goals.command("list")
def goals_list():
    """List all goals"""
    from modules.life.goal_manager import GoalManager

    manager = GoalManager()
    goal_list = manager.list_goals()

    if not goal_list:
        click.echo("No goals defined. Add one with: life goals define <title>")
        return

    click.echo(f"\n{'ID':<4} {'Title':<30} {'Progress':<10} {'Target'}")
    click.echo("-" * 65)

    for g in goal_list:
        progress = manager.progress(g['id'])
        pct = f"{progress['percentage']:.0f}%" if progress else "-"
        target = g['target_date'] or "-"
        title = g['title'][:29] + "..." if len(g['title']) > 29 else g['title']
        click.echo(f"{g['id']:<4} {title:<30} {pct:<10} {target}")


@goals.command("progress")
@click.argument("goal_id", type=int)
def goals_progress(goal_id):
    """Show progress for a goal"""
    from modules.life.goal_manager import GoalManager

    manager = GoalManager()
    progress = manager.progress(goal_id)
    if not progress:
        click.echo(f"Error: Goal #{goal_id} not found.")
        return

    click.echo(f"\nGoal #{goal_id}: {progress['title']}")
    click.echo("-" * 40)
    click.echo(f"Progress:   {progress['current_value']}/{progress['target_value']} ({progress['percentage']:.1f}%)")
    click.echo(f"Target:     {progress['target_date'] or 'Not set'}")
    if progress['days_remaining'] is not None:
        click.echo(f"Remaining:  {progress['days_remaining']} days")
    click.echo(f"Status:     {progress['status'].upper()}")


@goals.command("explain")
@click.argument("goal_id", type=int)
def goals_explain(goal_id):
    """Show event history for a goal (audit trail)"""
    from modules.life.goal_manager import GoalManager

    manager = GoalManager()
    events = manager.explain(goal_id)
    if not events:
        click.echo(f"Error: Goal #{goal_id} not found or has no events.")
        return

    click.echo(f"\nEvent History for Goal #{goal_id}:")
    click.echo("-" * 60)

    for e in events:
        timestamp = e['timestamp'][:19]
        event_type = e['event_type']
        payload_str = ", ".join(f"{k}={v}" for k, v in e['payload'].items())
        click.echo(f"[{timestamp}] {event_type}")
        if payload_str:
            click.echo(f"    {payload_str}")


# ============================================================================
# KNOWLEDGE COMMANDS
# ============================================================================

@cli.group()
def note():
    """Note management (Event-sourced)"""
    pass


@note.command("create")
@click.argument("title")
@click.option("--content", "-c", default="", help="Note content")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
def note_create(title, content, tags):
    """Create a new note"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    note_id = manager.create(title, content, tag_list)
    click.echo(f"Created note #{note_id}: {title}")


@note.command("edit")
@click.argument("note_id", type=int)
@click.option("--title", "-t", default=None, help="New title")
@click.option("--content", "-c", default=None, help="New content")
def note_edit(note_id, title, content):
    """Edit an existing note"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    if title is None and content is None:
        click.echo("Error: Provide --title or --content to update")
        return

    if manager.update(note_id, title=title, content=content):
        click.echo(f"Updated note #{note_id}")
    else:
        click.echo(f"Error: Note #{note_id} not found or archived")


@note.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--archived", "-a", is_flag=True, help="Include archived notes")
def note_list(tag, archived):
    """List all notes"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    notes = manager.list_notes(include_archived=archived, tag=tag)

    if not notes:
        click.echo("No notes found. Create one with: note create <title>")
        return

    click.echo(f"\n{'ID':<4} {'Title':<35} {'Tags':<20} {'Status'}")
    click.echo("-" * 70)

    for n in notes:
        title = n['title'][:34] + "..." if len(n['title']) > 34 else n['title']
        tags = ", ".join(n['tags'][:3]) if n['tags'] else "-"
        if len(n['tags']) > 3:
            tags += "..."
        status = "ARCHIVED" if n['archived'] else "active"
        click.echo(f"{n['id']:<4} {title:<35} {tags:<20} {status}")

    click.echo(f"\nTotal: {len(notes)} note(s)")


@note.command("show")
@click.argument("note_id", type=int)
def note_show(note_id):
    """Show note details"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    note = manager.get(note_id)
    if not note:
        click.echo(f"Error: Note #{note_id} not found")
        return

    click.echo(f"\nNote #{note['id']}: {note['title']}")
    click.echo("-" * 50)
    if note['tags']:
        click.echo(f"Tags: {', '.join(note['tags'])}")
    click.echo(f"Status: {'ARCHIVED' if note['archived'] else 'active'}")
    click.echo(f"Created: {note['created_at'][:19] if note['created_at'] else '-'}")
    if note['updated_at']:
        click.echo(f"Updated: {note['updated_at'][:19]}")
    click.echo("")
    if note['content']:
        click.echo(note['content'])
    else:
        click.echo("(no content)")


@note.command("search")
@click.argument("query")
@click.option("--archived", "-a", is_flag=True, help="Include archived notes")
def note_search(query, archived):
    """Search notes by title and content"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    results = manager.search(query, include_archived=archived)

    if not results:
        click.echo(f"No notes found matching '{query}'")
        return

    click.echo(f"\nSearch results for '{query}':")
    click.echo("-" * 50)

    for n in results:
        title = n['title'][:40] + "..." if len(n['title']) > 40 else n['title']
        click.echo(f"  #{n['id']} {title}")

    click.echo(f"\nFound: {len(results)} note(s)")


@note.command("tag")
@click.argument("note_id", type=int)
@click.argument("tags")
def note_tag(note_id, tags):
    """Set tags on a note (comma-separated)"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    if manager.tag(note_id, tag_list):
        click.echo(f"Tagged note #{note_id} with: {', '.join(tag_list)}")
    else:
        click.echo(f"Error: Note #{note_id} not found or archived")


@note.command("archive")
@click.argument("note_id", type=int)
def note_archive(note_id):
    """Archive a note (soft delete)"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    if manager.archive(note_id):
        click.echo(f"Archived note #{note_id}")
    else:
        click.echo(f"Error: Note #{note_id} not found or already archived")


@note.command("tags")
def note_tags():
    """List all unique tags"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    tags = manager.get_tags()

    if not tags:
        click.echo("No tags found")
        return

    click.echo("\nAll tags:")
    for tag in tags:
        click.echo(f"  - {tag}")


@note.command("explain")
@click.argument("note_id", type=int)
def note_explain(note_id):
    """Show event history for a note (audit trail)"""
    from modules.knowledge.note_manager import NoteManager

    manager = NoteManager()
    events = manager.explain(note_id)
    if not events:
        click.echo(f"Error: Note #{note_id} not found or has no events")
        return

    click.echo(f"\nEvent History for Note #{note_id}:")
    click.echo("-" * 60)

    for e in events:
        timestamp = e['timestamp'][:19]
        event_type = e['event_type']
        payload = e['payload']
        # Truncate content if present
        if 'content' in payload:
            content = payload['content']
            payload['content'] = content[:50] + "..." if len(content) > 50 else content
        payload_str = ", ".join(f"{k}={v}" for k, v in payload.items())
        click.echo(f"[{timestamp}] {event_type}")
        if payload_str:
            click.echo(f"    {payload_str}")


# ============================================================================
# CONTENT COMMANDS
# ============================================================================

@cli.group()
def idea():
    """Content idea management (Event-sourced)"""
    pass


@idea.command("add")
@click.argument("title")
@click.option("--description", "-d", default="", help="Idea description")
@click.option("--platform", "-p", type=click.Choice(["youtube", "podcast", "blog", "social", "other"]), default="other")
@click.option("--priority", "-r", type=int, default=3, help="Priority 1-5 (1=highest)")
def idea_add(title, description, platform, priority):
    """Add a new content idea"""
    from modules.content.idea_bank import IdeaBank, Platform

    bank = IdeaBank()
    platform_enum = Platform(platform)
    idea_id = bank.add(title, description, platform_enum, priority)
    click.echo(f"Added idea #{idea_id}: {title} [{platform}]")


@idea.command("list")
@click.option("--platform", "-p", type=click.Choice(["youtube", "podcast", "blog", "social", "other"]), default=None)
@click.option("--status", "-s", type=click.Choice(["draft", "planned", "in_progress", "published", "archived"]), default=None)
@click.option("--archived", "-a", is_flag=True, help="Include archived ideas")
def idea_list(platform, status, archived):
    """List content ideas"""
    from modules.content.idea_bank import IdeaBank, Platform, IdeaStatus

    bank = IdeaBank()
    platform_filter = Platform(platform) if platform else None
    status_filter = IdeaStatus(status) if status else None
    ideas = bank.list_ideas(platform=platform_filter, status=status_filter, include_archived=archived)

    if not ideas:
        click.echo("No ideas found. Add one with: idea add <title>")
        return

    click.echo(f"\n{'ID':<4} {'P':<2} {'Title':<30} {'Platform':<10} {'Status'}")
    click.echo("-" * 65)

    for i in ideas:
        title = i['title'][:29] + "..." if len(i['title']) > 29 else i['title']
        click.echo(f"{i['id']:<4} {i['priority']:<2} {title:<30} {i['platform']:<10} {i['status']}")

    click.echo(f"\nTotal: {len(ideas)} idea(s)")


@idea.command("show")
@click.argument("idea_id", type=int)
def idea_show(idea_id):
    """Show idea details"""
    from modules.content.idea_bank import IdeaBank

    bank = IdeaBank()
    idea = bank.get(idea_id)
    if not idea:
        click.echo(f"Error: Idea #{idea_id} not found")
        return

    click.echo(f"\nIdea #{idea['id']}: {idea['title']}")
    click.echo("-" * 50)
    click.echo(f"Platform: {idea['platform']}")
    click.echo(f"Status:   {idea['status']}")
    click.echo(f"Priority: {idea['priority']}")
    click.echo(f"Created:  {idea['created_at'][:19] if idea['created_at'] else '-'}")
    if idea['updated_at']:
        click.echo(f"Updated:  {idea['updated_at'][:19]}")
    click.echo("")
    if idea['description']:
        click.echo(idea['description'])
    else:
        click.echo("(no description)")


@idea.command("update")
@click.argument("idea_id", type=int)
@click.option("--title", "-t", default=None, help="New title")
@click.option("--description", "-d", default=None, help="New description")
@click.option("--platform", "-p", type=click.Choice(["youtube", "podcast", "blog", "social", "other"]), default=None)
def idea_update(idea_id, title, description, platform):
    """Update an idea's details"""
    from modules.content.idea_bank import IdeaBank, Platform

    bank = IdeaBank()
    if title is None and description is None and platform is None:
        click.echo("Error: Provide --title, --description, or --platform to update")
        return

    platform_enum = Platform(platform) if platform else None
    if bank.update(idea_id, title=title, description=description, platform=platform_enum):
        click.echo(f"Updated idea #{idea_id}")
    else:
        click.echo(f"Error: Idea #{idea_id} not found or archived")


@idea.command("status")
@click.argument("idea_id", type=int)
@click.argument("new_status", type=click.Choice(["draft", "planned", "in_progress", "published", "archived"]))
def idea_status(idea_id, new_status):
    """Change an idea's status"""
    from modules.content.idea_bank import IdeaBank, IdeaStatus

    bank = IdeaBank()
    status_enum = IdeaStatus(new_status)
    if bank.set_status(idea_id, status_enum):
        click.echo(f"Idea #{idea_id} status changed to: {new_status}")
    else:
        click.echo(f"Error: Idea #{idea_id} not found")


@idea.command("prioritize")
@click.argument("idea_id", type=int)
@click.argument("priority", type=int)
def idea_prioritize(idea_id, priority):
    """Set an idea's priority (1-5, 1=highest)"""
    from modules.content.idea_bank import IdeaBank

    bank = IdeaBank()
    if bank.prioritize(idea_id, priority):
        click.echo(f"Idea #{idea_id} priority set to: {priority}")
    else:
        click.echo(f"Error: Idea #{idea_id} not found or archived")


@idea.command("explain")
@click.argument("idea_id", type=int)
def idea_explain(idea_id):
    """Show event history for an idea (audit trail)"""
    from modules.content.idea_bank import IdeaBank

    bank = IdeaBank()
    events = bank.explain(idea_id)
    if not events:
        click.echo(f"Error: Idea #{idea_id} not found or has no events")
        return

    click.echo(f"\nEvent History for Idea #{idea_id}:")
    click.echo("-" * 60)

    for e in events:
        timestamp = e['timestamp'][:19]
        event_type = e['event_type']
        payload = e['payload']
        # Truncate description if present
        if 'description' in payload:
            desc = payload['description']
            payload['description'] = desc[:40] + "..." if len(desc) > 40 else desc
        payload_str = ", ".join(f"{k}={v}" for k, v in payload.items())
        click.echo(f"[{timestamp}] {event_type}")
        if payload_str:
            click.echo(f"    {payload_str}")


# ============================================================================
# FINANCE COMMANDS
# ============================================================================

@cli.group()
def finance():
    """Financial management commands"""
    pass


@finance.command("portfolio")
@click.option("--account", "-a", help="Filter by account")
def finance_portfolio(account):
    """View portfolio summary"""
    from modules.financial.portfolio_tracker import PortfolioTracker

    tracker = PortfolioTracker()
    summary = tracker.get_portfolio_summary(account)

    click.echo(f"\n=== Portfolio Summary ===")
    click.echo(f"Holdings: {summary['holdings_count']}")
    click.echo(f"Total Cost:  ${summary['total_cost']:,.2f}")
    click.echo(f"Total Value: ${summary['total_value']:,.2f}")

    gl = summary['total_gain_loss']
    gl_pct = summary['total_gain_loss_percent']
    sign = "+" if gl >= 0 else ""
    click.echo(f"Gain/Loss:   {sign}${gl:,.2f} ({sign}{gl_pct:.2f}%)")

    if summary['holdings']:
        click.echo(f"\n{'Symbol':<8} {'Shares':<10} {'Avg Cost':<10} {'Current':<10} {'G/L %'}")
        click.echo("-" * 55)
        for h in summary['holdings']:
            if 'current_price' in h:
                gl_pct = h.get('gain_loss_percent', 0)
                click.echo(f"{h['symbol']:<8} {h['shares']:<10.2f} ${h['cost_basis']:<9.2f} ${h['current_price']:<9.2f} {gl_pct:+.2f}%")


@finance.command("buy")
@click.argument("symbol")
@click.argument("shares", type=float)
@click.argument("price", type=float)
@click.option("--account", "-a", default="default", help="Account name")
def finance_buy(symbol, shares, price, account):
    """Record a stock purchase"""
    from modules.financial.portfolio_tracker import PortfolioTracker

    tracker = PortfolioTracker()
    transaction_id = tracker.buy(symbol=symbol, shares=shares, price=price, account=account)
    click.echo(f"Recorded purchase: {shares} shares of {symbol.upper()} @ ${price:.2f}")


@finance.command("sell")
@click.argument("symbol")
@click.argument("shares", type=float)
@click.argument("price", type=float)
@click.option("--account", "-a", default="default", help="Account name")
def finance_sell(symbol, shares, price, account):
    """Record a stock sale"""
    from modules.financial.portfolio_tracker import PortfolioTracker

    tracker = PortfolioTracker()
    result = tracker.sell(symbol=symbol, shares=shares, price=price, account=account)
    if result:
        click.echo(f"Recorded sale: {shares} shares of {symbol.upper()} @ ${price:.2f}")
    else:
        click.echo(f"Error: Insufficient shares of {symbol.upper()}")


@finance.command("watchlist")
def finance_watchlist():
    """View stock watchlist"""
    from modules.financial.stock_analyzer import StockAnalyzer

    analyzer = StockAnalyzer()
    watchlist = analyzer.get_watchlist()

    if not watchlist:
        click.echo("Watchlist is empty. Add with: finance watch <symbol>")
        return

    click.echo(f"\n{'Symbol':<8} {'Latest':<10} {'Target':<10} {'Notes'}")
    click.echo("-" * 50)

    for item in watchlist:
        latest = f"${item.get('latest_price', 0):.2f}" if item.get('latest_price') else "-"
        target = f"${item['target_price']:.2f}" if item.get('target_price') else "-"
        notes = item.get('notes', '')[:20] or "-"
        click.echo(f"{item['symbol']:<8} {latest:<10} {target:<10} {notes}")


@finance.command("watch")
@click.argument("symbol")
@click.option("--target", "-t", type=float, help="Target price")
@click.option("--notes", "-n", default="", help="Notes")
def finance_watch(symbol, target, notes):
    """Add a stock to watchlist"""
    from modules.financial.stock_analyzer import StockAnalyzer

    analyzer = StockAnalyzer()
    if analyzer.add_to_watchlist(symbol, target, notes):
        click.echo(f"Added {symbol.upper()} to watchlist")
    else:
        click.echo(f"Error: Could not add {symbol.upper()}")


@finance.command("unwatch")
@click.argument("symbol")
def finance_unwatch(symbol):
    """Remove a stock from watchlist"""
    from modules.financial.stock_analyzer import StockAnalyzer

    analyzer = StockAnalyzer()
    if analyzer.remove_from_watchlist(symbol):
        click.echo(f"Removed {symbol.upper()} from watchlist")
    else:
        click.echo(f"Error: {symbol.upper()} not in watchlist")


# ============================================================================
# STATUS COMMAND
# ============================================================================

@cli.command()
def status():
    """Show system status and summary"""
    from modules.life.task_tracker import TaskTracker, TaskStatus
    from modules.life.habit_tracker import HabitTracker
    from modules.life.contact_manager import ContactManager

    click.echo("\n=== Atlas Personal OS Status ===")
    click.echo(f"Version: {__version__}")
    click.echo(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Tasks
    tracker = TaskTracker()
    pending = tracker.count(TaskStatus.PENDING)
    overdue = len(tracker.get_overdue())
    due_today = len(tracker.get_due_today())

    click.echo("\nTasks:")
    click.echo(f"  Pending: {pending}")
    if overdue:
        click.echo(f"  OVERDUE: {overdue}")
    if due_today:
        click.echo(f"  Due Today: {due_today}")

    # Habits
    habit_tracker = HabitTracker()
    today_status = habit_tracker.get_today_status()
    if today_status:
        completed = sum(1 for h in today_status if h["completed_today"])
        click.echo(f"\nHabits: {completed}/{len(today_status)} completed today")

    # Contacts
    contact_mgr = ContactManager()
    birthdays = contact_mgr.get_upcoming_birthdays(7)
    if birthdays:
        click.echo(f"\nUpcoming Birthdays: {len(birthdays)} this week")


# ============================================================================
# VIDEO COMMANDS (CON-001)
# ============================================================================

@cli.group()
def video():
    """YouTube video planning (Event-sourced)"""
    pass


@video.command("plan")
@click.argument("title")
@click.option("--description", "-d", default="", help="Video description")
@click.option("--idea", "-i", type=int, help="Link to idea ID")
@click.option("--duration", "-t", type=int, help="Estimated duration in minutes")
@click.option("--tags", default="", help="Comma-separated tags")
def video_plan(title, description, idea, duration, tags):
    """Plan a new video"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    video_id = planner.plan(
        title=title,
        description=description,
        idea_id=idea,
        duration_estimate=duration,
        tags=tags
    )
    click.echo(f"Video planned with ID: {video_id}")


@video.command("list")
@click.option("--status", "-s", type=click.Choice(["planned", "scripted", "recorded", "edited", "published"]))
def video_list(status):
    """List all videos"""
    from modules.content.video_planner import VideoPlanner, VideoStatus

    planner = VideoPlanner()
    status_filter = VideoStatus(status) if status else None
    videos = planner.list_videos(status=status_filter)

    if not videos:
        click.echo("No videos found.")
        return

    click.echo(f"\n{'ID':<4} {'Status':<10} {'Duration':<10} {'Title'}")
    click.echo("-" * 60)

    for v in videos:
        duration = f"{v['duration_estimate']}min" if v['duration_estimate'] else "-"
        title = v['title'][:35] + "..." if len(v['title']) > 35 else v['title']
        click.echo(f"{v['id']:<4} {v['status']:<10} {duration:<10} {title}")

    click.echo(f"\nTotal: {len(videos)} video(s)")


@video.command("show")
@click.argument("video_id", type=int)
def video_show(video_id):
    """Show video details"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    video = planner.get(video_id)

    if not video:
        click.echo(f"Video {video_id} not found.")
        return

    click.echo(f"\nVideo #{video['id']}")
    click.echo(f"Title: {video['title']}")
    click.echo(f"Status: {video['status']}")
    click.echo(f"Description: {video['description'] or '-'}")
    click.echo(f"Duration: {video['duration_estimate'] or '-'} minutes")
    click.echo(f"Tags: {video['tags'] or '-'}")
    if video['idea_id']:
        click.echo(f"Linked Idea: #{video['idea_id']}")
    if video['script_completed_at']:
        click.echo(f"Scripted: {video['script_completed_at']}")
    if video['recorded_at']:
        click.echo(f"Recorded: {video['recorded_at']}")
    if video['edited_at']:
        click.echo(f"Edited: {video['edited_at']}")
    if video['published_at']:
        click.echo(f"Published: {video['published_at']}")
        click.echo(f"URL: {video['publish_url'] or '-'}")


@video.command("script")
@click.argument("video_id", type=int)
def video_script(video_id):
    """Mark video script as completed"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    if planner.mark_scripted(video_id):
        click.echo(f"Video {video_id} marked as scripted.")
    else:
        click.echo(f"Cannot mark video {video_id} as scripted. Check status.")


@video.command("record")
@click.argument("video_id", type=int)
def video_record(video_id):
    """Mark video as recorded"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    if planner.mark_recorded(video_id):
        click.echo(f"Video {video_id} marked as recorded.")
    else:
        click.echo(f"Cannot mark video {video_id} as recorded. Check status.")


@video.command("edit")
@click.argument("video_id", type=int)
def video_edit(video_id):
    """Mark video as edited"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    if planner.mark_edited(video_id):
        click.echo(f"Video {video_id} marked as edited.")
    else:
        click.echo(f"Cannot mark video {video_id} as edited. Check status.")


@video.command("publish")
@click.argument("video_id", type=int)
@click.option("--url", "-u", default="", help="Published video URL")
def video_publish(video_id, url):
    """Mark video as published"""
    from modules.content.video_planner import VideoPlanner

    planner = VideoPlanner()
    if planner.mark_published(video_id, url=url):
        click.echo(f"Video {video_id} marked as published.")
    else:
        click.echo(f"Cannot mark video {video_id} as published. Check status.")


@video.command("explain")
@click.argument("video_id", type=int)
def video_explain(video_id):
    """Show video event history (audit trail)"""
    from modules.content.video_planner import VideoPlanner
    import json

    planner = VideoPlanner()
    events = planner.explain(video_id)

    if not events:
        click.echo(f"No events found for video {video_id}.")
        return

    click.echo(f"\nEvent history for video #{video_id}:")
    click.echo("-" * 60)

    for event in events:
        payload = event['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)
        click.echo(f"\n[{event['timestamp']}] {event['event_type']}")
        for k, v in payload.items():
            if v is not None:
                click.echo(f"  {k}: {v}")


# ============================================================================
# UI COMMAND
# ============================================================================

@cli.command("ui")
def launch_ui():
    """Launch the Atlas desktop UI (Tkinter)"""
    from modules.ui.app import launch
    click.echo("Launching Atlas Desktop UI...")
    launch()


if __name__ == "__main__":
    cli()
