//! Integration tests for loading data.

use std::fs;
use std::path::Path;

use bss_data::{DataError, DataSource, LocalDirectory, Sample};
use tempfile::TempDir;

/// Create a temp directory containing the given (name, contents) files.
fn dir_with_files(files: &[(&str, &[u8])]) -> TempDir {
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    for (name, contents) in files {
        fs::write(dir.path().join(name), contents).expect("failed to write file");
    }
    dir
}

/// Load all samples from a source into a vector, failing on the first error.
fn load_all(source: &LocalDirectory) -> Result<Vec<Sample>, DataError> {
    source.load_data()?.collect()
}

/// Collect sample ids, sorted, so assertions do not depend on iteration order.
fn sorted_ids(samples: &[Sample]) -> Vec<&str> {
    let mut ids: Vec<&str> = samples.iter().map(|sample| sample.id.as_str()).collect();
    ids.sort_unstable();
    ids
}

#[test]
fn loads_supported_files_as_samples() {
    let dir = dir_with_files(&[("a.png", b"png-bytes"), ("b.jpg", b"jpg-bytes")]);

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert_eq!(sorted_ids(&samples), ["a.png", "b.jpg"]);
}

#[test]
fn preserves_raw_bytes() {
    let dir = dir_with_files(&[("frame.png", b"exact-bytes")]);

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

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

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert_eq!(sorted_ids(&samples), ["alpha.png", "delta.jpeg"]);
}

#[test]
fn matches_extensions_case_insensitively() {
    let dir = dir_with_files(&[("UPPER.PNG", b"1"), ("Mixed.Jpeg", b"2")]);

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert_eq!(samples.len(), 2);
}

#[test]
fn returns_empty_for_directory_with_no_supported_files() {
    let dir = dir_with_files(&[("bravo.txt", b"1"), ("data.bin", b"2")]);

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert!(samples.is_empty());
}

#[test]
fn returns_empty_for_empty_directory() {
    let dir = tempfile::tempdir().expect("failed to create temp dir");

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert!(samples.is_empty());
}

#[test]
fn does_not_traverse_subdirectories() {
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    fs::write(dir.path().join("top.png"), b"1").expect("write");
    let nested = dir.path().join("nested");
    fs::create_dir(&nested).expect("create dir");
    fs::write(nested.join("deep.png"), b"2").expect("write");

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert_eq!(sorted_ids(&samples), ["top.png"]);
}

#[test]
fn returns_source_not_found_for_missing_directory() {
    let source = LocalDirectory::new("/nonexistent/path/to/data");

    let result = source.load_data();

    assert!(matches!(
        result.err(),
        Some(DataError::SourceNotFound { .. })
    ));
}

#[test]
fn returns_source_not_found_when_path_is_a_file() {
    let dir = dir_with_files(&[("a.png", b"1")]);
    let source = LocalDirectory::new(dir.path().join("a.png"));

    let result = source.load_data();

    assert!(matches!(
        result.err(),
        Some(DataError::SourceNotFound { .. })
    ));
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

    let result = load_all(&LocalDirectory::new(dir.path()));

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

    let samples =
        load_all(&LocalDirectory::new(workspace_root.join("data/sample"))).expect("should load");

    let cat = samples
        .iter()
        .find(|sample| sample.id == "my_cat_in_a_bucket.jpeg")
        .expect("expected the sample image to be loaded");
    assert!(!cat.data.is_empty(), "loaded sample should contain bytes");
}
