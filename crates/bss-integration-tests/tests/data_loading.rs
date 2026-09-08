//! Workspace-level integration tests for loading sample data.

use std::fs;
use std::path::PathBuf;

use bss_data::{DataSource, LocalDirectory};

const CAT_SAMPLE_FILENAME: &str = "my_cat_in_a_bucket.jpeg";

/// JPEG files begin with the Start Of Image marker `FF D8 FF`.
const JPEG_MARKER: [u8; 3] = [0xFF, 0xD8, 0xFF];

fn sample_data_dir() -> PathBuf {
    // The workspace root is two levels above this crate's manifest.
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("data")
        .join("sample")
}

#[test]
fn loads_cat_in_a_bucket_sample() {
    let sample_dir = sample_data_dir();

    let samples = LocalDirectory::new(&sample_dir)
        .load_data()
        .expect("sample directory should load");

    let cat = samples
        .iter()
        .find(|sample| sample.id == CAT_SAMPLE_FILENAME)
        .expect("cat-in-a-bucket sample should be present");

    assert!(
        cat.data.starts_with(&JPEG_MARKER),
        "sample should contain valid JPEG bytes"
    );

    // The loaded bytes must match the file on disk exactly.
    let expected = fs::read(sample_dir.join(CAT_SAMPLE_FILENAME))
        .expect("sample file should be readable directly");
    assert_eq!(
        cat.data, expected,
        "loaded sample bytes should match the file on disk exactly"
    );
}
