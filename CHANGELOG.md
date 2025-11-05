# Changelog

## [2.0.2] - 2025-11-05

### Fixed
- Frontend: Set base path to './' for proper asset loading in Home Assistant Ingress
- Backend: Add missing /api/ha/entities endpoint for entity discovery
- Frontend now loads correctly in Home Assistant sidebar

## [2.0.1] - 2025-11-05

### Fixed
- Docker build: Install all npm dependencies including dev dependencies for build process
- Docker build: Explicitly copy package-lock.json for reproducible builds

## [2.0.0] - 2025-11-05

### Complete Redesign - Room-Based System

This is a complete rewrite of the irrigation system with a new room-based architecture.

#### Added
- **Room-Based Organization**: Organize everything by grow rooms
- **Simplified Water Events**: P1 and P2 events at room level
- **Manual Controls**: Easy manual pump/zone operation with proper timing
- **Environmental Monitoring**: Track sensors with historical graphs (1h to 7d)
- **Dashboard**: Overview of all rooms with status
- **Settings Page**: Configure delays and reset system
- **Pump Timing**: 5-second pump startup delay before zone opens
- **Zone Timing**: 2-second delay when switching between zones
- **Run Time Precision**: Specify run times in total seconds

#### Changed
- Complete database schema redesign
- New API structure focused on rooms
- Simplified UI with room-centric navigation
- Better entity discovery and selection

#### Removed
- Old pump-first hierarchy
- Global settings for auto mode
- Complex zone-level scheduling

### Breaking Changes
- This version is NOT compatible with v1.x
- All data must be reconfigured
- New database schema (irrigation_v2.db)

---

## [1.0.0] - 2025-11-05 (Deprecated)

Initial release with pump-based organization. See v1 branch for details.
