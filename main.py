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
# PUBLICATION COMMANDS (CAR-001)
# ============================================================================

@cli.group()
def pub():
    """Publication tracking (Event-sourced)"""
    pass


@pub.command("add")
@click.argument("title")
@click.option("--authors", "-a", default="", help="Comma-separated author names")
@click.option("--venue", "-v", type=click.Choice(["journal", "conference", "preprint", "book", "other"]), default="other")
@click.option("--abstract", default="", help="Publication abstract")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
def pub_add(title, authors, venue, abstract, tags):
    """Add a new publication"""
    from modules.career.publication_tracker import PublicationTracker, VenueType

    tracker = PublicationTracker()
    pub_id = tracker.add(
        title=title,
        authors=authors,
        venue=VenueType(venue),
        abstract=abstract,
        tags=tags
    )
    click.echo(f"Publication added with ID: {pub_id}")


@pub.command("list")
@click.option("--status", "-s", type=click.Choice(["draft", "submitted", "accepted", "rejected", "published"]))
@click.option("--venue", "-v", type=click.Choice(["journal", "conference", "preprint", "book", "other"]))
def pub_list(status, venue):
    """List all publications"""
    from modules.career.publication_tracker import PublicationTracker, PubStatus, VenueType

    tracker = PublicationTracker()
    status_filter = PubStatus(status) if status else None
    venue_filter = VenueType(venue) if venue else None
    pubs = tracker.list_publications(status=status_filter, venue=venue_filter)

    if not pubs:
        click.echo("No publications found.")
        return

    click.echo(f"\n{'ID':<4} {'Status':<10} {'Venue':<12} {'Title'}")
    click.echo("-" * 70)

    for p in pubs:
        title = p['title'][:40] + "..." if len(p['title']) > 40 else p['title']
        click.echo(f"{p['id']:<4} {p['status']:<10} {p['venue']:<12} {title}")

    click.echo(f"\nTotal: {len(pubs)} publication(s)")


@pub.command("show")
@click.argument("pub_id", type=int)
def pub_show(pub_id):
    """Show publication details"""
    from modules.career.publication_tracker import PublicationTracker

    tracker = PublicationTracker()
    pub = tracker.get(pub_id)

    if not pub:
        click.echo(f"Publication {pub_id} not found.")
        return

    click.echo(f"\nPublication #{pub['id']}")
    click.echo(f"Title: {pub['title']}")
    click.echo(f"Authors: {pub['authors'] or '-'}")
    click.echo(f"Venue: {pub['venue']}")
    click.echo(f"Status: {pub['status']}")
    click.echo(f"Abstract: {pub['abstract'][:100] + '...' if len(pub['abstract']) > 100 else pub['abstract'] or '-'}")
    click.echo(f"Tags: {pub['tags'] or '-'}")
    if pub['submission_date']:
        click.echo(f"Submitted: {pub['submission_date']}")
    if pub['acceptance_date']:
        click.echo(f"Accepted: {pub['acceptance_date']}")
    if pub['rejection_date']:
        click.echo(f"Rejected: {pub['rejection_date']}")
    if pub['publication_date']:
        click.echo(f"Published: {pub['publication_date']}")
    if pub['doi']:
        click.echo(f"DOI: {pub['doi']}")
    if pub['url']:
        click.echo(f"URL: {pub['url']}")


@pub.command("submit")
@click.argument("pub_id", type=int)
def pub_submit(pub_id):
    """Mark publication as submitted"""
    from modules.career.publication_tracker import PublicationTracker

    tracker = PublicationTracker()
    if tracker.submit(pub_id):
        click.echo(f"Publication {pub_id} marked as submitted.")
    else:
        click.echo(f"Cannot submit publication {pub_id}. Check status (must be draft).")


@pub.command("accept")
@click.argument("pub_id", type=int)
def pub_accept(pub_id):
    """Mark publication as accepted"""
    from modules.career.publication_tracker import PublicationTracker

    tracker = PublicationTracker()
    if tracker.accept(pub_id):
        click.echo(f"Publication {pub_id} marked as accepted.")
    else:
        click.echo(f"Cannot accept publication {pub_id}. Check status (must be submitted).")


@pub.command("reject")
@click.argument("pub_id", type=int)
def pub_reject(pub_id):
    """Mark publication as rejected"""
    from modules.career.publication_tracker import PublicationTracker

    tracker = PublicationTracker()
    if tracker.reject(pub_id):
        click.echo(f"Publication {pub_id} marked as rejected.")
    else:
        click.echo(f"Cannot reject publication {pub_id}. Check status (must be submitted).")


@pub.command("publish")
@click.argument("pub_id", type=int)
@click.option("--doi", "-d", default="", help="DOI identifier")
@click.option("--url", "-u", default="", help="Publication URL")
def pub_publish(pub_id, doi, url):
    """Mark publication as published"""
    from modules.career.publication_tracker import PublicationTracker

    tracker = PublicationTracker()
    if tracker.publish(pub_id, doi=doi, url=url):
        click.echo(f"Publication {pub_id} marked as published.")
    else:
        click.echo(f"Cannot publish publication {pub_id}. Check status (must be accepted).")


