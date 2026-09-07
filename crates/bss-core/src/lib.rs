//! Core utilities for BehaviorSimilaritySearch.
//!
//! Provides configuration loading and shared error types used across all crates.

pub mod config;
pub mod error;

pub use config::{
    load_config, parse_config, Config, DEFAULT_MAX_PING_RETRIES, DEFAULT_PING_RETRY_DELAY_SECS,
    DEFAULT_VALKEY_HOST, DEFAULT_VALKEY_PORT,
};
pub use error::ConfigError;
