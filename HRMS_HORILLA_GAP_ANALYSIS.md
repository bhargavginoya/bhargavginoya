# HRMS Gap Analysis and Horilla Alignment

## Current state of this repository

This codebase already has a functional baseline for:
- Authentication and role-based access.
- Attendance with geofence validation.
- Leave workflows.
- Basic payroll generation.
- Multi-center mapping stubs.
- Expo frontend for web/mobile attendance and admin screens.

## Critical gaps identified (vs production-grade HRMS)

1. **Geofencing assignment depth**
   - Earlier implementation only supported a single geofence on check-in payload.
   - Employee-to-multiple-geofence mapping was incomplete.

2. **Face verification strength**
   - Earlier code only stored a selfie payload and did not verify identity during attendance punch.

3. **Center-aware attendance**
   - Employees could be assigned to centers, but attendance did not actually resolve center geofences at runtime.

4. **Mobile/web parity gaps**
   - Attendance UI consumed all geofences rather than only employee-eligible geofences.

## Horilla-aligned implementation direction

Horilla emphasizes modular HRMS domains (attendance, leave, payroll, employee lifecycle, organization structures). This repository now follows the same principle by tightening:

- Employee-specific attendance controls.
- Geo-aware punch logic with multiple allowed zones.
- Identity verification prior to check-in/check-out.

## Geo-fencing question: "If there's no geo-fencing functionality, why not?"

Geo-fencing exists in this codebase. The practical reason it may appear "non-functional" in production is usually one of:
- Employee geofence mappings not configured.
- Mobile location permission denied.
- Device coordinates outside configured radius.
- Missing center-to-geofence assignment data.

The backend changes in this branch specifically address these setup and logic gaps.

## What was implemented in this branch

- Multi-geofence eligibility resolver for each employee across assigned centers and global geofences.
- Attendance check-in now validates against:
  1) configured face enrollment,
  2) allowed geofence set,
  3) nearest in-bound geofence fallback.
- Added `GET /api/attendance/eligible-geofences` for app-side filtering.
- Added employee field persistence for `allowed_geofence_ids` in center assignment API.
- Frontend attendance now displays assigned geofences and submits selected geofence.

## Remaining work for a truly enterprise-complete HRMS

- Replace fallback face fingerprint matcher with ML face embeddings + liveness detection.
- Add geofence polygons (not only circles) and shift-based fences.
- Add audit logs, anti-spoofing controls, and device trust policy.
- Implement Horilla-equivalent modules end-to-end:
  - Recruitment / onboarding
  - Performance / appraisal
  - Asset management
  - Expense / claims
  - Advanced payroll rules engine
  - Compliance and statutory packs