@pub.command("explain")
@click.argument("pub_id", type=int)
def pub_explain(pub_id):
    """Show publication event history (audit trail)"""
    from modules.career.publication_tracker import PublicationTracker
    import json

    tracker = PublicationTracker()
    events = tracker.explain(pub_id)

    if not events:
        click.echo(f"No events found for publication {pub_id}.")
        return

    click.echo(f"\nEvent history for publication #{pub_id}:")
    click.echo("-" * 60)

    for event in events:
        payload = event['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)
        click.echo(f"\n[{event['timestamp']}] {event['event_type']}")
        for k, v in payload.items():
            if v:
                click.echo(f"  {k}: {v}")


# ============================================================================
# CV COMMANDS (CAR-002)
# ============================================================================

@cli.group()
def cv():
    """CV/resume management (Event-sourced)"""
    pass


@cv.command("add")
@click.argument("entry_type", type=click.Choice(["experience", "education", "skill", "project", "certification"]))
@click.argument("title")
@click.option("--org", "-o", "organization", default="", help="Organization or institution")
@click.option("--description", "-d", default="", help="Entry description")
@click.option("--start", default="", help="Start date (YYYY-MM-DD)")
@click.option("--end", default="", help="End date (YYYY-MM-DD)")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
@click.option("--highlight", "-H", "highlights", multiple=True, help="Highlight (repeatable)")
def cv_add(entry_type, title, organization, description, start, end, tags, highlights):
    """Add a CV entry"""
    from modules.career.cv_manager import CVManager, EntryType

    manager = CVManager()
    try:
        entry_id = manager.add(
            entry_type=EntryType(entry_type),
            title=title,
            organization=organization,
            description=description,
            start_date=start,
            end_date=end,
            tags=tags,
            highlights=list(highlights)
        )
    except ValueError as exc:
        click.echo(f"Error: {exc}")
        return

    click.echo(f"Added CV entry #{entry_id}: {title}")


@cv.command("update")
@click.argument("entry_id", type=int)
@click.option("--type", "entry_type", type=click.Choice(["experience", "education", "skill", "project", "certification"]))
@click.option("--title", default=None, help="Entry title")
@click.option("--org", "-o", "organization", default=None, help="Organization or institution")
@click.option("--description", "-d", default=None, help="Entry description")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end", default=None, help="End date (YYYY-MM-DD)")
@click.option("--tags", "-t", default=None, help="Comma-separated tags")
@click.option("--highlight", "-H", "highlights", multiple=True, help="Highlight (repeatable)")
def cv_update(entry_id, entry_type, title, organization, description, start, end, tags, highlights):
    """Update a CV entry"""
    from modules.career.cv_manager import CVManager, EntryType

    manager = CVManager()
    payload = {
        "entry_type": EntryType(entry_type) if entry_type else None,
        "title": title,
        "organization": organization,
        "description": description,
        "start_date": start,
        "end_date": end,
        "tags": tags,
        "highlights": list(highlights) if highlights else None,
    }
    try:
        updated = manager.update(entry_id, **payload)
    except ValueError as exc:
        click.echo(f"Error: {exc}")
        return

    if updated:
        click.echo(f"Updated CV entry #{entry_id}")
    else:
        click.echo(f"Error: CV entry #{entry_id} not found or archived")


@cv.command("list")
@click.option("--type", "entry_type", type=click.Choice(["experience", "education", "skill", "project", "certification"]))
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--query", "-q", default=None, help="Search text")
@click.option("--start-after", default=None, help="Filter entries ending after date")
@click.option("--end-before", default=None, help="Filter entries starting before date")
@click.option("--archived", "-a", is_flag=True, help="Include archived entries")
def cv_list(entry_type, tag, query, start_after, end_before, archived):
    """List CV entries"""
    from modules.career.cv_manager import CVManager, EntryType

    manager = CVManager()
    entries = manager.list_entries(
        entry_type=EntryType(entry_type) if entry_type else None,
        tag=tag,
        query=query,
        start_after=start_after,
        end_before=end_before,
        include_archived=archived,
        limit=200
    )

    if not entries:
        click.echo("No CV entries found.")
        return

    click.echo(f"\n{'ID':<4} {'Type':<13} {'Dates':<23} {'Title'}")
    click.echo("-" * 75)

    for entry in entries:
        dates = "-"
        if entry["start_date"] or entry["end_date"]:
            dates = f"{entry['start_date'] or '??'} → {entry['end_date'] or 'present'}"
        title = entry["title"][:40] + "..." if len(entry["title"]) > 40 else entry["title"]
        click.echo(f"{entry['id']:<4} {entry['entry_type']:<13} {dates:<23} {title}")

    click.echo(f"\nTotal: {len(entries)} entry(s)")


@cv.command("show")
@click.argument("entry_id", type=int)
def cv_show(entry_id):
    """Show CV entry details"""
    from modules.career.cv_manager import CVManager

    manager = CVManager()
    entry = manager.get(entry_id)

    if not entry:
        click.echo(f"CV entry {entry_id} not found.")
        return

    click.echo(f"\nEntry #{entry['id']}")
    click.echo("-" * 40)
    click.echo(f"Type:        {entry['entry_type']}")
    click.echo(f"Title:       {entry['title']}")
    click.echo(f"Organization:{' ' if entry['organization'] else ' -'}{entry['organization'] or ''}")
    click.echo(f"Dates:       {entry['start_date'] or '-'} → {entry['end_date'] or 'present'}")
    click.echo(f"Tags:        {entry['tags'] or '-'}")
    click.echo(f"Description: {entry['description'] or '-'}")
    if entry["highlights"]:
        click.echo("Highlights:")
        for line in entry["highlights"].splitlines():
            click.echo(f"  - {line}")
    click.echo(f"Status:      {'ARCHIVED' if entry['archived'] else 'active'}")


@cv.command("archive")
@click.argument("entry_id", type=int)
def cv_archive(entry_id):
    """Archive a CV entry"""
    from modules.career.cv_manager import CVManager

    manager = CVManager()
    if manager.archive(entry_id):
        click.echo(f"Archived CV entry #{entry_id}")
    else:
        click.echo(f"Error: CV entry #{entry_id} not found or already archived")


@cv.command("export")
@click.option("--format", "-f", "export_format", type=click.Choice(["text", "markdown"]), default="text")
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), default=None)
@click.option("--type", "entry_type", type=click.Choice(["experience", "education", "skill", "project", "certification"]))
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--query", "-q", default=None, help="Search text")
@click.option("--start-after", default=None, help="Filter entries ending after date")
@click.option("--end-before", default=None, help="Filter entries starting before date")
@click.option("--archived", "-a", is_flag=True, help="Include archived entries")
def cv_export(export_format, output, entry_type, tag, query, start_after, end_before, archived):
    """Export CV entries"""
    from modules.career.cv_manager import CVManager, EntryType
    from modules.career.cv_renderer import render_markdown, render_text

    manager = CVManager()
    entries = manager.list_entries(
        entry_type=EntryType(entry_type) if entry_type else None,
        tag=tag,
        query=query,
        start_after=start_after,
        end_before=end_before,
        include_archived=archived,
        limit=1000
    )
    content = render_markdown(entries) if export_format == "markdown" else render_text(entries)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        click.echo(f"Exported CV to {output}")
        return

    click.echo(content)


