---
name: frontend-ui-quality
description: >-
  Guide for React/Next.js UI architecture, responsive design, accessibility (WCAG 2.1 AA),
  dashboard states, component patterns, onboarding flows, and visual consistency.
---

# Frontend UI Quality Skill

## Tech Stack

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui (Radix primitives)
- **Charts:** Recharts
- **State:** React Query (TanStack Query) for server state, React context for UI state
- **Forms:** React Hook Form + Zod validation

## Design System

### Color Palette
- **AQI Good (0-50):** Emerald/Green
- **AQI Moderate (51-100):** Yellow/Amber
- **AQI Unhealthy Sensitive (101-150):** Orange
- **AQI Unhealthy (151-200):** Red
- **AQI Very Unhealthy (201-300):** Purple
- **AQI Hazardous (301+):** Maroon
- **Simulated data:** Dashed borders + "SIMULATED" badge
- **Sensor offline:** Gray with pulsing dot

### Component States (ALL required)
Every interactive component must handle:
1. **Loading:** Skeleton or spinner
2. **Empty:** Helpful message + action prompt
3. **Error:** User-friendly message + retry
4. **Success:** Data display
5. **Stale:** Warning indicator
6. **Offline:** Degraded view with last-known data

## Required Pages

| Page | Route | Key Components |
|------|-------|---------------|
| Overview | `/` | StatusBanner, RoomCards, TrendCharts, DeviceList, AlertsFeed |
| Rooms | `/rooms/[id]` | RoomHeader, SensorGrid, TimeSeriesChart, EventTimeline |
| Devices | `/devices` | DeviceCards, StatusBadge, CapabilityList |
| Add Device | `/devices/add` | ProviderSelector, ConnectionWizard, CapabilityPreview |
| Events | `/events` | EventTimeline, SeverityFilter, EventDetail |
| Automations | `/automations` | RuleBuilder, ExecutionHistory, EnableToggle |
| AI Model Lab | `/models` | DatasetExplorer, TrainingDashboard, ModelRegistry |
| Analytics | `/analytics` | TimeRangeSelector, ComparisonCharts, ExportButton |
| Settings | `/settings` | ProfileForm, HomeManager, IntegrationCredentials |

## Accessibility Requirements (WCAG 2.1 AA)

- All interactive elements keyboard-navigable
- Color is never the sole indicator (use icons + labels)
- Minimum contrast ratio 4.5:1 for text
- All images and charts have alt text / aria-labels
- Focus indicators visible
- Screen reader announcements for live updates (aria-live)
- Skip navigation link

## Responsive Breakpoints

- Mobile: < 640px (single column, bottom nav)
- Tablet: 640-1024px (two column)
- Desktop: > 1024px (full sidebar nav + content)

## Validation Checklist

- [ ] Every page handles loading, empty, error, success states
- [ ] No decorative buttons without real functionality
- [ ] Dark mode fully supported
- [ ] Simulated data visually distinct from real data
- [ ] Charts are responsive and accessible
- [ ] Forms validate client-side with Zod
- [ ] Navigation is consistent across all pages
- [ ] Mobile layout tested

