//! Confirms bss-core compiles and its public API is reachable.

use std::path::Path;

use bss_core::{
    load_config, Config, ConfigError, DEFAULT_MAX_PING_RETRIES, DEFAULT_PING_RETRY_DELAY_SECS,
    DEFAULT_VALKEY_HOST, DEFAULT_VALKEY_PORT,
};

#[test]
fn bss_core_is_importable() {
    // Verify all public symbols are reachable.
    let config = Config::default();
    assert_eq!(config.valkey_host, DEFAULT_VALKEY_HOST);
    assert_eq!(config.valkey_port, DEFAULT_VALKEY_PORT);
    assert_eq!(config.valkey_ping_max_retries, DEFAULT_MAX_PING_RETRIES);
    assert_eq!(
        config.valkey_ping_retry_delay_secs,
        DEFAULT_PING_RETRY_DELAY_SECS
    );
}

#[test]
fn load_config_reachable() {
    // Confirms load_config is callable and returns a typed error for a missing file.
    let result = load_config(Path::new("/nonexistent/config.env"));
    assert!(matches!(result, Err(ConfigError::FileNotFound(_))));
}