@cv.command("explain")
@click.argument("entry_id", type=int)
def cv_explain(entry_id):
    """Show CV entry event history (audit trail)"""
    from modules.career.cv_manager import CVManager
    import json

    manager = CVManager()
    events = manager.explain(entry_id)

    if not events:
        click.echo(f"No events found for CV entry {entry_id}.")
        return

    click.echo(f"\nEvent history for CV entry #{entry_id}:")
    click.echo("-" * 60)

    for event in events:
        payload = event["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        click.echo(f"\n[{event['timestamp']}] {event['event_type']}")
        for k, v in payload.items():
            if v:
                click.echo(f"  {k}: {v}")


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
# PODCAST COMMANDS (CON-002)
# ============================================================================

@cli.group()
def podcast():
    """Podcast episode scheduling (Event-sourced)"""
    pass


@podcast.command("plan")
@click.argument("title")
@click.option("--description", "-d", default="", help="Episode description")
@click.option("--guest", "-g", default="", help="Guest name")
@click.option("--episode", "-e", type=int, help="Episode number")
@click.option("--idea", "-i", type=int, help="Link to idea ID")
@click.option("--duration", "-t", type=int, help="Estimated duration in minutes")
@click.option("--tags", default="", help="Comma-separated tags")
def podcast_plan(title, description, guest, episode, idea, duration, tags):
    """Plan a new podcast episode"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    episode_id = scheduler.plan(
        title=title,
        description=description,
        guest=guest,
        episode_number=episode,
        idea_id=idea,
        duration_estimate=duration,
        tags=tags
    )
    click.echo(f"Episode planned with ID: {episode_id}")


@podcast.command("list")
@click.option("--status", "-s", type=click.Choice(["planned", "outlined", "recorded", "edited", "published"]))
@click.option("--guest", "-g", default=None, help="Filter by guest name")
def podcast_list(status, guest):
    """List all podcast episodes"""
    from modules.content.podcast_scheduler import PodcastScheduler, EpisodeStatus

    scheduler = PodcastScheduler()
    status_filter = EpisodeStatus(status) if status else None
    episodes = scheduler.list_episodes(status=status_filter, guest=guest)

    if not episodes:
        click.echo("No episodes found.")
        return

    click.echo(f"\n{'ID':<4} {'Ep#':<5} {'Status':<10} {'Guest':<15} {'Title'}")
    click.echo("-" * 70)

    for ep in episodes:
        ep_num = str(ep['episode_number']) if ep['episode_number'] else "-"
        guest_name = ep['guest'][:14] + "..." if len(ep['guest']) > 14 else ep['guest'] or "-"
        title = ep['title'][:25] + "..." if len(ep['title']) > 25 else ep['title']
        click.echo(f"{ep['id']:<4} {ep_num:<5} {ep['status']:<10} {guest_name:<15} {title}")

    click.echo(f"\nTotal: {len(episodes)} episode(s)")


@podcast.command("show")
@click.argument("episode_id", type=int)
def podcast_show(episode_id):
    """Show episode details"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    episode = scheduler.get(episode_id)

    if not episode:
        click.echo(f"Episode {episode_id} not found.")
        return

    click.echo(f"\nEpisode #{episode['id']}")
    click.echo(f"Title: {episode['title']}")
    click.echo(f"Episode Number: {episode['episode_number'] or '-'}")
    click.echo(f"Status: {episode['status']}")
    click.echo(f"Guest: {episode['guest'] or '-'}")
    click.echo(f"Description: {episode['description'] or '-'}")
    click.echo(f"Duration: {episode['duration_estimate'] or '-'} minutes")
    click.echo(f"Tags: {episode['tags'] or '-'}")
    if episode['idea_id']:
        click.echo(f"Linked Idea: #{episode['idea_id']}")
    if episode['outlined_at']:
        click.echo(f"Outlined: {episode['outlined_at']}")
    if episode['recorded_at']:
        click.echo(f"Recorded: {episode['recorded_at']}")
    if episode['edited_at']:
        click.echo(f"Edited: {episode['edited_at']}")
    if episode['published_at']:
        click.echo(f"Published: {episode['published_at']}")
        click.echo(f"Audio URL: {episode['audio_url'] or '-'}")


@podcast.command("outline")
@click.argument("episode_id", type=int)
def podcast_outline(episode_id):
    """Mark episode outline as completed"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    if scheduler.mark_outlined(episode_id):
        click.echo(f"Episode {episode_id} marked as outlined.")
    else:
        click.echo(f"Cannot mark episode {episode_id} as outlined. Check status.")


@podcast.command("record")
@click.argument("episode_id", type=int)
def podcast_record(episode_id):
    """Mark episode as recorded"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    if scheduler.mark_recorded(episode_id):
        click.echo(f"Episode {episode_id} marked as recorded.")
    else:
        click.echo(f"Cannot mark episode {episode_id} as recorded. Check status.")


@podcast.command("edit")
@click.argument("episode_id", type=int)
def podcast_edit(episode_id):
    """Mark episode as edited"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    if scheduler.mark_edited(episode_id):
        click.echo(f"Episode {episode_id} marked as edited.")
    else:
        click.echo(f"Cannot mark episode {episode_id} as edited. Check status.")


@podcast.command("publish")
@click.argument("episode_id", type=int)
@click.option("--url", "-u", default="", help="Audio URL")
def podcast_publish(episode_id, url):
    """Mark episode as published"""
    from modules.content.podcast_scheduler import PodcastScheduler

    scheduler = PodcastScheduler()
    if scheduler.mark_published(episode_id, audio_url=url):
        click.echo(f"Episode {episode_id} marked as published.")
    else:
        click.echo(f"Cannot mark episode {episode_id} as published. Check status.")


@podcast.command("explain")
@click.argument("episode_id", type=int)
def podcast_explain(episode_id):
    """Show episode event history (audit trail)"""
    from modules.content.podcast_scheduler import PodcastScheduler
    import json

    scheduler = PodcastScheduler()
    events = scheduler.explain(episode_id)

    if not events:
        click.echo(f"No events found for episode {episode_id}.")
        return

    click.echo(f"\nEvent history for episode #{episode_id}:")
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
# PDF COMMANDS (KNOW-001)
# ============================================================================

@cli.group()
def pdf():
    """PDF library indexing (Event-sourced)"""
    pass


@pdf.command("index")
@click.argument("path")
@click.option("--title", "-t", default="", help="PDF title")
@click.option("--authors", "-a", default="", help="Comma-separated author names")
@click.option("--category", "-c", type=click.Choice(["research", "book", "article", "manual", "other"]), default="other")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--pages", "-p", type=int, default=0, help="Page count")
def pdf_index(path, title, authors, category, tags, pages):
    """Index a PDF file"""
    from modules.knowledge.pdf_indexer import PDFIndexer, PDFCategory

    indexer = PDFIndexer()
    pdf_id = indexer.index(
        file_path=path,
        title=title,
        authors=authors,
        category=PDFCategory(category),
        tags=tags,
        page_count=pages
    )
    click.echo(f"PDF indexed with ID: {pdf_id}")


@pdf.command("list")
@click.option("--category", "-c", type=click.Choice(["research", "book", "article", "manual", "other"]))
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--archived", "-a", is_flag=True, help="Include archived PDFs")
def pdf_list(category, tag, archived):
    """List indexed PDFs"""
    from modules.knowledge.pdf_indexer import PDFIndexer, PDFCategory

    indexer = PDFIndexer()
    category_filter = PDFCategory(category) if category else None
    pdfs = indexer.list_pdfs(category=category_filter, tag=tag, include_archived=archived)

    if not pdfs:
        click.echo("No PDFs found.")
        return

    click.echo(f"\n{'ID':<4} {'Category':<10} {'Pages':<6} {'Title'}")
    click.echo("-" * 65)

    for p in pdfs:
        title = p['title'][:40] + "..." if len(p['title']) > 40 else p['title']
        pages = str(p['page_count']) if p['page_count'] else "-"
        click.echo(f"{p['id']:<4} {p['category']:<10} {pages:<6} {title}")

    click.echo(f"\nTotal: {len(pdfs)} PDF(s)")


@pdf.command("show")
@click.argument("pdf_id", type=int)
def pdf_show(pdf_id):
    """Show PDF details"""
    from modules.knowledge.pdf_indexer import PDFIndexer

    indexer = PDFIndexer()
    pdf = indexer.get(pdf_id)

    if not pdf:
        click.echo(f"PDF {pdf_id} not found.")
        return

    click.echo(f"\nPDF #{pdf['id']}")
    click.echo(f"Title: {pdf['title']}")
    click.echo(f"Authors: {pdf['authors'] or '-'}")
    click.echo(f"Category: {pdf['category']}")
    click.echo(f"File: {pdf['file_path']}")
    click.echo(f"Pages: {pdf['page_count'] or '-'}")
    click.echo(f"Tags: {pdf['tags'] or '-'}")
    click.echo(f"Indexed: {pdf['indexed_at'][:19] if pdf['indexed_at'] else '-'}")
    click.echo(f"Status: {'ARCHIVED' if pdf['archived'] else 'active'}")
    if pdf['notes']:
        click.echo(f"\nNotes:\n{pdf['notes']}")


@pdf.command("search")
@click.argument("query")
@click.option("--archived", "-a", is_flag=True, help="Include archived PDFs")
def pdf_search(query, archived):
    """Search PDFs by title, authors, or notes"""
    from modules.knowledge.pdf_indexer import PDFIndexer

    indexer = PDFIndexer()
    results = indexer.search(query, include_archived=archived)

    if not results:
        click.echo(f"No PDFs found matching '{query}'")
        return

    click.echo(f"\nSearch results for '{query}':")
    click.echo("-" * 50)

    for p in results:
        title = p['title'][:40] + "..." if len(p['title']) > 40 else p['title']
        click.echo(f"  #{p['id']} {title}")

    click.echo(f"\nFound: {len(results)} PDF(s)")


@pdf.command("tag")
@click.argument("pdf_id", type=int)
@click.argument("tags")
def pdf_tag(pdf_id, tags):
    """Set tags on a PDF (comma-separated)"""
    from modules.knowledge.pdf_indexer import PDFIndexer

    indexer = PDFIndexer()
    if indexer.tag(pdf_id, tags):
        click.echo(f"Tagged PDF #{pdf_id} with: {tags}")
    else:
        click.echo(f"Error: PDF #{pdf_id} not found or archived")


@pdf.command("note")
@click.argument("pdf_id", type=int)
@click.argument("note_text")
def pdf_note(pdf_id, note_text):
    """Add a note to a PDF"""
    from modules.knowledge.pdf_indexer import PDFIndexer

    indexer = PDFIndexer()
    if indexer.add_note(pdf_id, note_text):
        click.echo(f"Added note to PDF #{pdf_id}")
    else:
        click.echo(f"Error: PDF #{pdf_id} not found or archived")


@pdf.command("archive")
@click.argument("pdf_id", type=int)
def pdf_archive(pdf_id):
    """Archive a PDF (soft delete)"""
    from modules.knowledge.pdf_indexer import PDFIndexer

    indexer = PDFIndexer()
    if indexer.archive(pdf_id):
        click.echo(f"Archived PDF #{pdf_id}")
    else:
        click.echo(f"Error: PDF #{pdf_id} not found or already archived")


@pdf.command("explain")
@click.argument("pdf_id", type=int)
def pdf_explain(pdf_id):
    """Show PDF event history (audit trail)"""
    from modules.knowledge.pdf_indexer import PDFIndexer
    import json

    indexer = PDFIndexer()
    events = indexer.explain(pdf_id)

    if not events:
        click.echo(f"No events found for PDF {pdf_id}.")
        return

    click.echo(f"\nEvent history for PDF #{pdf_id}:")
    click.echo("-" * 60)

    for event in events:
        payload = event['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)
        click.echo(f"\n[{event['timestamp']}] {event['event_type']}")
        for k, v in payload.items():
            if v:
                click.echo(f"  {k}: {v}")


# ============================================================================
# REMINDER COMMANDS (LIFE-004)
# ============================================================================

@cli.group()
def reminder():
    """Event reminders and calendar events (Event-sourced)"""
    pass


@reminder.command("add")
@click.argument("title")
@click.argument("event_date")
@click.option("--time", "-t", "event_time", default="", help="Event time (HH:MM)")
@click.option("--description", "-d", default="", help="Event description")
@click.option("--remind", "-r", type=int, default=30, help="Reminder minutes before")
@click.option("--recurrence", type=click.Choice(["none", "daily", "weekly", "monthly"]), default="none")
@click.option("--contact", "-c", type=int, help="Link to contact ID")
@click.option("--tags", default="", help="Comma-separated tags")
def reminder_add(title, event_date, event_time, description, remind, recurrence, contact, tags):
    """Add a new reminder (date format: YYYY-MM-DD)"""
    from modules.life.event_reminder import EventReminder, Recurrence

    system = EventReminder()
    reminder_id = system.add(
        title=title,
        event_date=event_date,
        event_time=event_time,
        description=description,
        reminder_minutes=remind,
        recurrence=Recurrence(recurrence),
        contact_id=contact,
        tags=tags
    )
    click.echo(f"Reminder added with ID: {reminder_id}")


@reminder.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--from", "-f", "from_date", default=None, help="From date (YYYY-MM-DD)")
@click.option("--to", "to_date", default=None, help="To date (YYYY-MM-DD)")
@click.option("--completed", "-c", is_flag=True, help="Include completed")
@click.option("--archived", "-a", is_flag=True, help="Include archived")
def reminder_list(tag, from_date, to_date, completed, archived):
    """List reminders"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    reminders = system.list_reminders(
        tag=tag,
        from_date=from_date,
        to_date=to_date,
        include_completed=completed,
        include_archived=archived
    )

    if not reminders:
        click.echo("No reminders found.")
        return

    click.echo(f"\n{'ID':<4} {'Date':<12} {'Time':<6} {'Title'}")
    click.echo("-" * 55)

    for r in reminders:
        time_str = r['event_time'][:5] if r['event_time'] else "-"
        title = r['title'][:30] + "..." if len(r['title']) > 30 else r['title']
        click.echo(f"{r['id']:<4} {r['event_date']:<12} {time_str:<6} {title}")

    click.echo(f"\nTotal: {len(reminders)} reminder(s)")


