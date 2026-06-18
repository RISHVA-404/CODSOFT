# ==============================================================================
#  SMART FILE SEARCH TOOL  —  v3.0
#  Mini Project  |  Python + Tkinter + File Handling + OOP
#
#  Concepts demonstrated:
#   Data Structures : List, Tuple, Set, Dictionary, Slicing,
#                     Sorting, Filtering, List Comprehension
#   OOP             : Classes, Objects, Constructors, Access Specifiers,
#                     Inheritance, Method Overriding, Operator Overloading
#   GUI             : Tkinter (5 screens with sidebar navigation)
#   Storage         : File Handling (search_history.txt)
# ==============================================================================

import os
import tkinter as tk
from tkinter import filedialog, messagebox

# ==============================================================================
#  SECTION A — COLOUR PALETTE & FONTS
# ==============================================================================

BG        = "#0F0F1A"   # main background
SIDE_BG   = "#16162A"   # sidebar
CARD      = "#1C1C2E"   # card panels
BORDER    = "#2A2A45"   # divider lines
ACCENT    = "#7C5CBF"   # violet (primary action)
AHOVER    = "#9B7DE0"   # lighter violet for hover
GREEN     = "#22C97A"   # success / found
RED       = "#E05555"   # danger / exit
YELLOW    = "#F5A623"   # warning
TEXT      = "#EEEEFF"   # main text
MUTED     = "#6A6A9A"   # secondary text
INP_BG    = "#11111E"   # entry background
INP_FG    = "#DDDDF5"   # entry text

FT        = ("Segoe UI", 9)          # body font
FT_B      = ("Segoe UI", 9,  "bold") # bold body
FT_H      = ("Segoe UI", 13, "bold") # heading
FT_BIG    = ("Segoe UI", 24, "bold") # hero title
FT_MONO   = ("Consolas",  9)         # monospace (paths)
FT_SIDE   = ("Segoe UI",  9, "bold") # sidebar items
FT_SM     = ("Segoe UI",  8, "bold") # small badge

# ==============================================================================
#  SECTION B — OOP: CLASS DEFINITIONS
# ==============================================================================

# ------------------------------------------------------------------------------
#  CLASS 1: FileRecord
#  Represents a single found file.
#  Demonstrates: Class, Constructor, Access Specifiers, Operator Overloading,
#                Tuple (to_tuple method)
# ------------------------------------------------------------------------------
class FileRecord:
    """Stores all information about one found file."""

    def __init__(self, full_path):
        # Constructor — called when FileRecord(path) is written
        self.__path = full_path                              # PRIVATE  (name mangling)
        self._name  = os.path.basename(full_path)           # PROTECTED
        self._ext   = os.path.splitext(full_path)[1].lower()# PROTECTED
        try:
            self._size_bytes = os.path.getsize(full_path)   # PROTECTED
        except OSError:
            self._size_bytes = 0

    # -- Getters (public interface to private/protected data) -----------------
    def get_path(self):  return self.__path
    def get_name(self):  return self._name
    def get_ext(self):   return self._ext

    def get_size_str(self):
        """Return human-readable file size string."""
        b = self._size_bytes
        if   b >= 1_048_576: return f"{b // 1_048_576} MB"
        elif b >= 1_024:     return f"{b // 1_024} KB"
        else:                return f"{b} B"

    # -- Operator Overloading -------------------------------------------------
    def __str__(self):
        """str(record) returns the file name."""
        return self._name

    def __eq__(self, other):
        """record1 == record2  compares by full path."""
        return self.__path == other.get_path()

    def __lt__(self, other):
        """record1 < record2  compares alphabetically by name (used for sorting)."""
        return self._name.lower() < str(other).lower()

    def __len__(self):
        """len(record) returns file size in bytes."""
        return self._size_bytes

    # -- Tuple representation -------------------------------------------------
    def to_tuple(self):
        """Return an immutable Tuple snapshot of this file's data.
        Demonstrates: Tuple (immutable, fixed data bundle)"""
        return (self._name, self.__path, self._ext, self._size_bytes)
        #        [0]name    [1]path       [2]ext      [3]size  — indexed like a tuple


# ------------------------------------------------------------------------------
#  CLASS 2: SearchEngine  (Base Class)
#  Demonstrates: Class, Constructor, Access Specifiers, Operator Overloading
# ------------------------------------------------------------------------------
class SearchEngine:
    """Base search engine — walks a folder and collects FileRecord objects."""

    def __init__(self, folder):
        # Constructor
        self._folder  = folder   # protected: subclasses can read this
        self._results = []       # List of FileRecord objects

    def search(self, keyword, extension):
        """
        Walk self._folder recursively using os.walk().
        Collect every file that matches keyword AND extension.
        Returns a List of FileRecord objects.
        """
        self._results = []   # reset List

        try:
            for folder_path, _, files in os.walk(self._folder):
                for file_name in files:
                    rec = FileRecord(os.path.join(folder_path, file_name))

                    # Filtering conditions
                    kw_ok  = (keyword   == "") or (keyword in file_name.lower())
                    ext_ok = (extension == "") or (rec.get_ext() == extension)

                    if kw_ok and ext_ok:
                        self._results.append(rec)   # append to List

        except PermissionError:
            pass   # silently skip protected system folders

        return self._results

    # -- Getters ---------------------------------------------------------------
    def get_results(self):
        return self._results

    def get_unique_extensions(self):
        """
        Return a Set of unique file extensions in the results.
        Demonstrates: Set (automatically removes duplicates)
        """
        return {rec.get_ext() for rec in self._results}   # Set comprehension

    # -- Operator overloading --------------------------------------------------
    def __len__(self):
        """len(engine) → number of results found."""
        return len(self._results)

    def __str__(self):
        """str(engine) → readable description."""
        return f"SearchEngine | folder: {self._folder} | found: {len(self)}"


