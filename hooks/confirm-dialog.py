#!/usr/bin/env python3
"""Claude Code PreToolUse hook - sleek tkinter confirmation dialog."""

import json
import sys

DANGEROUS_PATTERNS = [
    'rm -rf', 'rm -r', 'rm -f', 'rmdir',
    'git push --force', 'git push -f',
    'git reset --hard', 'git clean',
    'git branch -D', 'git checkout --',
    'drop ', 'truncate ', 'DELETE FROM',
    'sudo rm', 'sudo mv /', 'sudo chmod 777',
    'mkfs', 'dd if=', ':(){ :|:& };:',
]

INTERCEPT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'Bash'}

# ── Catppuccin Mocha palette ──
C = {
    'base':      '#1e1e2e', 'mantle':     '#181825', 'crust':     '#11111b',
    'surface0':  '#313244', 'surface1':   '#45475a', 'surface2':  '#585b70',
    'overlay0':  '#6c7086', 'overlay1':   '#7f849c',
    'text':      '#cdd6f4', 'subtext0':   '#a6adc8', 'subtext1':  '#bac2de',
    'blue':      '#89b4fa', 'lavender':   '#b4befe', 'sapphire':  '#74c7ec',
    'red':       '#f38ba8', 'maroon':     '#eba0ac', 'peach':     '#fab387',
    'yellow':    '#f9e2af', 'green':      '#a6e3a1', 'teal':      '#94e2d5',
    'mauve':     '#cba6f7', 'pink':       '#f5c2e7', 'flamingo':  '#f2cdcd',
    'rosewater': '#f5e0dc',
}


def is_dangerous(tool_name, tool_input):
    if tool_name == 'Bash':
        cmd = tool_input.get('command', '')
        return any(p in cmd for p in DANGEROUS_PATTERNS)
    return False


def format_content(tool_name, tool_input):
    if tool_name == 'Bash':
        return tool_input.get('command', '(empty)')
    elif tool_name in ('Edit', 'Write'):
        return tool_input.get('file_path', '(unknown file)')
    elif tool_name == 'MultiEdit':
        edits = tool_input.get('edits', [])
        return '\n'.join(e.get('file_path', '?') for e in edits)
    return str(tool_input)


