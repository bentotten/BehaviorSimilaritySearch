//! Error types for bss-core.

use std::path::PathBuf;

use thiserror::Error;

/// Errors that can occur when loading configuration.
#[derive(Debug, Error)]
pub enum ConfigError {
    /// The config path does not exist, or is not a regular file.
    #[error("Config file not found: {0}")]
    FileNotFound(PathBuf),

    /// The file extension is not supported. Only `.env` is accepted.
    #[error("Unsupported config file format '{0}'. Expected a .env file.")]
    UnsupportedFormat(String),

    /// The config file exists but could not be read or parsed line-by-line.
    #[error("Failed to read config file '{path}': {reason}")]
    ReadError { path: PathBuf, reason: String },

    /// One or more environment variables could not be deserialised into the Config struct.
    #[error("Failed to deserialise config from environment: {0}")]
    DeserialisationError(#[from] envy::Error),
}