# ------------------------------------------------------------------------------
#  CLASS 3: FilteredSearchEngine  (Inherits SearchEngine)
#  Demonstrates: Inheritance, Method Overriding, Constructor,
#                List Comprehension, Slicing, Sorting, Dictionary
# ------------------------------------------------------------------------------
class FilteredSearchEngine(SearchEngine):
    """
    Extends SearchEngine with sorting, slicing, filtering, and statistics.
    Inherits all attributes and methods from SearchEngine.
    """

    # MAX_RESULTS is a class variable (shared by all instances, like a constant)
    MAX_RESULTS = 1000

    def __init__(self, folder, sort_by="name"):
        super().__init__(folder)          # Call parent constructor via super()
        self.__sort_by = sort_by          # PRIVATE: "name" or "ext"

    # -- Method Overriding -----------------------------------------------------
    def search(self, keyword, extension):
        """
        OVERRIDES SearchEngine.search().
        Calls the parent version first, then sorts and slices the results.
        Demonstrates: Method Overriding, Sorting, Slicing
        """
        super().search(keyword, extension)    # Run parent search logic

        # Sorting: uses FileRecord.__lt__ for alphabetical sort
        if self.__sort_by == "name":
            self._results = sorted(self._results)                      # A→Z by name
        elif self.__sort_by == "ext":
            self._results = sorted(self._results, key=lambda r: r.get_ext())  # by extension

        # Slicing: keep only the first MAX_RESULTS items
        # Demonstrates: Slicing on a List
        self._results = self._results[:self.MAX_RESULTS]

        return self._results

    def filter_by_ext(self, ext):
        """
        Return only the records matching a given extension.
        Demonstrates: Filtering technique + List Comprehension
        """
        if ext == "ALL":
            return self._results
        # List comprehension with condition — same as a filtered loop
        return [rec for rec in self._results if rec.get_ext() == ext]

    def get_stats(self):
        """
        Build and return a Dictionary of search statistics.
        Demonstrates: Dictionary, Set, List, Tuple access, List Comprehension
        """
        ext_set = self.get_unique_extensions()            # Set (unique types)
        sizes   = [rec.to_tuple()[3] for rec in self._results]  # List comp + tuple index [3]

        stats = {
            "total"      : len(self._results),            # int
            "types"      : len(ext_set),                  # int
            "ext_list"   : sorted(list(ext_set)),         # List from Set, sorted
            "size_kb"    : sum(sizes) // 1024,            # int
        }
        return stats   # Dictionary


# ------------------------------------------------------------------------------
#  CLASS 4: SearchHistory  (independent utility class)
#  Demonstrates: Class, Constructor, Access Specifiers, File Handling,
#                Dictionaries, List, Slicing
# ------------------------------------------------------------------------------
class SearchHistory:
    """Saves and loads the user's recent searches to/from a text file."""

    _FILE = "search_history.txt"   # Class variable — shared, immutable string

    def __init__(self):
        self.__records = []   # PRIVATE List of Dictionaries
        self._load()          # Load existing history on construction

    def add(self, keyword, extension, count):
        """
        Append one search record (as a Dictionary) to the history list.
        Keeps only the last 10 entries using Slicing.
        """
        record = {
            "keyword"  : keyword or "(any)",
            "extension": extension or "(all types)",
            "count"    : str(count),
        }
        self.__records.append(record)           # List append
        self.__records = self.__records[-10:]   # Slicing — keep last 10

        self._save()   # persist to file after every change

    def get_recent(self, n=5):
        """Return the last n records using Slicing."""
        return self.__records[-n:]   # Slicing on List

    def clear(self):
        """Wipe history (both in memory and on disk)."""
        self.__records = []
        self._save()

    def _save(self):
        """Write all records to file. File Handling — WRITE mode."""
        try:
            with open(self._FILE, "w") as f:
                for rec in self.__records:
                    # Each line: keyword|extension|count
                    f.write(f"{rec['keyword']}|{rec['extension']}|{rec['count']}\n")
        except Exception:
            pass   # Don't crash if file can't be written

    def _load(self):
        """Read records from file. File Handling — READ mode."""
        self.__records = []
        try:
            with open(self._FILE, "r") as f:
                for line in f:
                    parts = line.strip().split("|")   # Split on | delimiter
                    if len(parts) == 3:
                        self.__records.append({
                            "keyword"  : parts[0],
                            "extension": parts[1],
                            "count"    : parts[2],
                        })
        except FileNotFoundError:
            pass   # First run — no file yet, start with empty history


# ==============================================================================
#  SECTION C — GLOBAL APP STATE
# ==============================================================================

selected_folder = ""              # Folder chosen by the user
engine          = None            # FilteredSearchEngine instance (created at search time)
history         = SearchHistory() # Load history from file immediately on start
visible_recs    = []              # List of FileRecord currently shown in the results listbox