@reminder.command("show")
@click.argument("reminder_id", type=int)
def reminder_show(reminder_id):
    """Show reminder details"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    r = system.get(reminder_id)

    if not r:
        click.echo(f"Reminder {reminder_id} not found.")
        return

    click.echo(f"\nReminder #{r['id']}")
    click.echo(f"Title: {r['title']}")
    click.echo(f"Date: {r['event_date']}")
    click.echo(f"Time: {r['event_time'] or '-'}")
    click.echo(f"Description: {r['description'] or '-'}")
    click.echo(f"Remind: {r['reminder_minutes']} minutes before")
    click.echo(f"Recurrence: {r['recurrence']}")
    click.echo(f"Tags: {r['tags'] or '-'}")
    if r['contact_id']:
        click.echo(f"Linked Contact: #{r['contact_id']}")
    click.echo(f"Status: {'COMPLETED' if r['completed'] else 'ARCHIVED' if r['archived'] else 'active'}")


@reminder.command("upcoming")
@click.option("--days", "-d", type=int, default=7, help="Days to look ahead")
def reminder_upcoming(days):
    """Show upcoming reminders"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    reminders = system.upcoming(days=days)

    if not reminders:
        click.echo(f"No reminders in the next {days} days.")
        return

    click.echo(f"\nUpcoming Reminders (next {days} days):")
    click.echo("-" * 50)

    for r in reminders:
        time_str = r['event_time'][:5] if r['event_time'] else ""
        click.echo(f"  {r['event_date']} {time_str} - {r['title']}")


