import os
from unittest.mock import MagicMock

from modes.files import FilesMode
from providers.files import CODE_EXTENSIONS, EXT_MAP, IGNORE_DIRS, FileProvider


def test_document_extensions_categorization():
    """Verify all major document formats map to Documents or PDF."""
    test_docs = [
        (".pdf", "PDF"),
        (".doc", "Documents"),
        (".docx", "Documents"),
        (".odt", "Documents"),
        (".rtf", "Documents"),
        (".txt", "Documents"),
        (".md", "Documents"),
        (".xlsx", "Documents"),
        (".xls", "Documents"),
        (".pptx", "Documents"),
        (".ppt", "Documents"),
        (".odp", "Documents"),
        (".ods", "Documents"),
        (".odg", "Documents"),
        (".epub", "Documents"),
        (".fb2", "Documents"),
        (".djvu", "Documents"),
    ]
    for ext, expected_cat in test_docs:
        assert ext in EXT_MAP, f"Extension {ext} must be present in EXT_MAP"
        mime, cat = EXT_MAP[ext]
        assert cat == expected_cat, f"Expected {expected_cat} for {ext}, got {cat}"


def test_code_extensions_separated():
    """Code extensions should not be in EXT_MAP with Documents category."""
    for ext in CODE_EXTENSIONS:
        if ext in EXT_MAP:
            _, cat = EXT_MAP[ext]
            assert cat != "Documents", f"Code extension {ext} must not have category Documents"


def test_create_result_category_inference():
    """FileProvider._create_result correctly identifies document categories."""
    fp = FileProvider(history_manager=None)

    # PDF
    res_pdf = fp._create_result("/tmp/test.pdf", "test.pdf", "application/pdf", 50)
    assert res_pdf.preview_data.get("category") == "PDF"

    # Word doc
    res_doc = fp._create_result("/tmp/task.doc", "task.doc", "application/msword", 50)
    assert res_doc.preview_data.get("category") == "Documents"

    # OpenDocument
    res_odt = fp._create_result("/tmp/notes.odt", "notes.odt", "application/vnd.oasis.opendocument.text", 50)
    assert res_odt.preview_data.get("category") == "Documents"

    # E-book
    res_epub = fp._create_result("/tmp/book.epub", "book.epub", "application/epub+zip", 50)
    assert res_epub.preview_data.get("category") == "Documents"

    # Unknown Minecraft chunk file -> Other (NOT Documents)
    res_mca = fp._create_result("/tmp/r.0.0.mca", "r.0.0.mca", "application/octet-stream", 50)
    assert res_mca.preview_data.get("category") == "Other"

    # Python source file -> Code (NOT Documents)
    res_py = fp._create_result("/tmp/app.py", "app.py", "text/x-python", 50)
    assert res_py.preview_data.get("category") == "Code"


def test_scan_folder_buckets_no_binaries_in_documents(tmp_path):
    """Verify that scanning a folder puts docs into Documents and ignores binary chunk files."""
    doc_file = tmp_path / "MyDoc.docx"
    doc_file.write_text("dummy")

    pdf_file = tmp_path / "Guide.pdf"
    pdf_file.write_text("dummy")

    chunk_file = tmp_path / "r.0.0.mca"
    chunk_file.write_bytes(b"\x00\x01\x02")

    dat_file = tmp_path / "level.dat"
    dat_file.write_bytes(b"\x00\x01")

    py_file = tmp_path / "script.py"
    py_file.write_text("print(1)")

    buckets = {k: [] for k in ["All", "PDF", "Documents", "Images", "Videos", "Audio", "Folders", "Archives"]}

    for entry in os.scandir(tmp_path):
        ext = os.path.splitext(entry.name)[1].lower()
        cat = "Other"
        mime = "application/octet-stream"
        if ext in EXT_MAP:
            mime, cat = EXT_MAP[ext]
        elif ext in CODE_EXTENSIONS:
            cat = "Code"
        st = entry.stat()
        item = {
            "name": entry.name,
            "name_lower": entry.name.lower(),
            "path": entry.path,
            "mime": mime,
            "category": cat,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "is_dir": False
        }
        if cat in buckets:
            buckets[cat].append(item)
        if cat == "PDF":
            buckets["Documents"].append(item)

    doc_names = [x["name"] for x in buckets["Documents"]]
    assert "MyDoc.docx" in doc_names
    assert "Guide.pdf" in doc_names
    assert "r.0.0.mca" not in doc_names
    assert "level.dat" not in doc_names
    assert "script.py" not in doc_names


def test_ignore_dirs_includes_game_and_env():
    """Verify that game and virtualenv directories are blacklisted."""
    for d in ["games", "steam", ".minecraft", "venv", "python_env", "node_modules"]:
        assert d in IGNORE_DIRS, f"{d} should be in IGNORE_DIRS"


def test_files_mode_filter_func():
    """Verify FilesMode._filter_func accepts all document formats and rejects non-docs."""
    mw = MagicMock()
    mw.config_manager.get.return_value = "space"
    mw.entry.get_text.return_value = ""

    fm = FilesMode(mw)
    fm.active_category = "Documents"

    fp = FileProvider(history_manager=None)

    # Valid documents should PASS
    valid_files = [
        ("/home/user/Doc.pdf", "Doc.pdf", "application/pdf"),
        ("/home/user/Задания.doc", "Задания.doc", "application/msword"),
        ("/home/user/Report.docx", "Report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("/home/user/Notes.odt", "Notes.odt", "application/vnd.oasis.opendocument.text"),
        ("/home/user/Data.xlsx", "Data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("/home/user/Slide.pptx", "Slide.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("/home/user/Book.epub", "Book.epub", "application/epub+zip"),
        ("/home/user/Novel.fb2", "Novel.fb2", "application/x-fictionbook+xml"),
        ("/home/user/Paper.djvu", "Paper.djvu", "image/vnd.djvu"),
        ("/home/user/Draw.odg", "Draw.odg", "application/vnd.oasis.opendocument.graphics"),
        ("/home/user/README.md", "README.md", "text/markdown"),
        ("/home/user/todo.txt", "todo.txt", "text/plain"),
    ]

    for path, name, mime in valid_files:
        res = fp._create_result(path, name, mime, 50)
        child = MagicMock()
        child.result = res
        assert fm._filter_func(child) is True, f"Failed to pass document filter for {name} ({mime})"

    # Non-documents should be REJECTED under active_category == 'Documents'
    invalid_files = [
        ("/home/user/r.0.0.mca", "r.0.0.mca", "application/octet-stream"),
        ("/home/user/libfoo.so", "libfoo.so", "application/x-sharedlib"),
        ("/home/user/save.dat", "save.dat", "application/octet-stream"),
        ("/home/user/photo.jpg", "photo.jpg", "image/jpeg"),
        ("/home/user/song.mp3", "song.mp3", "audio/mpeg"),
        ("/home/user/archive.zip", "archive.zip", "application/zip"),
    ]

    for path, name, mime in invalid_files:
        res = fp._create_result(path, name, mime, 50)
        child = MagicMock()
        child.result = res
        assert fm._filter_func(child) is False, f"Non-document {name} must be rejected under Documents filter"