# ==============================================================================
#  SECTION D — GUI HELPER FUNCTIONS
# ==============================================================================

def clear_window():
    """Remove all widgets from root so a fresh screen can be drawn."""
    for w in root.winfo_children():
        w.destroy()


def styled_btn(parent, label, cmd, bg=ACCENT, fg=TEXT, width=15, py=7):
    """Create and return one styled flat button with hover effect."""
    b = tk.Button(parent, text=label, command=cmd,
                  font=FT_B, bg=bg, fg=fg,
                  activebackground=AHOVER, activeforeground=TEXT,
                  relief="flat", bd=0, cursor="hand2",
                  width=width, pady=py)
    hover = AHOVER if bg == ACCENT else BORDER
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def hr(parent, color=BORDER, px=0, py=6):
    """Draw a thin horizontal rule (divider line)."""
    tk.Frame(parent, bg=color, height=1).pack(fill="x", padx=px, pady=py)


def page_title(content, title, subtitle=""):
    """Render the page heading + optional subtitle inside the content area."""
    f = tk.Frame(content, bg=BG, pady=16)
    f.pack(fill="x", padx=28)
    tk.Label(f, text=title, font=FT_H, bg=BG, fg=TEXT).pack(anchor="w")
    if subtitle:
        tk.Label(f, text=subtitle, font=FT, bg=BG, fg=MUTED,
                 wraplength=680, justify="left").pack(anchor="w", pady=(2, 0))
    hr(content, px=28, py=0)


def sidebar(outer, active="home"):
    """
    Build a fixed-width left sidebar with navigation buttons.
    active — key of the currently active screen (gets highlighted).
    """
    sb = tk.Frame(outer, bg=SIDE_BG, width=158)
    sb.pack(side="left", fill="y")
    sb.pack_propagate(False)

    # Logo
    logo = tk.Frame(sb, bg=ACCENT, pady=16)
    logo.pack(fill="x")
    tk.Label(logo, text="🔍", font=("Segoe UI", 20), bg=ACCENT, fg=TEXT).pack()
    tk.Label(logo, text="FILE SEARCH", font=FT_SM, bg=ACCENT, fg=TEXT).pack()

    hr(sb, py=3)

    # Nav items: (icon + label, key, callback)
    items = [
        ("🏠  Home",     "home",    show_welcome),
        ("📁  Browse",   "browse",  show_browse),
        ("🔍  Search",   "search",  _nav_search),
        ("📋  Results",  "results", _nav_results),
        ("ℹ️  About",    "about",   show_about),
    ]

    for label, key, cmd in items:
        is_act = (key == active)
        item_bg = ACCENT if is_act else SIDE_BG
        item_fg = TEXT   if is_act else MUTED

        b = tk.Button(sb, text=label, command=cmd,
                      font=FT_SIDE, bg=item_bg, fg=item_fg,
                      activebackground=ACCENT, activeforeground=TEXT,
                      relief="flat", bd=0, cursor="hand2",
                      anchor="w", padx=18, pady=11)
        b.pack(fill="x")
        if not is_act:
            b.bind("<Enter>", lambda e, x=b: x.config(bg=BORDER, fg=TEXT))
            b.bind("<Leave>", lambda e, x=b: x.config(bg=SIDE_BG, fg=MUTED))

    # Spacer then Exit at bottom
    tk.Frame(sb, bg=SIDE_BG).pack(fill="both", expand=True)
    hr(sb, py=2)
    eb = tk.Button(sb, text="✕  Exit", command=root.quit,
                   font=FT_SIDE, bg=SIDE_BG, fg=RED,
                   activebackground=RED, activeforeground=TEXT,
                   relief="flat", bd=0, cursor="hand2",
                   anchor="w", padx=18, pady=11)
    eb.pack(fill="x", pady=(0, 8))
    eb.bind("<Enter>", lambda e: eb.config(bg=RED, fg=TEXT))
    eb.bind("<Leave>", lambda e: eb.config(bg=SIDE_BG, fg=RED))


def status_bar(outer, msg="Ready"):
    """Thin info strip pinned to the bottom of the window."""
    bar = tk.Frame(outer, bg=SIDE_BG, height=24)
    bar.pack(side="bottom", fill="x")
    bar.pack_propagate(False)
    tk.Label(bar, text=f"  ● {msg}", font=FT_SM, bg=SIDE_BG, fg=MUTED).pack(side="left", pady=3)
    tk.Label(bar, text="Smart File Search Tool v3.0  |  Python OOP + Tkinter + File Handling  ",
             font=FT_SM, bg=SIDE_BG, fg=MUTED).pack(side="right")


# Sidebar callbacks with guards
def _nav_search():
    if not selected_folder:
        messagebox.showinfo("No Folder", "Please browse and select a folder first.")
        return
    show_search()

def _nav_results():
    if engine is None or len(engine) == 0:
        messagebox.showinfo("No Results", "Run a search first.")
        return
    show_results()


# ==============================================================================
#  SECTION E — SCREEN 1: WELCOME / HOME
# ==============================================================================

