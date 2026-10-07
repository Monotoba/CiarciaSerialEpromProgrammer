# Release checklist

## Before an experimental host-software prerelease

- [ ] Merge the reviewed PR after all latest-commit CI jobs pass.
- [ ] Select and synchronize an alpha version in `pyproject.toml` and package `__version__`.
- [ ] Build wheel and source distribution from the intended release commit.
- [ ] Install/check the wheel outside the checkout and verify license metadata.
- [ ] Confirm historical reference PDFs are excluded from release packages.
- [ ] Record checksums and validation results in release notes.
- [ ] State that physical hardware/firmware compatibility is unvalidated and
      matching Arduino firmware is not provided.
- [ ] Publish as a GitHub prerelease after approval; PyPI publication is separate.

## Before claiming hardware validation

- [ ] Identify exact schematic, firmware, chip variants, and electrical settings.
- [ ] Validate reads, blank-check, programming, and independent read-back verify.
- [ ] Validate full 64 KiB split transfers and address boundaries.
- [ ] Confirm program completion/error handling and pacing with firmware.
- [ ] Record tested devices and distinguish them from registry-only profiles.
