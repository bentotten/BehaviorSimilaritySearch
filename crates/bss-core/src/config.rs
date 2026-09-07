//! Configuration loading for BehaviorSimilaritySearch.

use std::path::Path;

use serde::Deserialize;

use crate::error::ConfigError;

/// Default Valkey server hostname.
pub const DEFAULT_VALKEY_HOST: &str = "127.0.0.1";

/// Default Valkey server port.
pub const DEFAULT_VALKEY_PORT: u16 = 6379;

/// Default maximum number of ping attempts before giving up.
pub const DEFAULT_MAX_PING_RETRIES: usize = 5;

/// Default seconds to wait between ping attempts.
pub const DEFAULT_PING_RETRY_DELAY_SECS: u64 = 2;

fn default_valkey_host() -> String {
    DEFAULT_VALKEY_HOST.to_string()
}

fn default_valkey_port() -> u16 {
    DEFAULT_VALKEY_PORT
}

fn default_valkey_ping_max_retries() -> usize {
    DEFAULT_MAX_PING_RETRIES
}

fn default_valkey_ping_retry_delay_secs() -> u64 {
    DEFAULT_PING_RETRY_DELAY_SECS
}

/// Runtime configuration.
#[derive(Debug, Deserialize, PartialEq)]
pub struct Config {
    /// Valkey server hostname or IP address.
    #[serde(default = "default_valkey_host")]
    pub valkey_host: String,

    /// Valkey server port.
    #[serde(default = "default_valkey_port")]
    pub valkey_port: u16,

    /// Maximum number of ping retries on startup.
    #[serde(default = "default_valkey_ping_max_retries")]
    pub valkey_ping_max_retries: usize,

    /// Seconds to wait between ping retries.
    #[serde(
        default = "default_valkey_ping_retry_delay_secs",
        rename = "valkey_ping_retry_delay"
    )]
    pub valkey_ping_retry_delay_secs: u64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            valkey_host: default_valkey_host(),
            valkey_port: default_valkey_port(),
            valkey_ping_max_retries: default_valkey_ping_max_retries(),
            valkey_ping_retry_delay_secs: default_valkey_ping_retry_delay_secs(),
        }
    }
}

/// Deserialise configuration from key/value pairs.
///
/// # Errors
///
/// - [`ConfigError::DeserialisationError`] if a value cannot be deserialised
///   into its expected type.
pub fn parse_config<I>(pairs: I) -> Result<Config, ConfigError>
where
    I: IntoIterator<Item = (String, String)>,
{
    Ok(envy::from_iter(pairs)?)
}

/// Load configuration from a `.env` file at the given path.
///
/// # Errors
///
/// - [`ConfigError::FileNotFound`] if the path does not exist or is not a
///   regular file (e.g. a directory).
/// - [`ConfigError::UnsupportedFormat`] if the extension is not `.env`.
/// - [`ConfigError::ReadError`] if the file exists but cannot be read or a
///   line cannot be parsed into a key/value pair.
/// - [`ConfigError::DeserialisationError`] if a value cannot be deserialised
///   into its expected type.
pub fn load_config(path: &Path) -> Result<Config, ConfigError> {
    // Require a regular file: directories and other non-file paths are not
    // valid config sources and cannot be read line-by-line.
    if !path.is_file() {
        return Err(ConfigError::FileNotFound(path.to_path_buf()));
    }

    match path.extension().and_then(|ext| ext.to_str()) {
        Some("env") => {}
        other => {
            return Err(ConfigError::UnsupportedFormat(
                other.unwrap_or("").to_string(),
            ));
        }
    }

    // Read the file into key/value pairs, surfacing read failures rather than
    // discarding them.
    let iter = dotenvy::from_path_iter(path).map_err(|error| ConfigError::ReadError {
        path: path.to_path_buf(),
        reason: error.to_string(),
    })?;

    let mut pairs = Vec::new();
    for item in iter {
        let (key, value) = item.map_err(|error| ConfigError::ReadError {
            path: path.to_path_buf(),
            reason: error.to_string(),
        })?;
        pairs.push((key, value));
    }

    parse_config(pairs)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Helper to build owned key/value pairs from string literals.
    fn pairs(items: &[(&str, &str)]) -> Vec<(String, String)> {
        items
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_string()))
            .collect()
    }

    #[test]
    fn parses_all_values() {
        let config = parse_config(pairs(&[
            ("VALKEY_HOST", "192.168.1.1"),
            ("VALKEY_PORT", "6380"),
            ("VALKEY_PING_MAX_RETRIES", "3"),
            ("VALKEY_PING_RETRY_DELAY", "5"),
        ]))
        .expect("should parse config");

        assert_eq!(config.valkey_host, "192.168.1.1");
        assert_eq!(config.valkey_port, 6380);
        assert_eq!(config.valkey_ping_max_retries, 3);
        assert_eq!(config.valkey_ping_retry_delay_secs, 5);
    }

    #[test]
    fn applies_defaults_for_missing_keys() {
        let config = parse_config(pairs(&[])).expect("should parse config with defaults");

        assert_eq!(config, Config::default());
    }

    #[test]
    fn applies_partial_defaults() {
        // Only host is provided; everything else falls back to defaults.
        let config = parse_config(pairs(&[("VALKEY_HOST", "10.0.0.1")]))
            .expect("should parse config with partial defaults");

        assert_eq!(config.valkey_host, "10.0.0.1");
        assert_eq!(config.valkey_port, DEFAULT_VALKEY_PORT);
        assert_eq!(config.valkey_ping_max_retries, DEFAULT_MAX_PING_RETRIES);
        assert_eq!(
            config.valkey_ping_retry_delay_secs,
            DEFAULT_PING_RETRY_DELAY_SECS
        );
    }

    #[test]
    fn returns_deserialisation_error_for_non_numeric_port() {
        let result = parse_config(pairs(&[("VALKEY_PORT", "foo")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_non_numeric_max_retries() {
        let result = parse_config(pairs(&[("VALKEY_PING_MAX_RETRIES", "bar")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_non_numeric_retry_delay() {
        let result = parse_config(pairs(&[("VALKEY_PING_RETRY_DELAY", "foobar")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_port_above_u16_max() {
        // 99999 exceeds u16::MAX (65535).
        let result = parse_config(pairs(&[("VALKEY_PORT", "99999")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_negative_port() {
        let result = parse_config(pairs(&[("VALKEY_PORT", "-1")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_negative_max_retries() {
        let result = parse_config(pairs(&[("VALKEY_PING_MAX_RETRIES", "-5")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_empty_numeric_value() {
        // An empty string is not a valid u16.
        let result = parse_config(pairs(&[("VALKEY_PORT", "")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }

    #[test]
    fn returns_deserialisation_error_for_float_port() {
        // A float is not a valid integer port.
        let result = parse_config(pairs(&[("VALKEY_PORT", "63.79")]));

        assert!(matches!(result, Err(ConfigError::DeserialisationError(_))));
    }
}