def show_welcome():
    """
    Welcome screen.
    Displays recent search history loaded from the file via SearchHistory.
    Demonstrates: Dictionary (history records), Slicing (get_recent)
    """
    clear_window()
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)
    sidebar(outer, active="home")
    status_bar(outer, "Welcome! Click ▶ Start to begin.")

    content = tk.Frame(outer, bg=BG)
    content.pack(side="left", fill="both", expand=True)

    # Centre card
    centre = tk.Frame(content, bg=BG)
    centre.place(relx=0.5, rely=0.44, anchor="center")

    tk.Label(centre, text="🔍", font=("Segoe UI", 50), bg=BG, fg=ACCENT).pack()
    tk.Label(centre, text="Smart File Search Tool", font=FT_BIG, bg=BG, fg=TEXT).pack()
    tk.Frame(centre, bg=ACCENT, height=3, width=340).pack(pady=8)
    tk.Label(centre, text="Browse · Search · Open   —   powered by Python OOP",
             font=FT, bg=BG, fg=MUTED).pack(pady=(0, 22))

    # Action buttons
    brow = tk.Frame(centre, bg=BG)
    brow.pack()
    styled_btn(brow, "▶  Start",   show_browse,  bg=ACCENT,  width=16, py=9).pack(side="left", padx=6)
    styled_btn(brow, "ℹ  About",   show_about,   bg=CARD,    width=13, py=9).pack(side="left", padx=6)
    styled_btn(brow, "✕  Exit",    root.quit,    bg=RED,     width=11, py=9).pack(side="left", padx=6)

    # Recent history (Dictionary list from file)
    recent = history.get_recent(4)   # Slicing inside SearchHistory.get_recent()
    if recent:
        hist_f = tk.Frame(centre, bg=CARD, padx=20, pady=12)
        hist_f.pack(fill="x", pady=(22, 0))
        tk.Label(hist_f, text="RECENT SEARCHES", font=FT_SM, bg=CARD, fg=MUTED).pack(anchor="w")
        hr(hist_f, color=BORDER, py=4)

        for rec in reversed(recent):    # recent is a List of Dictionaries
            row = tk.Frame(hist_f, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  🔎  {rec['keyword']}",      # dict key access
                     font=FT_B, bg=CARD, fg=TEXT, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=rec['extension'],
                     font=FT_MONO, bg=CARD, fg=ACCENT, width=10, anchor="w").pack(side="left")
            tk.Label(row, text=f"{rec['count']} file(s)",
                     font=FT_SM, bg=CARD, fg=GREEN).pack(side="left")


# ==============================================================================
#  SECTION F — SCREEN 2: BROWSE (Folder Selection + Preview + Live Filter)
# ==============================================================================