@reminder.command("complete")
@click.argument("reminder_id", type=int)
def reminder_complete(reminder_id):
    """Mark reminder as completed"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    if system.complete(reminder_id):
        click.echo(f"Reminder {reminder_id} marked as completed.")
    else:
        click.echo(f"Cannot complete reminder {reminder_id}. Check status.")


@reminder.command("snooze")
@click.argument("reminder_id", type=int)
@click.option("--minutes", "-m", type=int, default=15, help="Minutes to snooze")
def reminder_snooze(reminder_id, minutes):
    """Snooze a reminder"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    if system.snooze(reminder_id, minutes=minutes):
        click.echo(f"Reminder {reminder_id} snoozed for {minutes} minutes.")
    else:
        click.echo(f"Cannot snooze reminder {reminder_id}. Check status.")


@reminder.command("archive")
@click.argument("reminder_id", type=int)
def reminder_archive(reminder_id):
    """Archive a reminder (soft delete)"""
    from modules.life.event_reminder import EventReminder

    system = EventReminder()
    if system.archive(reminder_id):
        click.echo(f"Reminder {reminder_id} archived.")
    else:
        click.echo(f"Cannot archive reminder {reminder_id}. Check status.")


@reminder.command("explain")
@click.argument("reminder_id", type=int)
def reminder_explain(reminder_id):
    """Show reminder event history (audit trail)"""
    from modules.life.event_reminder import EventReminder
    import json

    system = EventReminder()
    events = system.explain(reminder_id)

    if not events:
        click.echo(f"No events found for reminder {reminder_id}.")
        return

    click.echo(f"\nEvent history for reminder #{reminder_id}:")
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
# REPO ANALYZER COMMANDS (KNOW-005)
# ============================================================================

