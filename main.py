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


if __name__ == "__main__":
    cli()
