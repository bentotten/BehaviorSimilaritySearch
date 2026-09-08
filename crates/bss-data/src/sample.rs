//! The [`Sample`] type: a single unit of data loaded from a source.

use bytes::Bytes;

/// A single unit of data loaded from a source.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Sample {
    /// Identifier for the sample (e.g. filename, object key).
    pub id: String,

    /// Raw, undecoded bytes of the sample.
    pub data: Bytes,
}
