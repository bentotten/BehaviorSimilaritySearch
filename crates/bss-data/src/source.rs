//! The [`DataSource`] trait.

use std::fs;
use std::path::{Path, PathBuf};

use bytes::Bytes;
use tracing::warn;

use crate::error::DataError;
use crate::sample::Sample;

/// Extensions recognised as loadable samples, compared case-insensitively.
///
/// Video-chunk extensions will be added here when video bootstrapping lands.
pub const SUPPORTED_EXTENSIONS: &[&str] = &["jpg", "jpeg", "png"];

/// A source of [`Sample`]s for bootstrapping.
pub trait DataSource {
    /// Return an iterator over the samples in the source.
    ///
    /// Samples are yielded lazily so that arbitrarily large sources can be
    /// processed with bounded memory: the caller drives the iterator.
    ///
    /// # Notes
    //  - Iteration order is unspecified.
    ///
    /// # Errors
    ///
    /// - [`DataError::SourceNotFound`] if the source location does not exist or
    ///   is not a valid source.
    /// - [`DataError::ReadError`] (per item) if an individual sample cannot be
    ///   read.
    fn load_data(
        &self,
    ) -> Result<Box<dyn Iterator<Item = Result<Sample, DataError>> + '_>, DataError>;
}

/// A [`DataSource`] backed by a local filesystem directory.
///
/// # Notes
///
///  - Subdirectories are not traversed.
#[derive(Debug, Clone)]
pub struct LocalDirectory {
    root: PathBuf,
}

impl LocalDirectory {
    /// Create a DataSource rooted at the given directory.
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self { root: root.into() }
    }
}

impl DataSource for LocalDirectory {
    fn load_data(
        &self,
    ) -> Result<Box<dyn Iterator<Item = Result<Sample, DataError>> + '_>, DataError> {
        if !self.root.is_dir() {
            return Err(DataError::SourceNotFound {
                location: self.root.display().to_string(),
            });
        }

        let entries = fs::read_dir(&self.root).map_err(|error| DataError::SourceNotFound {
            location: format!("{}: {error}", self.root.display()),
        })?;

        let samples = entries.filter_map(|entry| match entry {
            Ok(entry) => read_supported_sample(&entry.path()),
            Err(error) => Some(Err(DataError::ReadError {
                id: String::new(),
                reason: error.to_string(),
            })),
        });

        Ok(Box::new(samples))
    }
}

/// Read a single sample from a path, or `None` if it is not a supported file.
///
/// Returns `Some(Err(..))` when a supported file exists but cannot be read.
fn read_supported_sample(path: &Path) -> Option<Result<Sample, DataError>> {
    if !is_supported_file(path) {
        warn!(path = %path.display(), "skipping unsupported file");
        return None;
    }

    let id = file_id(path);
    let sample = fs::read(path)
        .map(|bytes| Sample {
            id: id.clone(),
            data: Bytes::from(bytes),
        })
        .map_err(|error| DataError::ReadError {
            id,
            reason: error.to_string(),
        });

    Some(sample)
}

fn is_supported_file(path: &Path) -> bool {
    path.is_file() && has_supported_extension(path)
}

fn has_supported_extension(path: &Path) -> bool {
    match path.extension().and_then(|extension| extension.to_str()) {
        Some(extension) => {
            let extension = extension.to_ascii_lowercase();
            SUPPORTED_EXTENSIONS.contains(&extension.as_str())
        }
        None => false,
    }
}

// Falls back to the full path when a file name cannot be extracted, so every
// sample retains a usable identifier.
fn file_id(path: &Path) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .map(str::to_string)
        .unwrap_or_else(|| path.display().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recognises_supported_extensions() {
        assert!(has_supported_extension(Path::new("frame.jpg")));
        assert!(has_supported_extension(Path::new("frame.jpeg")));
        assert!(has_supported_extension(Path::new("frame.png")));
    }

    #[test]
    fn extension_matching_is_case_insensitive() {
        assert!(has_supported_extension(Path::new("frame.JPG")));
        assert!(has_supported_extension(Path::new("frame.Png")));
        assert!(has_supported_extension(Path::new("frame.JPEG")));
    }

    #[test]
    fn rejects_unsupported_extensions() {
        assert!(!has_supported_extension(Path::new("notes.txt")));
        assert!(!has_supported_extension(Path::new("archive.tar.gz")));
    }

    #[test]
    fn rejects_missing_extension() {
        assert!(!has_supported_extension(Path::new("frame")));
        assert!(!has_supported_extension(Path::new(".hidden")));
    }

    #[test]
    fn derives_id_from_file_name() {
        assert_eq!(
            file_id(Path::new("/some/dir/frame_001.png")),
            "frame_001.png"
        );
        assert_eq!(file_id(Path::new("frame.jpg")), "frame.jpg");
    }
}
