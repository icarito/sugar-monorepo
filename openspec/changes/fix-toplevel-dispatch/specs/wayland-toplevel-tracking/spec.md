## ADDED Requirements

### Requirement: Toplevel events are delivered, not merely available
The tracker SHALL deliver toplevel open, close, and focus events to its
callbacks on a compositor advertising
`zwlr_foreign_toplevel_manager_v1`. Reporting the protocol as available
without delivering any event is a failure of this requirement.

#### Scenario: A window opens on a wlroots compositor
- **WHEN** the tracker is running on a compositor that offers the
  protocol and an application maps a toplevel window
- **THEN** the tracker invokes its open callback with that window's
  app id

#### Scenario: Focus changes are reported
- **WHEN** an application's toplevel becomes activated (focused)
- **THEN** the tracker invokes its focus callback with that window's
  app id

#### Scenario: A window closes
- **WHEN** an application's tracked toplevel is closed
- **THEN** the tracker invokes its close callback for that window

### Requirement: Event loop flushes outgoing requests
The tracker's Wayland event loop SHALL use a mechanism that flushes the
client's outgoing request buffer each iteration, so the compositor
begins and continues streaming toplevel events. A non-flushing dispatch
loop (which leaves the manager bind unflushed and delivers no events)
SHALL NOT be used.

#### Scenario: Loop uses a flushing mechanism
- **WHEN** the tracker's event loop runs
- **THEN** it flushes pending requests to the compositor on each
  iteration rather than only reading incoming events

### Requirement: Loop does not busy-spin
The tracker's event loop SHALL NOT consume a CPU core while idle waiting
for window events.

#### Scenario: Idle between events
- **WHEN** no toplevel events are occurring
- **THEN** the tracker thread yields between iterations rather than
  spinning continuously

### Requirement: Stop remains responsive
Stopping the tracker SHALL cause its event loop to exit promptly and tear
down the Wayland connection cleanly.

#### Scenario: Stopping the tracker
- **WHEN** `stop()` is called
- **THEN** the event loop exits within a short bounded interval and the
  display is disconnected without raising to the caller
