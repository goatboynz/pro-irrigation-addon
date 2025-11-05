# Requirements Document

## Introduction

The Pro-Irrigation Add-on is a Home Assistant integration that provides a centralized, GUI-based irrigation management system. It replaces a complex system of manual Node-RED flows and dozens of input helpers with a single, professional interface. The system is built around a "Pumps -> Zones" hierarchy that matches the physical layout of irrigation hardware, with intelligent scheduling capabilities and built-in safety mechanisms to prevent pump conflicts.

## Glossary

- **Pro-Irrigation Add-on**: The Home Assistant add-on system being specified
- **Irrigation Zone**: A physical area controlled by a single switch entity that receives water from a pump
- **Irrigation Pump**: A physical water pump that supplies water to one or more zones
- **Pump Lock**: A safety mechanism that prevents multiple zones on the same pump from running simultaneously
- **Auto Mode**: A scheduling mode that automatically calculates irrigation event times based on global light schedule settings
- **Manual Mode**: A scheduling mode where users specify exact irrigation event times
- **P1 Event**: The first irrigation event of the day, scheduled relative to lights-on time
- **P2 Event**: Subsequent irrigation events distributed throughout the day
- **Switch Entity**: A Home Assistant entity (switch.*) that controls physical irrigation hardware
- **Global Settings**: System-wide configuration values stored in Home Assistant helpers (light times, timing offsets)
- **Scheduler Engine**: The backend service that calculates when zones should run
- **Pump Queue**: A first-in-first-out queue that manages zone execution order for each pump
- **Home Assistant Ingress**: The mechanism that embeds the add-on's web interface into the Home Assistant sidebar

## Requirements

### Requirement 1

**User Story:** As an irrigation system operator, I want to access all irrigation management features through a single web interface embedded in Home Assistant, so that I don't need to manage multiple tools or external applications.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL provide a web-based graphical user interface accessible through Home Assistant Ingress
2. WHEN a user navigates to the add-on from the Home Assistant sidebar, THE Pro-Irrigation Add-on SHALL display the Pumps Dashboard as the home screen
3. THE Pro-Irrigation Add-on SHALL render the interface using modern web technologies that match Home Assistant's visual design language
4. THE Pro-Irrigation Add-on SHALL maintain user session state across page navigation within the interface

### Requirement 2

**User Story:** As an irrigation system operator, I want to add and manage pumps through a visual dashboard, so that I can organize my irrigation system according to my physical hardware layout.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL display a Pumps Dashboard showing all configured pumps in a grid layout
2. WHEN viewing the Pumps Dashboard, THE Pro-Irrigation Add-on SHALL display each pump's name, current status, and active zone information on individual pump cards
3. THE Pro-Irrigation Add-on SHALL provide an "Add New Pump" button on the Pumps Dashboard
4. WHEN a user clicks "Add New Pump", THE Pro-Irrigation Add-on SHALL prompt the user to enter a pump name and create a new pump configuration
5. THE Pro-Irrigation Add-on SHALL provide a "Manage" button on each pump card that navigates to the Zone Manager for that pump

### Requirement 3

**User Story:** As an irrigation system operator, I want to add zones to specific pumps and select Home Assistant switch entities for each zone, so that I can configure which physical hardware each zone controls.

#### Acceptance Criteria

1. WHEN a user clicks "Manage" on a pump card, THE Pro-Irrigation Add-on SHALL display the Zone Manager screen showing all zones assigned to that pump
2. THE Pro-Irrigation Add-on SHALL provide an "Add New Zone to this Pump" button on the Zone Manager screen
3. WHEN a user adds or edits a zone, THE Pro-Irrigation Add-on SHALL display a Zone Editor form
4. THE Pro-Irrigation Add-on SHALL populate a searchable dropdown list in the Zone Editor with all switch entities discovered from Home Assistant
5. WHEN a user selects a switch entity, THE Pro-Irrigation Add-on SHALL associate that entity with the zone configuration and store it in the database

### Requirement 4

**User Story:** As an irrigation system operator, I want zones on the same pump to never run simultaneously, so that I prevent pump overload and ensure system safety.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL maintain a separate queue for each configured pump
2. WHEN a zone is scheduled to run, THE Pro-Irrigation Add-on SHALL add the zone's execution job to its associated pump's queue
3. WHILE a pump's lock entity indicates the pump is in use, THE Pro-Irrigation Add-on SHALL NOT start any additional zones on that pump
4. WHEN a pump's lock entity indicates the pump is idle AND the pump's queue contains jobs, THE Pro-Irrigation Add-on SHALL execute the first job in the queue
5. THE Pro-Irrigation Add-on SHALL activate the pump lock entity before starting a zone and deactivate it after the zone completes

### Requirement 5

**User Story:** As an irrigation system operator, I want to configure zones with Auto Mode scheduling, so that irrigation events are automatically calculated based on my lighting schedule without manual time entry.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL provide an Auto Mode option in the Zone Editor
2. WHEN Auto Mode is selected, THE Pro-Irrigation Add-on SHALL display configuration fields for P1 duration, P2 event count, and P2 duration
3. THE Pro-Irrigation Add-on SHALL calculate P1 event start time by adding the global P1 start delay to the global lights-on time
4. THE Pro-Irrigation Add-on SHALL calculate P2 event times by distributing events evenly between the P2 start time and the P2 end time
5. THE Pro-Irrigation Add-on SHALL calculate P2 start time by adding the global P2 start delay to the global lights-on time
6. THE Pro-Irrigation Add-on SHALL calculate P2 end time by subtracting the global P2 end buffer from the global lights-off time