def show_browse():
    """
    Browse screen.
    User picks a folder; a live-filter bar searches inside it.
    Demonstrates: os.walk, List, List Comprehension, File preview
    """
    clear_window()
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)
    sidebar(outer, active="browse")
    status_bar(outer, "Browse — select a folder.")

    content = tk.Frame(outer, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    page_title(content, "📁  Browse & Select Folder",
               "Pick a folder then filter the preview list to find files.")

    # Path row
    ctrl = tk.Frame(content, bg=BG, pady=10)
    ctrl.pack(fill="x", padx=28)

    global folder_path_var
    folder_path_var = tk.StringVar(value=selected_folder or "No folder selected …")

    tk.Entry(ctrl, textvariable=folder_path_var, font=FT_MONO,
             bg=INP_BG, fg=MUTED, relief="flat", state="readonly", bd=0
             ).pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

    styled_btn(ctrl, "📁  Browse", _pick_folder, width=14, py=6).pack(side="left")

    # Live filter bar
    fbar = tk.Frame(content, bg=CARD, pady=8)
    fbar.pack(fill="x", padx=28, pady=(6, 0))
    tk.Label(fbar, text="  🔎  Search in folder:", font=FT, bg=CARD, fg=MUTED).pack(side="left")

    global browse_filter_var
    browse_filter_var = tk.StringVar()
    tk.Entry(fbar, textvariable=browse_filter_var, font=FT,
             bg=INP_BG, fg=INP_FG, insertbackground=TEXT,
             relief="flat", bd=0, width=36
             ).pack(side="left", ipady=6, padx=8)

    global browse_count_lbl
    browse_count_lbl = tk.Label(fbar, text="0 files", font=FT_SM, bg=CARD, fg=MUTED)
    browse_count_lbl.pack(side="left")

    # Every keystroke refreshes the preview list
    browse_filter_var.trace("w", lambda *_: _refresh_browse())

    # Preview listbox
    lf = tk.Frame(content, bg=INP_BG)
    lf.pack(fill="both", expand=True, padx=28, pady=(0, 8))

    vs = tk.Scrollbar(lf, orient="vertical",   bg=CARD)
    hs = tk.Scrollbar(lf, orient="horizontal", bg=CARD)
    vs.pack(side="right",  fill="y")
    hs.pack(side="bottom", fill="x")

    global browse_lb
    browse_lb = tk.Listbox(lf, font=FT_MONO, bg=INP_BG, fg=TEXT,
                           selectbackground=ACCENT, selectforeground=TEXT,
                           relief="flat", bd=0, activestyle="none",
                           yscrollcommand=vs.set, xscrollcommand=hs.set)
    browse_lb.pack(side="left", fill="both", expand=True)
    vs.config(command=browse_lb.yview)
    hs.config(command=browse_lb.xview)

    # Nav
    nav = tk.Frame(content, bg=BG, pady=10)
    nav.pack(fill="x", padx=28)
    styled_btn(nav, "⌂  Home",       show_welcome,       bg=CARD,  fg=MUTED, width=12, py=6).pack(side="left")
    styled_btn(nav, "Next: Search →", _go_to_search,      bg=GREEN, width=16, py=6).pack(side="right")

    # Reload preview if folder was already chosen
    if selected_folder:
        _refresh_browse()


def _pick_folder():
    """Open OS folder picker; update global selected_folder."""
    global selected_folder
    folder = filedialog.askdirectory(title="Select a Folder to Search")
    if folder:
        selected_folder = folder
        folder_path_var.set(selected_folder)
        browse_filter_var.set("")
        _refresh_browse()


def _refresh_browse():
    """
    Refill the browse listbox based on selected_folder and the filter keyword.
    Uses os.walk() + List Comprehension + Filtering.
    """
    browse_lb.delete(0, tk.END)
    if not selected_folder:
        return

    kw = browse_filter_var.get().strip().lower()

    # List comprehension: build list of matching paths in one line
    all_paths = [
        os.path.join(fp, fn)
        for fp, _, files in os.walk(selected_folder)
        for fn in files
        if (kw == "") or (kw in fn.lower())   # Filtering condition
    ]

    # Sorting the list alphabetically before display
    all_paths.sort()

    for path in all_paths:
        browse_lb.insert(tk.END, "  " + path)

    count = len(all_paths)
    browse_count_lbl.config(text=f"{count} file(s)",
                            fg=GREEN if count > 0 else RED)


def _go_to_search():
    if not selected_folder:
        messagebox.showwarning("No Folder", "Please select a folder first.")
        return
    show_search()


# ==============================================================================
#  SECTION G — SCREEN 3: SEARCH (Keyword + Extension Inputs)
# ==============================================================================

def show_search():
    """
    Search form screen.
    Demonstrates: Entry widgets, List of extension chips (Tuple),
                  Input validation, Dictionary (sort options)
    """
    clear_window()
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)
    sidebar(outer, active="search")
    status_bar(outer, f"Searching inside: {selected_folder}")

    content = tk.Frame(outer, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    page_title(content, "🔍  Search Files", f"Folder: {selected_folder}")

    card = tk.Frame(content, bg=CARD, padx=26, pady=20)
    card.pack(padx=28, pady=14, fill="x")

    # -- Keyword input --------------------------------------------------------
    tk.Label(card, text="FILE NAME KEYWORD", font=FT_SM,
             bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 3))

    kw_row = tk.Frame(card, bg=CARD)
    kw_row.pack(fill="x", pady=(0, 14))
    tk.Label(kw_row, text="🔤", font=("Segoe UI", 13), bg=CARD, fg=ACCENT).pack(side="left", padx=(0, 8))

    global keyword_var
    keyword_var = tk.StringVar()
    kw_e = tk.Entry(kw_row, textvariable=keyword_var, font=FT,
                    bg=INP_BG, fg=INP_FG, insertbackground=TEXT,
                    relief="flat", bd=0, width=46)
    kw_e.pack(side="left", ipady=8)
    kw_e.focus()

    # -- Extension input + quick-pick chips (Tuple of extension strings) ------
    tk.Label(card, text="FILE EXTENSION  (leave blank = all types)", font=FT_SM,
             bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 3))

    ext_row = tk.Frame(card, bg=CARD)
    ext_row.pack(fill="x", pady=(0, 12))
    tk.Label(ext_row, text="📄", font=("Segoe UI", 13), bg=CARD, fg=ACCENT).pack(side="left", padx=(0, 8))

    global extension_var
    extension_var = tk.StringVar(value=".txt")
    tk.Entry(ext_row, textvariable=extension_var, font=FT,
             bg=INP_BG, fg=INP_FG, insertbackground=TEXT,
             relief="flat", bd=0, width=12
             ).pack(side="left", ipady=8)

    # Tuple of quick-pick extension chips (Tuple — immutable, fixed choices)
    ext_chips_tuple = (".txt", ".pdf", ".py", ".docx", ".jpg", ".csv", ".mp4")
    chips_f = tk.Frame(ext_row, bg=CARD)
    chips_f.pack(side="left", padx=12)
    for ext in ext_chips_tuple:   # iterate over Tuple
        chip = tk.Label(chips_f, text=ext, font=FT_SM, bg=BORDER, fg=ACCENT,
                        padx=6, pady=3, cursor="hand2")
        chip.pack(side="left", padx=3)
        chip.bind("<Button-1>", lambda e, x=ext: extension_var.set(x))
        chip.bind("<Enter>",    lambda e, c=chip: c.config(bg=ACCENT, fg=TEXT))
        chip.bind("<Leave>",    lambda e, c=chip: c.config(bg=BORDER, fg=ACCENT))

    # -- Sort option (Dictionary mapping label → key) -------------------------
    sort_opts_dict = {"Sort A→Z by Name": "name", "Sort by Extension": "ext"}

    tk.Label(card, text="SORT RESULTS BY", font=FT_SM,
             bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 3))

    global sort_var
    sort_var = tk.StringVar(value="Sort A→Z by Name")
    sort_row = tk.Frame(card, bg=CARD)
    sort_row.pack(anchor="w", pady=(0, 14))
    for label in sort_opts_dict:   # Dictionary keys
        tk.Radiobutton(sort_row, text=label, variable=sort_var, value=label,
                       font=FT, bg=CARD, fg=TEXT,
                       selectcolor=CARD, activebackground=CARD,
                       activeforeground=ACCENT).pack(side="left", padx=(0, 16))

    hr(card, py=4)

    btn_row = tk.Frame(card, bg=CARD)
    btn_row.pack(pady=(4, 0))
    styled_btn(btn_row, "🔍  Search Files", lambda: _run_search(sort_opts_dict),
               bg=ACCENT, width=18, py=8).pack(side="left", padx=(0, 10))
    styled_btn(btn_row, "✖  Clear",         _clear_inputs,
               bg=CARD, fg=MUTED, width=12, py=8).pack(side="left")

    # Tips
    tips_f = tk.Frame(content, bg=BORDER, padx=16, pady=8)
    tips_f.pack(padx=28, fill="x")
    for tip in ["💡  Keyword blank = match any name.",
                "💡  Extension blank = all file types.",
                "💡  Search is case-insensitive."]:
        tk.Label(tips_f, text=tip, font=FT, bg=BORDER, fg=MUTED, anchor="w").pack(anchor="w")

    nav = tk.Frame(content, bg=BG, pady=10)
    nav.pack(fill="x", padx=28)
    styled_btn(nav, "← Browse", show_browse, bg=CARD, fg=MUTED, width=12, py=6).pack(side="left")


