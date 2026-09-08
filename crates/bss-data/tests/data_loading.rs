//! Integration tests for loading data.

use std::fs;
use std::path::Path;

use bss_data::{DataError, DataSource, LocalDirectory};
use tempfile::TempDir;

/// Create a temp directory containing the given (name, contents) files.
fn dir_with_files(files: &[(&str, &[u8])]) -> TempDir {
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    for (name, contents) in files {
        fs::write(dir.path().join(name), contents).expect("failed to write file");
    }
    dir
}

#[test]
fn loads_supported_files_as_samples() {
    let dir = dir_with_files(&[("a.png", b"png-bytes"), ("b.jpg", b"jpg-bytes")]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    assert_eq!(samples.len(), 2);
    let ids: Vec<&str> = samples.iter().map(|s| s.id.as_str()).collect();
    assert_eq!(ids, ["a.png", "b.jpg"]);
}

#[test]
fn preserves_raw_bytes() {
    let dir = dir_with_files(&[("frame.png", b"exact-bytes")]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    assert_eq!(samples.len(), 1);
    assert_eq!(samples[0].data, b"exact-bytes"[..]);
}

#[test]
fn filters_out_unsupported_files() {
    let dir = dir_with_files(&[
        ("alpha.png", b"1"),
        ("bravo.txt", b"2"),
        ("charlie.mp4", b"3"),
        ("delta.jpeg", b"4"),
    ]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    let ids: Vec<&str> = samples.iter().map(|s| s.id.as_str()).collect();
    assert_eq!(ids, ["alpha.png", "delta.jpeg"]);
}

#[test]
fn matches_extensions_case_insensitively() {
    let dir = dir_with_files(&[("UPPER.PNG", b"1"), ("Mixed.Jpeg", b"2")]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    assert_eq!(samples.len(), 2);
}

#[test]
fn returns_samples_sorted_by_id() {
    let dir = dir_with_files(&[("c.png", b"1"), ("a.png", b"2"), ("b.png", b"3")]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    let ids: Vec<&str> = samples.iter().map(|s| s.id.as_str()).collect();
    assert_eq!(ids, ["a.png", "b.png", "c.png"]);
}

#[test]
fn returns_empty_for_directory_with_no_supported_files() {
    let dir = dir_with_files(&[("bravo.txt", b"1"), ("data.bin", b"2")]);

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    assert!(samples.is_empty());
}

#[test]
fn returns_empty_for_empty_directory() {
    let dir = tempfile::tempdir().expect("failed to create temp dir");

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    assert!(samples.is_empty());
}

#[test]
fn does_not_traverse_subdirectories() {
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    fs::write(dir.path().join("top.png"), b"1").expect("write");
    let nested = dir.path().join("nested");
    fs::create_dir(&nested).expect("create dir");
    fs::write(nested.join("deep.png"), b"2").expect("write");

    let samples = LocalDirectory::new(dir.path())
        .load_data()
        .expect("should load samples");

    let ids: Vec<&str> = samples.iter().map(|s| s.id.as_str()).collect();
    assert_eq!(ids, ["top.png"]);
}

#[test]
fn returns_source_not_found_for_missing_directory() {
    let result = LocalDirectory::new("/nonexistent/path/to/data").load_data();

    assert!(matches!(result, Err(DataError::SourceNotFound { .. })));
}

#[test]
fn returns_source_not_found_when_path_is_a_file() {
    let dir = dir_with_files(&[("a.png", b"1")]);
    let file_path = dir.path().join("a.png");

    let result = LocalDirectory::new(&file_path).load_data();

    assert!(matches!(result, Err(DataError::SourceNotFound { .. })));
}

// Relies on Unix permission bits to make a file unreadable, only available
// on Unix based platforms.
#[cfg(unix)]
#[test]
fn returns_read_error_for_unreadable_file() {
    use std::os::unix::fs::PermissionsExt;

    let dir = dir_with_files(&[("locked.png", b"secret")]);
    let file_path = dir.path().join("locked.png");
    fs::set_permissions(&file_path, fs::Permissions::from_mode(0o000)).expect("set permissions");

    // Whether permission bits are enforced is a runtime property (root and some
    // filesystems ignore them), so it cannot be gated with cfg. Probe directly:
    // if the file is still readable, the unreadable precondition does not hold
    // and the test would fail falsely, so skip instead.
    if fs::read(&file_path).is_ok() {
        eprintln!(
            "skipping returns_read_error_for_unreadable_file: \
             permission bits are not enforced in this environment (e.g. running as root)"
        );
        return;
    }

    let result = LocalDirectory::new(dir.path()).load_data();

    assert!(matches!(
        result,
        Err(DataError::ReadError { id, .. }) if id == "locked.png"
    ));
}

#[test]
fn loads_checked_in_sample_directory() {
    // The checked-in sample directory must load cleanly and contain the sample
    // image. Specific counts beyond "at least one" are not asserted so that
    // adding sample data does not break this test.
    let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("..");

    let samples = LocalDirectory::new(workspace_root.join("data/sample"))
        .load_data()
        .expect("should load sample directory");

    assert!(
        samples.iter().any(|s| s.id == "my_cat_in_a_bucket.jpeg"),
        "expected the sample image to be loaded, got: {:?}",
        samples.iter().map(|s| &s.id).collect::<Vec<_>>()
    );
    assert!(
        !samples[0].data.is_empty(),
        "loaded sample should contain bytes"
    );
}