def show_dialog(content, tool_name, dangerous):
    try:
        import tkinter as tk
    except ImportError:
        print(f"\n[Hook] {tool_name}: {content}", file=sys.stderr)
        resp = input("Allow? (y/n): ").strip().lower()
        return resp == 'y'

    result = {'allowed': False}
    root = tk.Tk()
    root.withdraw()
    root.title('')
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.overrideredirect(True)

    # Theme colors
    if dangerous:
        accent = C['red']
        accent_hover = '#ff9eb8'
        header_fg = C['red']
        badge_bg = C['red']
        badge_text = C['crust']
    else:
        accent = C['blue']
        accent_hover = C['lavender']
        header_fg = C['blue']
        badge_bg = C['blue']
        badge_text = C['crust']

    # ── Main container with colored border ──
    root.configure(bg=accent)
    outer = tk.Frame(root, bg=accent, padx=2, pady=2)
    outer.pack(fill='both', expand=True)
    main = tk.Frame(outer, bg=C['base'])
    main.pack(fill='both', expand=True)

    # ── Header ──
    header = tk.Frame(main, bg=C['mantle'], padx=28, pady=18)
    header.pack(fill='x')

    top_row = tk.Frame(header, bg=C['mantle'])
    top_row.pack(fill='x')

    # Diamond icon
    icon_cv = tk.Canvas(top_row, width=32, height=32, bg=C['mantle'], highlightthickness=0)
    icon_cv.pack(side='left', padx=(0, 12))
    cx, cy, r = 16, 16, 11
    pts = [cx, cy-r, cx+r*0.55, cy-r*0.15, cx+r, cy,
           cx+r*0.55, cy+r*0.15, cx, cy+r,
           cx-r*0.55, cy+r*0.15, cx-r, cy,
           cx-r*0.55, cy-r*0.15]
    icon_cv.create_polygon(pts, fill=accent, outline='')

    tk.Label(top_row, text='Claude Code', font=('SF Pro Display', 17, 'bold'),
             bg=C['mantle'], fg=C['text']).pack(side='left')

    # Close button
    close_btn = tk.Label(top_row, text=' × ', font=('SF Pro', 16),
                         bg=C['mantle'], fg=C['overlay0'], cursor='hand2')
    close_btn.pack(side='right')
    close_btn.bind('<Button-1>', lambda e: on_deny())
    close_btn.bind('<Enter>', lambda e: close_btn.configure(fg=C['text']))
    close_btn.bind('<Leave>', lambda e: close_btn.configure(fg=C['overlay0']))

    # Badges row
    sub_row = tk.Frame(header, bg=C['mantle'])
    sub_row.pack(fill='x', pady=(10, 0))
    tk.Label(sub_row, text=f'  {tool_name}  ', font=('SF Mono', 10, 'bold'),
             bg=badge_bg, fg=badge_text, padx=4, pady=2).pack(side='left')
    if dangerous:
        tk.Label(sub_row, text='  DANGEROUS  ', font=('SF Mono', 10, 'bold'),
                 bg=C['red'], fg=C['crust'], padx=4, pady=2).pack(side='left', padx=(8, 0))

    # Separator
    tk.Frame(main, bg=C['surface0'], height=1).pack(fill='x')

    # ── Body ──
    body = tk.Frame(main, bg=C['base'], padx=28, pady=18)
    body.pack(fill='both', expand=True)

    if tool_name == 'Bash':
        action_text = 'Claude wants to execute:'
    elif tool_name in ('Edit', 'Write'):
        action_text = 'Claude wants to modify:'
    else:
        action_text = 'Claude wants to operate on:'

    tk.Label(body, text=action_text, font=('SF Pro Text', 13),
             bg=C['base'], fg=C['subtext0'], anchor='w').pack(fill='x', pady=(0, 10))

    # Code display
    code_frame = tk.Frame(body, bg=C['crust'], padx=16, pady=12)
    code_frame.pack(fill='both', expand=True, pady=(0, 4))

    line_count = min(max(content.count('\n') + 1, 2), 14)
    content_text = tk.Text(
        code_frame, font=('SF Mono', 12), bg=C['crust'],
        fg=C['rosewater'] if dangerous else C['green'],
        wrap='word', height=line_count, width=56,
        relief='flat', borderwidth=0,
        insertbackground=C['crust'], highlightthickness=0,
        selectbackground=C['surface1'], selectforeground=C['text'],
        spacing1=2, spacing3=2,
    )
    content_text.pack(fill='both', expand=True)
    content_text.insert('1.0', content)
    content_text.configure(state='disabled')

    # Keyboard hints
    hint_frame = tk.Frame(body, bg=C['base'])
    hint_frame.pack(fill='x', pady=(8, 0))
    for lbl, desc in [('Enter', ' allow  '), ('Esc', ' deny')]:
        tk.Label(hint_frame, text=lbl, font=('SF Mono', 10, 'bold'),
                 bg=C['surface0'], fg=C['subtext0'], padx=6, pady=1).pack(side='left')
        tk.Label(hint_frame, text=desc, font=('SF Pro Text', 10),
                 bg=C['base'], fg=C['overlay0']).pack(side='left')

    # ── Buttons ──
    btn_area = tk.Frame(main, bg=C['mantle'], padx=28, pady=16)
    btn_area.pack(fill='x')
    btn_area.columnconfigure(0, weight=1)
    btn_area.columnconfigure(1, weight=1)

    def on_deny():
        result['allowed'] = False
        root.destroy()

    def on_allow():
        result['allowed'] = True
        root.destroy()

    def make_button(parent, text, bg_color, fg_color, hover_bg, hover_fg,
                    command, col, padx_adj):
        frame = tk.Frame(parent, bg=bg_color, cursor='hand2')
        frame.grid(row=0, column=col, sticky='ew', padx=padx_adj)
        btn = tk.Label(frame, text=f'  {text}  ', font=('SF Pro Display', 13, 'bold'),
                       bg=bg_color, fg=fg_color, padx=20, pady=10)
        btn.pack(fill='both', expand=True)
        def enter(e):
            frame.configure(bg=hover_bg); btn.configure(bg=hover_bg, fg=hover_fg)
        def leave(e):
            frame.configure(bg=bg_color); btn.configure(bg=bg_color, fg=fg_color)
        for w in (frame, btn):
            w.bind('<Enter>', enter)
            w.bind('<Leave>', leave)
            w.bind('<Button-1>', lambda e: command())

    make_button(btn_area, 'Deny', C['surface1'], C['subtext0'],
                C['surface2'], C['text'], on_deny, 0, (0, 8))
    make_button(btn_area, 'Allow', accent, C['crust'],
                accent_hover, C['crust'], on_allow, 1, (8, 0))

    # Keyboard
    root.bind('<Escape>', lambda e: on_deny())
    root.bind('<Return>', lambda e: on_allow())

    # ── Center + fade in ──
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f'{w}x{h}+{x}+{y}')

    root.attributes('-alpha', 0.0)
    root.deiconify()

    def fade_in(a=0.0):
        if a < 1.0:
            root.attributes('-alpha', min(a + 0.15, 1.0))
            root.after(20, fade_in, a + 0.15)
    fade_in()
    root.mainloop()
    return result['allowed']


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    if tool_name not in INTERCEPT_TOOLS:
        sys.exit(0)

    tool_input = data.get('tool_input', {})
    dangerous = is_dangerous(tool_name, tool_input)

    if not dangerous:
        sys.exit(0)

    content = format_content(tool_name, tool_input)
    print(f"[hook] DANGEROUS {tool_name}: {content[:80]}", file=sys.stderr)

    allowed = show_dialog(content, tool_name, dangerous)
    if not allowed:
        print("Operation denied by user.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
