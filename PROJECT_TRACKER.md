# CoMIT Project Tracker & Roadmap

This file tracks all requested features, current progress, and architectural decisions to ensure no hallucinations and strict adherence to the project vision.

## Phase 1: Core Intersection Management (Completed & Refined)
- [x] Basic RL integration with SUMO.
- [x] V2X messaging via MQTT.
- [x] Emergency Green Corridor logic.
- [x] Fix Safety Checker conflict matrix (Critical bug resolved: N/S now conflicts with E/W).
- [x] Dashboard: Base implementation with React/Vite.
- [x] Dashboard: Update KPI Metrics (Wait Reduction, CO2 Saved, Density, RL Confidence).
- [x] Dashboard: Multi-language (i18n) localization toggle (EN, FR, TA).
- [x] Dashboard: Highlight active Green Corridor on the map.

## Phase 1.5: UI/UX Overhaul (In Progress)
- [ ] Overhaul the React Dashboard UI to strictly match the generated glassmorphism design image (deep blue/cyan hues, premium glowing elements, high-tech map aesthetic).

## Phase 2: Centralized City-Wide Ecosystem (To Do)
- [x] **Admin Enforcement & Violation Dashboard**: New UI tab to track speed limit violations and red-light runners with cropped images and timestamps.
- [x] **Infrastructure Monitoring (Potholes)**: Update vision nodes to simulate pothole detection and send warnings via V2X.
- [x] **Synchronized Navigation**: Update the voice module logic to combine turn-by-turn navigation with GLOSA speed advisory (e.g., "Turn right, maintain 40km/h").
- [x] **Centralized Predictive Routing**: V2V/V2I simulation where civilian cars are rerouted *before* the ambulance reaches the intersection.

---
*Last updated: Session 1*