@cli.group()
def repo():
    """GitHub repository analysis (Onboarding)"""
    pass


@repo.command("analyze")
@click.argument("github_url")
@click.option("--notes", "-n", default="", help="Notes about why analyzing this repo")
@click.option("--tags", "-t", default="", help="Comma-separated tags")
def repo_analyze(github_url, notes, tags):
    """Analyze a GitHub repository"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    click.echo(f"Analyzing repository: {github_url}")
    click.echo("Fetching repository data...")

    try:
        analysis_id = analyzer.analyze(github_url, notes=notes, tags=tag_list)
        analysis = analyzer.get(analysis_id)

        click.echo(f"\nAnalysis #{analysis_id} complete!")
        click.echo(f"Repository: {analysis['repo_name']}")
        click.echo(f"Language: {analysis['language']}")
        click.echo(f"Stars: {analysis['stars']:,}")

        tech = analysis.get('technologies', {})
        if tech.get('frameworks'):
            click.echo(f"Frameworks: {', '.join(tech['frameworks'])}")

        patterns = analysis.get('patterns', [])
        if patterns:
            click.echo(f"\nPatterns detected: {len(patterns)}")
            for p in patterns[:3]:
                click.echo(f"  - {p['name']}")

    except Exception as e:
        click.echo(f"Error analyzing repository: {e}")


@repo.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--language", "-l", default=None, help="Filter by language")
@click.option("--archived", "-a", is_flag=True, help="Include archived")
def repo_list(tag, language, archived):
    """List analyzed repositories"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    analyses = analyzer.list_analyses(tag=tag, language=language, include_archived=archived)

    if not analyses:
        click.echo("No repositories analyzed yet. Use: repo analyze <github_url>")
        return

    click.echo(f"\n{'ID':<4} {'Language':<12} {'Stars':<8} {'Repository'}")
    click.echo("-" * 65)

    for a in analyses:
        lang = a['language'][:11] if a['language'] else "-"
        stars = f"{a['stars']:,}" if a['stars'] else "-"
        repo = a['repo_name'][:30] + "..." if len(a['repo_name']) > 30 else a['repo_name']
        click.echo(f"{a['id']:<4} {lang:<12} {stars:<8} {repo}")

    click.echo(f"\nTotal: {len(analyses)} analysis(es)")


