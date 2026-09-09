//! Integration tests for loading data.

use std::fs;

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
fn skips_directory_with_supported_extension() {
    // A directory whose name ends in a supported extension looks loadable but
    // is not a regular file, so it is skipped rather than loaded or errored.
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    fs::create_dir(dir.path().join("photos.png")).expect("create dir");
    fs::write(dir.path().join("real.png"), b"1").expect("write");

    let samples = load_all(&LocalDirectory::new(dir.path())).expect("should load samples");

    assert_eq!(sorted_ids(&samples), ["real.png"]);
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

    let Err(DataError::ReadError { id, source }) = result else {
        panic!("expected a ReadError, got: {result:?}");
    };
    assert_eq!(id, "locked.png");
    // The underlying io::Error is preserved, so callers can inspect its kind
    // rather than string-matching the message.
    assert_eq!(source.kind(), std::io::ErrorKind::PermissionDenied);
}

// A directory that exists but cannot be listed (read bit removed) must surface
// as SourceUnreadable, distinct from SourceNotFound. Relies on Unix permission
// bits, so it is only compiled on Unix platforms.
#[cfg(unix)]
#[test]
fn returns_source_unreadable_for_unlistable_directory() {
    use std::os::unix::fs::PermissionsExt;

    let dir = tempfile::tempdir().expect("failed to create temp dir");
    let unlistable = dir.path().join("locked_dir");
    fs::create_dir(&unlistable).expect("create dir");
    fs::set_permissions(&unlistable, fs::Permissions::from_mode(0o000)).expect("set permissions");

    // Restore permissions on the way out so TempDir cleanup can remove it.
    struct RestorePermissions(std::path::PathBuf);
    impl Drop for RestorePermissions {
        fn drop(&mut self) {
            let _ = fs::set_permissions(&self.0, fs::Permissions::from_mode(0o755));
        }
    }
    let _restore = RestorePermissions(unlistable.clone());

    // Permission enforcement is a runtime property (root and some filesystems
    // ignore it). If the directory is still listable, the precondition does not
    // hold and the test would fail falsely, so skip instead.
    if fs::read_dir(&unlistable).is_ok() {
        eprintln!(
            "skipping returns_source_unreadable_for_unlistable_directory: \
             permission bits are not enforced in this environment (e.g. running as root)"
        );
        return;
    }

    let source = LocalDirectory::new(&unlistable);
    let result = source.load_data();

    assert!(matches!(
        result.err(),
        Some(DataError::SourceUnreadable { .. })
    ));
}

// A single unreadable item must yield an Err for that item without preventing
// the readable items from being yielded. Iterating item by item (rather than
// collecting into a Result) verifies the per-item contract. Relies on Unix
// permission bits to make one item unreadable.
#[cfg(unix)]
#[test]
fn iteration_survives_per_item_errors() {
    use std::os::unix::fs::PermissionsExt;

    let dir = dir_with_files(&[("good.png", b"ok"), ("bad.png", b"secret")]);
    let bad = dir.path().join("bad.png");
    fs::set_permissions(&bad, fs::Permissions::from_mode(0o000)).expect("set permissions");

    // Permission enforcement is a runtime property (root and some filesystems
    // ignore it). If the file is still readable, the precondition does not hold
    // and the test would fail falsely, so skip instead.
    if fs::read(&bad).is_ok() {
        eprintln!(
            "skipping iteration_survives_per_item_errors: \
             permission bits are not enforced in this environment (e.g. running as root)"
        );
        return;
    }

    let source = LocalDirectory::new(dir.path());
    let mut ok_ids = Vec::new();
    let mut error_count = 0;
    for result in source.load_data().expect("source should open") {
        match result {
            Ok(sample) => ok_ids.push(sample.id),
            Err(DataError::ReadError { .. }) => error_count += 1,
            Err(other) => panic!("unexpected error: {other:?}"),
        }
    }

    assert_eq!(
        ok_ids,
        ["good.png"],
        "the readable sample should still be yielded"
    );
    assert_eq!(error_count, 1, "the unreadable item should yield one error");
}
