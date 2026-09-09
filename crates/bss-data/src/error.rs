//! Error types for bss-data.

use std::io;

use thiserror::Error;

/// Errors related to data.
#[derive(Debug, Error)]
pub enum DataError {
    /// The data source does not exist or is not a valid source location
    /// (e.g. a path that is not a directory).
    #[error("Data source not found: {location}")]
    SourceNotFound { location: String },

    /// The source exists but its contents could not be enumerated
    /// (e.g. insufficient permissions, or an I/O error listing a directory).
    ///
    /// Distinct from [`DataError::SourceNotFound`]: the source was located, but
    /// listing what it contains failed. The underlying [`io::Error`] is
    /// preserved as the error source so callers can inspect its
    /// [`io::ErrorKind`].
    #[error("Failed to enumerate data source '{location}'")]
    SourceUnreadable {
        location: String,
        #[source]
        source: io::Error,
    },

    /// An individual item could not be read from the source.
    ///
    /// `id` is the item's identifier (a filename or object key). The underlying
    /// [`io::Error`] is preserved as the error source so callers can inspect
    /// its [`io::ErrorKind`].
    #[error("Failed to read item '{id}'")]
    ReadError {
        id: String,
        #[source]
        source: io::Error,
    },
}