def _clear_inputs():
    keyword_var.set("")
    extension_var.set(".txt")


def _run_search(sort_opts_dict):
    """
    Read inputs, build a FilteredSearchEngine object, run the search,
    save the result to history, then show the results screen.
    """
    global engine, visible_recs

    kw  = keyword_var.get().strip().lower()
    ext = extension_var.get().strip().lower()

    # Input validation
    if not kw and not ext:
        messagebox.showwarning("Empty Search", "Enter a keyword or extension.")
        return

    # Ensure extension starts with a dot
    if ext and not ext.startswith("."):
        ext = "." + ext

    # Get sort key from the Dictionary using the radio-button selection
    sort_key = sort_opts_dict[sort_var.get()]   # Dictionary value lookup

    # Create a FilteredSearchEngine object (OOP — instantiation)
    engine = FilteredSearchEngine(selected_folder, sort_by=sort_key)

    # Run search — method overriding happens here (calls child version)
    engine.search(kw, ext)
    visible_recs = list(engine.get_results())   # List copy

    # Save to history (File Handling inside SearchHistory)
    history.add(kw, ext, len(engine))

    show_results()


# ==============================================================================
#  SECTION H — SCREEN 4: RESULTS
# ==============================================================================

def show_results():
    """
    Results screen.
    Shows the found files, a live filter bar, extension chips from a Set,
    a stats panel from a Dictionary, and double-click to open.
    Demonstrates: List, Set, Dictionary, Tuple, Slicing, List Comprehension
    """
    global visible_recs
    clear_window()
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)
    count = len(engine)
    sidebar(outer, active="results")
    status_bar(outer, f"{count} file(s) found.")

    content = tk.Frame(outer, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    page_title(content, f"📋  Results  —  {count} file(s) found",
               f"Folder: {selected_folder}")

    # ── Stats bar from Dictionary ─────────────────────────────────────────────
    stats = engine.get_stats()   # Returns a Dictionary
    sbar = tk.Frame(content, bg=CARD, padx=20, pady=8)
    sbar.pack(fill="x", padx=28, pady=(8, 4))

    stat_items = [
        ("Files",       stats["total"],      TEXT),
        ("File Types",  stats["types"],      ACCENT),
        ("Total Size",  f"{stats['size_kb']} KB", YELLOW),
    ]
    for label, value, color in stat_items:
        col = tk.Frame(sbar, bg=CARD)
        col.pack(side="left", padx=18)
        tk.Label(col, text=str(value), font=FT_H,  bg=CARD, fg=color).pack()
        tk.Label(col, text=label,      font=FT_SM, bg=CARD, fg=MUTED).pack()

    # ── Extension filter chips from a Set ─────────────────────────────────────
    # get_unique_extensions() returns a Set — convert to sorted List for display
    ext_set  = engine.get_unique_extensions()          # Set
    ext_list = ["ALL"] + sorted(list(ext_set))         # List from Set (with slicing-safe sort)
    # Slicing: show only first 10 extension chips to avoid overflow
    ext_list = ext_list[:11]                           # Slicing

    chips_frame = tk.Frame(content, bg=BG, pady=4)
    chips_frame.pack(fill="x", padx=28)

    global active_ext_filter
    active_ext_filter = tk.StringVar(value="ALL")

    def _apply_ext_filter(ext_val):
        active_ext_filter.set(ext_val)
        filtered = engine.filter_by_ext(ext_val)  # List Comprehension inside method
        _fill_lb(filtered)

    for ext in ext_list:
        chip = tk.Label(chips_frame, text=f"  {ext}  ", font=FT_SM,
                        bg=BORDER, fg=ACCENT, padx=4, pady=4, cursor="hand2")
        chip.pack(side="left", padx=3)
        chip.bind("<Button-1>", lambda e, x=ext: _apply_ext_filter(x))
        chip.bind("<Enter>",    lambda e, c=chip: c.config(bg=ACCENT, fg=TEXT))
        chip.bind("<Leave>",    lambda e, c=chip: c.config(bg=BORDER, fg=ACCENT))

    # ── Live text filter bar ──────────────────────────────────────────────────
    fbar = tk.Frame(content, bg=CARD, pady=7)
    fbar.pack(fill="x", padx=28, pady=(6, 4))
    tk.Label(fbar, text="  🔎  Filter:", font=FT, bg=CARD, fg=MUTED).pack(side="left")

    global res_filter_var
    res_filter_var = tk.StringVar()
    tk.Entry(fbar, textvariable=res_filter_var, font=FT,
             bg=INP_BG, fg=INP_FG, insertbackground=TEXT,
             relief="flat", bd=0, width=38
             ).pack(side="left", ipady=6, padx=8)

    global res_count_lbl
    res_count_lbl = tk.Label(fbar, text=f"{count} shown", font=FT_SM,
                             bg=CARD, fg=GREEN if count > 0 else RED)
    res_count_lbl.pack(side="left")

    res_filter_var.trace("w", lambda *_: _live_filter())

    # ── Listbox + scrollbars ──────────────────────────────────────────────────
    lf = tk.Frame(content, bg=INP_BG)
    lf.pack(fill="both", expand=True, padx=28, pady=(0, 6))

    vs = tk.Scrollbar(lf, orient="vertical",   bg=CARD)
    hs = tk.Scrollbar(lf, orient="horizontal", bg=CARD)
    vs.pack(side="right",  fill="y")
    hs.pack(side="bottom", fill="x")

    global result_lb
    result_lb = tk.Listbox(lf, font=FT_MONO, bg=INP_BG, fg=TEXT,
                           selectbackground=ACCENT, selectforeground=TEXT,
                           relief="flat", bd=0, activestyle="none",
                           yscrollcommand=vs.set, xscrollcommand=hs.set)
    result_lb.pack(side="left", fill="both", expand=True)
    vs.config(command=result_lb.yview)
    hs.config(command=result_lb.xview)

    # Fill listbox initially with all results
    visible_recs = list(engine.get_results())
    _fill_lb(visible_recs)

    result_lb.bind("<Double-Button-1>", _open_file)

    # Info hint
    tk.Label(content, text="💡  Double-click a file to open it.",
             font=FT, bg=BG, fg=MUTED).pack(anchor="w", padx=28)

    # Nav
    nav = tk.Frame(content, bg=BG, pady=8)
    nav.pack(fill="x", padx=28)
    styled_btn(nav, "← New Search", show_search, bg=CARD, fg=MUTED, width=14, py=6).pack(side="left")
    styled_btn(nav, "⌂  Home",       show_welcome, bg=ACCENT,          width=12, py=6).pack(side="right")


def _fill_lb(records):
    """
    Clear and repopulate the results listbox from a List of FileRecord objects.
    Uses to_tuple() to demonstrate Tuple access in display.
    Demonstrates: Tuple indexing
    """
    global visible_recs
    visible_recs = list(records)
    result_lb.delete(0, tk.END)

    if not records:
        result_lb.insert(tk.END, "  No files match.")
        return

    for rec in records:
        info = rec.to_tuple()               # Tuple: (name, path, ext, size)
        size = rec.get_size_str()
        # Display: "[.ext]  size  full_path"
        result_lb.insert(tk.END, f"  [{info[2]:6}]  {size:>8}    {info[1]}")
        #                              tuple[2]=ext          tuple[1]=path

    n = len(records)
    res_count_lbl.config(text=f"{n} shown", fg=GREEN if n > 0 else RED)


def _live_filter():
    """
    Filter visible results by the text typed in the filter entry.
    Demonstrates: List Comprehension + Filtering
    """
    kw = res_filter_var.get().strip().lower()
    # List comprehension — filter the engine's full result list
    filtered = [r for r in engine.get_results() if kw in r.get_path().lower()]
    _fill_lb(filtered)


def _open_file(event=None):
    """
    Open the double-clicked file.
    Uses Tuple: record.to_tuple()[1] for the path.
    """
    sel = result_lb.curselection()
    if not sel:
        return
    idx = sel[0]
    if idx >= len(visible_recs):
        return
    path = visible_recs[idx].get_path()   # Private getter (access specifier)
    try:
        os.startfile(path)
        # Linux  → os.system(f'xdg-open "{path}"')
        # macOS  → os.system(f'open "{path}"')
    except Exception as err:
        messagebox.showerror("Cannot Open", f"Error: {err}")


# ==============================================================================
#  SECTION I — SCREEN 5: ABOUT
# ==============================================================================

def show_about():
    """
    About screen.
    Uses a List of Dictionaries to build the concept grid.
    Demonstrates: List, Dictionary, List Comprehension (for grid display)
    """
    clear_window()
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True)
    sidebar(outer, active="about")
    status_bar(outer, "About this project.")

    content = tk.Frame(outer, bg=BG)
    content.pack(side="left", fill="both", expand=True)
    page_title(content, "ℹ️  About This Project")

    # Scrollable canvas for long content
    canvas = tk.Canvas(content, bg=BG, highlightthickness=0, bd=0)
    vs     = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vs.set)
    vs.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True, padx=(28, 0), pady=8)
    inner = tk.Frame(canvas, bg=BG)
    cw    = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

    # ── Description card ──────────────────────────────────────────────────────
    _about_block(inner, "📝  DESCRIPTION", [
        "Smart File Search Tool searches any folder recursively using os.walk().",
        "Results are sorted, filterable live, and can be opened with a double-click.",
        "Search history is saved to a text file using Python File Handling.",
        "Built entirely with Python standard library — no external packages needed.",
    ])

    # ── Technologies: List of Dictionaries ────────────────────────────────────
    tech_card = tk.Frame(inner, bg=CARD, padx=22, pady=16)
    tech_card.pack(fill="x", pady=(0, 10), padx=(0, 28))
    tk.Label(tech_card, text="🛠️  TECHNOLOGIES USED",
             font=FT_SM, bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 8))

    # List of Dictionaries — each dict holds one technology entry
    tech_list = [
        {"icon": "🐍", "name": "Python 3",           "desc": "Core language"},
        {"icon": "🖼️", "name": "Tkinter",            "desc": "GUI — Frames, Listbox, Entry, Button"},
        {"icon": "📂", "name": "filedialog",          "desc": "OS folder picker"},
        {"icon": "⚠️", "name": "messagebox",          "desc": "Popup alerts"},
        {"icon": "🚶", "name": "os.walk()",           "desc": "Recursive folder traversal"},
        {"icon": "📁", "name": "File Handling",       "desc": "Read/Write search_history.txt"},
        {"icon": "🏗️", "name": "OOP",                "desc": "Classes, Inheritance, Overriding"},
    ]

    for tech in tech_list:   # tech is a Dictionary
        row = tk.Frame(tech_card, bg=BORDER, padx=14, pady=6)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=f"{tech['icon']}  {tech['name']}",
                 font=FT_B, bg=BORDER, fg=ACCENT, width=26, anchor="w").pack(side="left")
        tk.Label(row, text=tech["desc"],
                 font=FT, bg=BORDER, fg=TEXT, anchor="w").pack(side="left")

    # ── Python Concepts: List of Tuples for the grid ──────────────────────────
    conc_card = tk.Frame(inner, bg=CARD, padx=22, pady=16)
    conc_card.pack(fill="x", pady=(0, 10), padx=(0, 28))
    tk.Label(conc_card, text="📚  PYTHON CONCEPTS DEMONSTRATED",
             font=FT_SM, bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 8))

    # Tuple of concept strings (immutable — these won't change)
    concepts_tuple = (
        "List", "Tuple", "Set", "Dictionary",
        "Mutability / Immutability", "Slicing", "Sorting", "Filtering",
        "List Comprehension", "Class", "Object", "Constructor",
        "Access Specifiers", "Inheritance", "Method Overriding", "Operator Overloading",
        "File Handling", "os.walk()", "Tkinter GUI", "Input Validation",
    )

    grid_f = tk.Frame(conc_card, bg=CARD)
    grid_f.pack(anchor="w")
    cols = 4
    # Enumerate over Tuple — display as a grid using .grid() layout
    for i, concept in enumerate(concepts_tuple):
        tk.Label(grid_f, text=f"  {concept}  ", font=FT_SM,
                 bg=BORDER, fg=ACCENT, padx=4, pady=4
                 ).grid(row=i // cols, column=i % cols, padx=5, pady=4, sticky="w")

    # ── OOP Summary ───────────────────────────────────────────────────────────
    _about_block(inner, "🏗️  OOP CLASSES USED", [
        "FileRecord      — stores file data (private/protected, __str__, __eq__, __lt__, __len__)",
        "SearchEngine    — base class with os.walk() search logic",
        "FilteredSearch  — inherits SearchEngine, overrides search() with sort + slice",
        "SearchHistory   — saves/loads Dict records using File Handling",
    ])

    # ── Buttons ───────────────────────────────────────────────────────────────
    btn_f = tk.Frame(inner, bg=BG, pady=16)
    btn_f.pack(fill="x", padx=(0, 28))
    styled_btn(btn_f, "← Back to Home", show_welcome, bg=ACCENT, width=18, py=8).pack(side="left")
    styled_btn(btn_f, "✕  Exit App",    root.quit,    bg=RED,    width=14, py=8).pack(side="left", padx=12)


def _about_block(parent, heading, lines):
    """Helper: render a text card on the About screen."""
    card = tk.Frame(parent, bg=CARD, padx=22, pady=14)
    card.pack(fill="x", pady=(0, 10), padx=(0, 28))
    tk.Label(card, text=heading, font=FT_SM, bg=CARD, fg=MUTED).pack(anchor="w", pady=(0, 6))
    for line in lines:
        tk.Label(card, text=line, font=FT, bg=CARD, fg=TEXT,
                 anchor="w", justify="left").pack(anchor="w", pady=1)


# ==============================================================================
#  SECTION J — MAIN WINDOW
# ==============================================================================

root = tk.Tk()
root.title("Smart File Search Tool")
root.geometry("980x590")
root.minsize(820, 500)
root.resizable(True, True)
root.config(bg=BG)

# Centre window on screen
root.update_idletasks()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"980x590+{(sw-980)//2}+{(sh-590)//2}")

# Launch welcome screen
show_welcome()

# Hand control to Tkinter — must be the last line
root.mainloop()