@repo.command("show")
@click.argument("analysis_id", type=int)
def repo_show(analysis_id):
    """Show analysis details"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    a = analyzer.get(analysis_id)

    if not a:
        click.echo(f"Analysis {analysis_id} not found.")
        return

    click.echo(f"\nAnalysis #{a['id']}: {a['repo_name']}")
    click.echo("-" * 50)
    click.echo(f"URL: {a['github_url']}")
    click.echo(f"Description: {a['description'] or '-'}")
    click.echo(f"Language: {a['language']}")
    click.echo(f"Stars: {a['stars']:,} | Forks: {a['forks']:,}")
    click.echo(f"Topics: {', '.join(a['topics']) if a['topics'] else '-'}")
    click.echo(f"Tags: {', '.join(a['tags']) if a['tags'] else '-'}")
    click.echo(f"Analyzed: {a['analyzed_at'][:19] if a['analyzed_at'] else '-'}")

    tech = a.get('technologies', {})
    if tech:
        click.echo("\nTechnologies:")
        if tech.get('languages'):
            click.echo(f"  Languages: {', '.join(tech['languages'])}")
        if tech.get('frameworks'):
            click.echo(f"  Frameworks: {', '.join(tech['frameworks'])}")
        if tech.get('tools'):
            click.echo(f"  Tools: {', '.join(tech['tools'])}")

    struct = a.get('structure', {})
    if struct:
        click.echo(f"\nStructure: {struct.get('total_files', 0)} files")
        if struct.get('top_level_dirs'):
            click.echo(f"  Directories: {', '.join(struct['top_level_dirs'][:8])}")

    patterns = a.get('patterns', [])
    if patterns:
        click.echo("\nPatterns:")
        for p in patterns:
            click.echo(f"  - {p['name']} ({p['confidence']})")

    if a.get('lessons'):
        click.echo(f"\nLessons Learned: {len(a['lessons'])}")
        for lesson in a['lessons'][:3]:
            click.echo(f"  - {lesson['title']}")


@repo.command("report")
@click.argument("analysis_id", type=int)
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), default=None)
def repo_report(analysis_id, output):
    """Generate markdown report for an analysis"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    report = analyzer.generate_report(analysis_id)

    if not report:
        click.echo(f"Analysis {analysis_id} not found.")
        return

    if output:
        Path(output).write_text(report, encoding="utf-8")
        click.echo(f"Report saved to {output}")
    else:
        click.echo(report)


