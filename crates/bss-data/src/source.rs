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
    /// Load all supported samples from the source.
    ///
    /// Samples are returned sorted by [`Sample::id`] for deterministic ordering.
    /// An empty source yields an empty vector rather than an error.
    ///
    /// # Errors
    ///
    /// - [`DataError::SourceNotFound`] if the source location does not exist or
    ///   is not a valid source.
    /// - [`DataError::ReadError`] if an individual item cannot be read.
    fn load_data(&self) -> Result<Vec<Sample>, DataError>;
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
    fn load_data(&self) -> Result<Vec<Sample>, DataError> {
        if !self.root.is_dir() {
            return Err(DataError::SourceNotFound {
                location: self.root.display().to_string(),
            });
        }

        let entries = fs::read_dir(&self.root).map_err(|error| DataError::SourceNotFound {
            location: format!("{}: {error}", self.root.display()),
        })?;

        let mut samples = Vec::new();

        for entry in entries {
            let path = entry
                .map_err(|error| DataError::ReadError {
                    id: self.root.display().to_string(),
                    reason: error.to_string(),
                })?
                .path();

            if !is_supported_file(&path) {
                warn!(path = %path.display(), "skipping unsupported file");
                continue;
            }

            let id = file_id(&path);
            let bytes = fs::read(&path).map_err(|error| DataError::ReadError {
                id: id.clone(),
                reason: error.to_string(),
            })?;

            samples.push(Sample {
                id,
                data: Bytes::from(bytes),
            });
        }

        samples.sort_by(|a, b| a.id.cmp(&b.id));
        Ok(samples)
    }
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
