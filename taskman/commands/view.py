import re
import shutil
import sys
import textwrap
from datetime import date, timedelta

from taskman import db

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')
MIN_COL_WIDTH = 18
COL_GAP = 2


def _vlen(s):
    return len(_ANSI_RE.sub('', s))


def _pad(s, width):
    return s + ' ' * max(0, width - _vlen(s))


def _red(s):   return f'\033[31m{s}\033[0m'
def _blue(s):  return f'\033[34m{s}\033[0m'
def _green(s): return f'\033[32m{s}\033[0m'
def _bold(s):  return f'\033[1m{s}\033[0m'
def _dim(s):   return f'\033[2m{s}\033[0m'


def _format_due(due_str, today):
    due = date.fromisoformat(due_str)
    delta = (due - today).days
    label = (
        due.strftime('%b ') + str(due.day) if delta < 0
        else 'today'      if delta == 0
        else 'tomorrow'   if delta == 1
        else due.strftime('%A').lower() if delta < 7
        else due.strftime('%b ') + str(due.day)
    )
    return _red(label) if delta < 0 else _blue(label)


def filter_tasks(tasks, list_id, mode, today):
    if mode == 'done':
        return sorted(
            [t for t in tasks if t['listId'] == list_id and t['done']],
            key=lambda t: t['done'],
            reverse=True,
        )

    pending = [t for t in tasks if t['listId'] == list_id and not t['done']]

    if mode == 'day':
        return sorted(
            [t for t in pending if t['due'] and date.fromisoformat(t['due']) <= today],
            key=lambda t: t['due'],
        )
    if mode == 'week':
        cutoff = today + timedelta(days=7)
        return sorted(
            [t for t in pending if t['due'] and date.fromisoformat(t['due']) <= cutoff],
            key=lambda t: t['due'],
        )

    dated = sorted([t for t in pending if t['due']], key=lambda t: t['due'])
    dateless = [t for t in pending if not t['due']]
    return dated + dateless


def _render_column(list_name, tasks, col_width, today, mode='all'):
    lines = [
        _pad(_bold(list_name), col_width),
        '─' * col_width,
    ]

    if not tasks:
        lines.append(_pad(_dim('  no tasks'), col_width))
        return lines

    for task in tasks:
        name_lines = textwrap.wrap(task['name'], col_width - 2) or ['']
        for i, part in enumerate(name_lines):
            prefix = '✓ ' if mode == 'done' and i == 0 else ('· ' if i == 0 else '  ')
            text = _dim(prefix + part) if mode == 'done' else prefix + part
            lines.append(_pad(text, col_width))
        if mode == 'done' and task['done']:
            lines.append(_pad('  ' + _green(task['done']), col_width))
        elif task['due']:
            lines.append(_pad('  ' + _format_due(task['due'], today), col_width))

    return lines


def _cols_per_row(n):
    term_w = shutil.get_terminal_size((80, 24)).columns
    for cols in range(n, 0, -1):
        w = (term_w - COL_GAP * (cols - 1)) // cols
        if w >= MIN_COL_WIDTH:
            return cols, w
    return 1, term_w


def _render_section(pairs, today, mode):
    n = len(pairs)
    cols_per_row, col_width = _cols_per_row(n)
    gap = ' ' * COL_GAP

    for row_start in range(0, n, cols_per_row):
        row = pairs[row_start:row_start + cols_per_row]
        columns = [_render_column(lst['name'], tasks, col_width, today, mode) for lst, tasks in row]

        max_lines = max(len(c) for c in columns)
        for col in columns:
            col += [' ' * col_width] * (max_lines - len(col))

        for parts in zip(*columns):
            print(gap.join(parts))
        print()


def cmd_ls(args):
    mode = 'all'
    filter_name = None

    for arg in args:
        if arg == '--day':
            mode = 'day'
        elif arg == '--week':
            mode = 'week'
        elif arg == '--done':
            mode = 'done'
        else:
            filter_name = arg

    data = db.load()
    today = date.today()

    all_lists = data['lists']
    if filter_name:
        group = next((g for g in data['groups'] if g['name'] == filter_name), None)
        if group:
            show_lists = [l for l in all_lists if l['groupId'] == group['id']]
        else:
            lst = next((l for l in all_lists if l['name'] == filter_name), None)
            if not lst:
                print(f"taskman: '{filter_name}' is not a list or group", file=sys.stderr)
                sys.exit(1)
            show_lists = [lst]

        if not show_lists:
            print('no lists found')
            return

        pairs = [(lst, filter_tasks(data['tasks'], lst['id'], mode, today)) for lst in show_lists]
        pairs = [(lst, tasks) for lst, tasks in pairs if tasks]
        if pairs:
            _render_section(pairs, today, mode)
        return

    if not all_lists:
        print('no lists found')
        return

    seen = set()

    for group in sorted(data['groups'], key=lambda g: g['name']):
        group_lists = sorted([l for l in all_lists if l['groupId'] == group['id']], key=lambda l: l['name'])
        if not group_lists:
            continue
        pairs = [(lst, filter_tasks(data['tasks'], lst['id'], mode, today)) for lst in group_lists]
        pairs = [(lst, tasks) for lst, tasks in pairs if tasks]
        if pairs:
            print(_bold(group['name']))
            _render_section(pairs, today, mode)
        seen.update(l['id'] for l in group_lists)

    ungrouped = sorted([l for l in all_lists if l['id'] not in seen], key=lambda l: l['name'])
    if ungrouped:
        pairs = [(lst, filter_tasks(data['tasks'], lst['id'], mode, today)) for lst in ungrouped]
        pairs = [(lst, tasks) for lst, tasks in pairs if tasks]
        if pairs:
            _render_section(pairs, today, mode)