### Requirement 6

**User Story:** As an irrigation system operator, I want to configure zones with Manual Mode scheduling, so that I can specify exact irrigation times for zones that need precise control.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL provide a Manual Mode option in the Zone Editor
2. WHEN Manual Mode is selected, THE Pro-Irrigation Add-on SHALL display text input fields for P1 event list and P2 event list
3. THE Pro-Irrigation Add-on SHALL accept event times in HH:MM.SS format where SS represents duration in seconds
4. WHEN a user enters a manual event list, THE Pro-Irrigation Add-on SHALL parse each entry to extract the scheduled time and duration
5. THE Pro-Irrigation Add-on SHALL validate that manual event times are in correct format before saving the zone configuration

### Requirement 7

**User Story:** As an irrigation system operator, I want to configure global settings that apply to all Auto Mode zones, so that I can adjust system-wide timing parameters from a central location.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL provide a Global Settings page accessible from the main navigation
2. THE Pro-Irrigation Add-on SHALL display dropdown selectors for linking to Home Assistant entities: lights-on time, lights-off time, P1 start delay, P2 start delay, and P2 end buffer
3. WHEN the Global Settings page loads, THE Pro-Irrigation Add-on SHALL query Home Assistant to populate dropdowns with available input_datetime and input_number entities
4. THE Pro-Irrigation Add-on SHALL store the selected global entity references in the database
5. THE Pro-Irrigation Add-on SHALL provide a text area for feed schedule notes

### Requirement 8

**User Story:** As an irrigation system operator, I want the system to automatically discover and execute scheduled irrigation events, so that zones run at the correct times without manual intervention.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL run a Scheduler Engine process that evaluates all zone schedules every 60 seconds
2. WHEN the Scheduler Engine runs, THE Pro-Irrigation Add-on SHALL retrieve current global settings from Home Assistant
3. WHEN the Scheduler Engine runs, THE Pro-Irrigation Add-on SHALL calculate all scheduled event times for each enabled zone
4. WHEN the current time matches a zone's scheduled event time, THE Pro-Irrigation Add-on SHALL create an execution job containing the zone name, switch entity, and duration
5. WHEN an execution job is created, THE Pro-Irrigation Add-on SHALL add the job to the appropriate pump's queue

### Requirement 9

**User Story:** As an irrigation system operator, I want zones to execute in the order they were scheduled, so that the system behaves predictably when multiple zones are queued.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL run a Pump Queue Processor that checks all pump queues every 1 second
2. WHEN the Pump Queue Processor finds a pump with an idle lock AND a non-empty queue, THE Pro-Irrigation Add-on SHALL execute the first job in that pump's queue
3. WHEN executing a job, THE Pro-Irrigation Add-on SHALL call Home Assistant's turn_on service for the pump lock entity
4. WHEN executing a job, THE Pro-Irrigation Add-on SHALL call Home Assistant's turn_on service for the zone's switch entity
5. WHEN a job's duration expires, THE Pro-Irrigation Add-on SHALL call Home Assistant's turn_off service for the zone's switch entity
6. WHEN a job completes, THE Pro-Irrigation Add-on SHALL call Home Assistant's turn_off service for the pump lock entity

### Requirement 10

**User Story:** As an irrigation system operator, I want all pump and zone configurations stored persistently, so that my settings are preserved across add-on restarts and Home Assistant reboots.

#### Acceptance Criteria

1. THE Pro-Irrigation Add-on SHALL use a SQLite database stored in the /data directory for all configuration persistence
2. THE Pro-Irrigation Add-on SHALL store pump configurations including pump name and associated lock entity
3. THE Pro-Irrigation Add-on SHALL store zone configurations including zone name, associated pump, switch entity, schedule mode, and mode-specific parameters
4. THE Pro-Irrigation Add-on SHALL store global settings including entity references and feed schedule notes
5. WHEN the add-on starts, THE Pro-Irrigation Add-on SHALL load all configurations from the database before beginning scheduler operations

### Requirement 11

**User Story:** As an irrigation system operator, I want to view each zone's current mode and next scheduled run time, so that I can verify the system is configured correctly.

#### Acceptance Criteria

1. WHEN viewing the Zone Manager for a pump, THE Pro-Irrigation Add-on SHALL display each zone's name, schedule mode, and next scheduled event time
2. THE Pro-Irrigation Add-on SHALL calculate the next scheduled event time based on the zone's current configuration and global settings
3. WHEN a zone is in Auto Mode, THE Pro-Irrigation Add-on SHALL display "Auto" as the mode indicator
4. WHEN a zone is in Manual Mode, THE Pro-Irrigation Add-on SHALL display "Manual" as the mode indicator
5. THE Pro-Irrigation Add-on SHALL update displayed next run times when zone configurations or global settings change

### Requirement 12

**User Story:** As an irrigation system operator, I want to see real-time pump status information, so that I know which zones are currently running or queued.

#### Acceptance Criteria

1. WHEN viewing the Pumps Dashboard, THE Pro-Irrigation Add-on SHALL display each pump's current status as "Idle", "Running", or "Queued"
2. WHEN a pump is running a zone, THE Pro-Irrigation Add-on SHALL display the active zone's name on the pump card
3. WHEN a pump has jobs in its queue, THE Pro-Irrigation Add-on SHALL indicate the queued status on the pump card
4. THE Pro-Irrigation Add-on SHALL update pump status displays within 5 seconds of status changes
