//! Integration tests for `load_config`.

use std::io::Write;
use std::path::Path;

use bss_core::{load_config, ConfigError};
use tempfile::NamedTempFile;

/// Write contents to a temp file with the given suffix and return the handle.
fn temp_file_with_suffix(suffix: &str, contents: &str) -> NamedTempFile {
    let mut file = tempfile::Builder::new()
        .suffix(suffix)
        .tempfile()
        .expect("failed to create temp file");
    write!(file, "{contents}").expect("failed to write temp file");
    file
}

#[test]
fn loads_values_from_real_env_file() {
    let file = temp_file_with_suffix(
        ".env",
        "VALKEY_HOST=192.168.1.1\nVALKEY_PORT=6380\nVALKEY_PING_MAX_RETRIES=3\nVALKEY_PING_RETRY_DELAY=5\n",
    );

    let config = load_config(file.path()).expect("should load config from file");

    assert_eq!(config.valkey_host, "192.168.1.1");
    assert_eq!(config.valkey_port, 6380);
    assert_eq!(config.valkey_ping_max_retries, 3);
    assert_eq!(config.valkey_ping_retry_delay_secs, 5);
}

#[test]
fn applies_defaults_for_empty_env_file() {
    let file = temp_file_with_suffix(".env", "");

    let config = load_config(file.path()).expect("should load config with defaults");

    assert_eq!(config, bss_core::Config::default());
}

#[test]
fn loads_checked_in_local_env_file_without_error() {
    // The checked-in config must parse cleanly. Specific values are not asserted
    // here so that legitimate local edits to local.env do not break this test;
    // default-value behaviour is covered by the unit tests.
    let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("..");

    let result = load_config(&workspace_root.join("configs/local.env"));

    assert!(
        result.is_ok(),
        "local.env should load without error: {result:?}"
    );
}

#[test]
fn returns_file_not_found_for_missing_path() {
    let result = load_config(Path::new("/nonexistent/path/config.env"));

    assert!(matches!(result, Err(ConfigError::FileNotFound(_))));
}

#[test]
fn returns_unsupported_format_for_non_env_extension() {
    let file = temp_file_with_suffix(".yaml", "VALKEY_HOST=127.0.0.1\n");

    let result = load_config(file.path());

    assert!(matches!(result, Err(ConfigError::UnsupportedFormat(_))));
}

#[test]
fn returns_unsupported_format_for_no_extension() {
    // A file with no extension should be rejected before any parsing.
    let file = tempfile::Builder::new()
        .prefix("noext")
        .rand_bytes(6)
        .tempfile()
        .expect("failed to create temp file");

    let result = load_config(file.path());

    assert!(matches!(result, Err(ConfigError::UnsupportedFormat(_))));
}

#[test]
fn extension_check_is_case_sensitive() {
    // Extension matching is case-sensitive: only a lowercase `.env` is accepted.
    let file = temp_file_with_suffix(".ENV", "VALKEY_PORT=6380\n");

    let result = load_config(file.path());

    assert!(matches!(result, Err(ConfigError::UnsupportedFormat(_))));
}

#[test]
fn propagates_deserialisation_error_from_file_contents() {
    // A malformed value in a real .env file must surface as a
    // DeserialisationError through the full file-loading path.
    let file = temp_file_with_suffix(".env", "VALKEY_PORT=not_a_number\n");

    let result = load_config(file.path());

    assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
}

#[test]
fn returns_file_not_found_when_path_is_a_directory() {
    // A directory is not a valid config source even when its name ends in `.env`.
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    let env_dir = dir.path().join("config.env");
    std::fs::create_dir(&env_dir).expect("failed to create dir");

    let result = load_config(&env_dir);

    assert!(matches!(result, Err(ConfigError::FileNotFound(_))));
}

#[test]
fn returns_file_not_found_when_path_is_a_directory_without_env_extension() {
    // A non-file path is rejected regardless of its extension.
    let dir = tempfile::tempdir().expect("failed to create temp dir");

    let result = load_config(dir.path());

    assert!(matches!(result, Err(ConfigError::FileNotFound(_))));
}
