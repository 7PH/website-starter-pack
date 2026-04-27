# Changelog

All notable changes to the Website Starter Pack will be documented in this file.

This changelog helps track breaking changes and new features for easier migration of projects using this starter pack.

## [Unreleased]

### Added

- Override hooks for `PageHeader` and `PageFooter` in `layouts/default.vue` and
  `layouts/fullheight.vue`. Sub-apps register replacements via the existing
  `componentOverrides` map in `config/component-overrides.ts`. Same pattern as
  existing `Breadcrumb` / `OrganizationsCreateModal` overrides.
- Starter Pack initial release
