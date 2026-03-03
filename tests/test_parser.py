from __future__ import annotations

from agentlint.parser import parse_unified_diff


def test_parse_single_file_single_hunk() -> None:
    diff = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 line1
-line2
+line2_changed
+line3
"""
    parsed = parse_unified_diff(diff)
    assert len(parsed.files) == 1
    file = parsed.files[0]
    assert file.path == "app.py"
    assert file.added_lines == 2
    assert file.deleted_lines == 1
    assert len(file.hunks) == 1
    additions = file.added_content()
    assert additions == [(2, "line2_changed"), (3, "line3")]


def test_parse_multiple_files() -> None:
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-a
+b
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1 +1 @@
-x
+y
"""
    parsed = parse_unified_diff(diff)
    assert parsed.changed_paths == ["a.py", "b.py"]


def test_parse_binary_file() -> None:
    diff = """diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""
    parsed = parse_unified_diff(diff)
    assert len(parsed.files) == 1
    assert parsed.files[0].is_binary is True


def test_parse_rename() -> None:
    diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
"""
    parsed = parse_unified_diff(diff)
    file = parsed.files[0]
    assert file.is_rename is True
    assert file.old_path == "old.py"
    assert file.new_path == "new.py"
    assert file.path == "new.py"


def test_parse_new_and_deleted_flags() -> None:
    diff = """diff --git a/new.txt b/new.txt
new file mode 100644
--- /dev/null
+++ b/new.txt
@@ -0,0 +1 @@
+hello

diff --git a/dead.txt b/dead.txt
deleted file mode 100644
--- a/dead.txt
+++ /dev/null
@@ -1 +0,0 @@
-bye
"""
    parsed = parse_unified_diff(diff)
    assert parsed.files[0].is_new is True
    assert parsed.files[1].is_deleted is True


def test_parse_ignores_no_newline_marker() -> None:
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-a
+b
\\ No newline at end of file
"""
    parsed = parse_unified_diff(diff)
    assert parsed.files[0].added_lines == 1
    assert parsed.files[0].deleted_lines == 1


def test_parse_empty_diff() -> None:
    parsed = parse_unified_diff("")
    assert parsed.files == []


def test_parse_hunk_header_without_counts() -> None:
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-a
+b
"""
    parsed = parse_unified_diff(diff)
    hunk = parsed.files[0].hunks[0]
    assert hunk.old_count == 1
    assert hunk.new_count == 1


def test_parse_without_diff_header() -> None:
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-a
+b
"""
    parsed = parse_unified_diff(diff)
    assert len(parsed.files) == 1
    assert parsed.files[0].path == "file.txt"


def test_parse_unknown_hunk_line_treated_as_context() -> None:
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,1 +1,1 @@
?a
"""
    parsed = parse_unified_diff(diff)
    line = parsed.files[0].hunks[0].lines[0]
    assert line.prefix == " "
    assert line.content == "?a"