@repo.command("lesson")
@click.argument("analysis_id", type=int)
@click.argument("title")
@click.option("--description", "-d", default="", help="Lesson description")
@click.option("--apply-to", "-a", default="", help="Where to apply this lesson")
def repo_lesson(analysis_id, title, description, apply_to):
    """Add a lesson learned from a repository"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    if analyzer.add_lesson(analysis_id, title, description, apply_to):
        click.echo(f"Added lesson to analysis #{analysis_id}: {title}")
    else:
        click.echo(f"Error: Analysis #{analysis_id} not found")


@repo.command("pattern")
@click.argument("analysis_id", type=int)
@click.argument("pattern_name")
@click.option("--description", "-d", default="", help="Pattern description")
@click.option("--applicability", "-a", default="", help="When to apply this pattern")
def repo_pattern(analysis_id, pattern_name, description, applicability):
    """Add a manually identified pattern"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    if analyzer.add_pattern(analysis_id, pattern_name, description, applicability):
        click.echo(f"Added pattern to analysis #{analysis_id}: {pattern_name}")
    else:
        click.echo(f"Error: Analysis #{analysis_id} not found")


@repo.command("patterns")
def repo_patterns():
    """List all patterns across all analyzed repos"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    patterns = analyzer.get_all_patterns()

    if not patterns:
        click.echo("No patterns found. Analyze some repositories first.")
        return

    click.echo(f"\nAll Identified Patterns ({len(patterns)} total):")
    click.echo("-" * 50)

    for p in patterns:
        source = p.get('source_repo', '').split('/')[-1] if p.get('source_repo') else '-'
        click.echo(f"  - {p.get('name', p.get('pattern_name', '-'))} (from {source})")


@repo.command("lessons")
def repo_lessons():
    """List all lessons learned across all repos"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    lessons = analyzer.get_all_lessons()

    if not lessons:
        click.echo("No lessons recorded. Add some with: repo lesson <id> <title>")
        return

    click.echo(f"\nAll Lessons Learned ({len(lessons)} total):")
    click.echo("-" * 50)

    for lesson in lessons:
        source = lesson.get('source_repo', '').split('/')[-1] if lesson.get('source_repo') else '-'
        click.echo(f"  - {lesson['title']} (from {source})")
        if lesson.get('apply_to'):
            click.echo(f"    Apply to: {lesson['apply_to']}")


@repo.command("archive")
@click.argument("analysis_id", type=int)
def repo_archive(analysis_id):
    """Archive an analysis"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer

    analyzer = RepoAnalyzer()
    if analyzer.archive(analysis_id):
        click.echo(f"Archived analysis #{analysis_id}")
    else:
        click.echo(f"Error: Analysis #{analysis_id} not found")


@repo.command("explain")
@click.argument("analysis_id", type=int)
def repo_explain(analysis_id):
    """Show event history for an analysis"""
    from modules.knowledge.repo_analyzer import RepoAnalyzer
    import json

    analyzer = RepoAnalyzer()
    events = analyzer.explain(analysis_id)

    if not events:
        click.echo(f"No events found for analysis {analysis_id}.")
        return

    click.echo(f"\nEvent history for analysis #{analysis_id}:")
    click.echo("-" * 60)

    for event in events:
        payload = event['payload']
        if isinstance(payload, str):
            payload = json.loads(payload)
        click.echo(f"\n[{event['timestamp']}] {event['event_type']}")
        # Show selected fields only (not full payload)
        for k in ['repo_name', 'pattern_name', 'title', 'status']:
            if k in payload:
                click.echo(f"  {k}: {payload[k]}")


# ============================================================================
# UI COMMANDS
# ============================================================================

@cli.command("ui")
def launch_ui():
    """Launch the Atlas desktop UI (Tkinter)"""
    from modules.ui.app import launch
    click.echo("Launching Atlas Desktop UI...")
    launch()


@cli.command("web")
@click.option("--host", "-h", default="127.0.0.1", help="API host")
@click.option("--port", "-p", default=8000, type=int, help="API port")
def launch_web(host, port):
    """Launch the Atlas Web API server"""
    click.echo(f"Starting Atlas Web API on http://{host}:{port}")
    click.echo("Web UI: Run 'npm run dev' in the web/ directory")
    from modules.api.server import run_server
    run_server(host=host, port=port)


if __name__ == "__main__":
    cli()
