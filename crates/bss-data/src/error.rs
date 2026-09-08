//! Error types for bss-data.

use thiserror::Error;

/// Errors related to data.
#[derive(Debug, Error)]
pub enum DataError {
    /// The data source could not be found or is not a valid source location.
    #[error("Data source not found: {location}")]
    SourceNotFound { location: String },

    /// An individual item could not be read from the source.
    ///
    /// `id` is the item's identifier (a filename or object key).
    #[error("Failed to read item '{id}': {reason}")]
    ReadError { id: String, reason: String },
}
