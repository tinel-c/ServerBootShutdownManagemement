# Health Dashboard Visual Guide

This document describes the comprehensive health monitoring dashboard layout and features.

## Dashboard Overview

The health monitoring dashboard displays detailed information from your health check service (e.g., Healthchecks.io) via MQTT. Each server (Dell T310 and HP DL360p) has its own health monitoring panel.

## Header Section

```
┌─────────────────────────────────────────────────────────────┐
│  Dell T310                    Dec 29, 2025 10:51 AM  [ALL HEALTHY]  │
│  Last sync: 2s ago             Checks: 1                    │
└─────────────────────────────────────────────────────────────┘
```

**Displays**:
- Server name from MQTT payload
- Current timestamp (formatted)
- Overall status badge (green=all healthy, red=issues detected, orange=warning)
- Last sync time (auto-updating, human-readable)
- Total number of health checks

## Individual Check Cards

Each health check is displayed in its own card with comprehensive information:

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ nextcloud  [nextcloud]                          [UP]     │
│                                                              │
│ ┌──────────────┬──────────────┐  ┌──────────────┬─────────┐│
│ │ Total Pings  │ Grace Period │  │ Timeout      │ Manual  ││
│ │ 255,949      │ 300s         │  │ 120s         │ AUTO    ││
│ └──────────────┴──────────────┘  └──────────────┴─────────┘│
│                                                              │
│ ⏱️ Last Ping:   Dec 29, 10:50:01                           │
│ ⏭️ Next Ping:   Dec 29, 10:52:01                           │
│ ⏳ Time Until:  1m 23s                                      │
│                                                              │
│                    🔗 View Badge                            │
└─────────────────────────────────────────────────────────────┘
```

### Check Card Components

#### 1. **Header Line**
- **Status Icon**: ✅ (up), ❌ (down), ⚠️ (warning)
- **Check Name**: Display name (e.g., "nextcloud")
- **Slug**: Technical identifier in brackets
- **Status Pill**: Color-coded status badge (UP/DOWN/WARNING)

#### 2. **Description** (if available)
- Optional text description of the check
- Displayed below the header

#### 3. **Tags** (if available)
- Colored pill badges for each tag
- Format: #tag1 #tag2
- Green background with rounded corners

#### 4. **Statistics Grid** (2x2)
- **Total Pings**: Formatted number with thousands separators (e.g., 255,949)
- **Grace Period**: Time in seconds before check is considered late
- **Timeout**: Maximum time allowed for check completion
- **Manual Resume**: Shows "REQUIRED" (orange) or "AUTO" (green)

#### 5. **Timing Information**
- **Last Ping**: When the last successful ping was received (formatted timestamp)
- **Next Ping**: When the next ping is expected (formatted timestamp)
- **Time Until**: Live countdown to next ping (updates every second)
  - Shows "Overdue!" if next ping time has passed
  - Format: hours, minutes, seconds (e.g., "2h 15m" or "45s")

#### 6. **Optional Fields** (if present)
- **Methods**: Communication methods (📡 http, email, etc.)
- **Subject**: Email subject for alerts (📧)
- **Started**: Flag showing if check has been started (▶️)

#### 7. **Badge URL** (if available)
- Clickable link to external status badge
- Opens in new tab
- Format: 🔗 View Badge

## Color Coding

### Status Colors
- **Green (#4caf50)**: Healthy/Up
- **Red (#f44336)**: Down/Error
- **Orange (#ff9800)**: Warning/Unknown

### Card Styling
- **Green Left Border**: Check is UP
- **Red Left Border**: Check is DOWN
- **Orange Left Border**: Check is WARNING/UNKNOWN
- **Glowing Effect**: Status pill has matching glow shadow

### Visual Effects
- **Gradient Backgrounds**: Modern gradient overlays
- **Glass-morphism**: Semi-transparent backgrounds with blur
- **Shadow Effects**: Elevated card appearance
- **Smooth Transitions**: Animations on state changes
- **Icon Glows**: Status icons have drop-shadow effects

## Live Updates

The dashboard updates automatically:
- **Every 1 second**: Countdown timers, time deltas refresh
- **On MQTT message**: All data updates when new health report arrives

## Empty State

When no health checks are available:

```
┌─────────────────────────────────────────────────────────────┐
│                           ⚠️                                 │
│              No Health Checks Available                     │
│         Waiting for health data from server...              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Healthchecks.io → Python Backend → MQTT Broker → Node-RED → Dashboard
                                    (dell/t310/health)
```

1. Python script polls Healthchecks.io API
2. Formats data and publishes to MQTT topic
3. Node-RED subscribes and receives health data
4. Vue.js template renders beautiful dashboard
5. Auto-refresh keeps countdown timers live

## MQTT Payload Example

```json
{
  "timestamp": "2025-12-29T10:51:43.189705",
  "server": "Dell T310",
  "checks": [
    {
      "name": "nextcloud",
      "slug": "nextcloud",
      "tags": "",
      "desc": "",
      "status": "up",
      "n_pings": 255949,
      "grace": 300,
      "timeout": 120,
      "last_ping": "2025-12-29T10:50:01+00:00",
      "next_ping": "2025-12-29T10:52:01+00:00",
      "manual_resume": false,
      "started": false,
      "methods": "",
      "subject": "",
      "badge_url": "https://healthchecks.io/b/2/...",
      "unique_key": "8a4c520e..."
    }
  ]
}
```

## Customization Options

### Adjusting Card Height
In the flow JSON, modify the `height` property:
```json
"height": "8"  // Increase for more vertical space
```

### Changing Colors
Edit the color values in the template methods:
```javascript
// In getStatusPillStyle()
if (status === 'up') {
    return { background: '#4caf50' }  // Change to your color
}
```

### Modifying Statistics
Add/remove items from the statistics grid in the template HTML:
```html
<div style="display: grid; grid-template-columns: repeat(2, 1fr);">
    <!-- Add your custom metric here -->
</div>
```

### Time Format
Change date formatting in the `formatDateTime()` method:
```javascript
return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
    // Add: year: 'numeric', weekday: 'short', etc.
})
```

## Performance Notes

- **Efficient Updates**: Only Vue.js data changes trigger re-renders
- **1-second Interval**: Balance between responsiveness and CPU usage
- **Flow Context**: No persistent storage, data resets on Node-RED restart
- **Lightweight**: Pure CSS styling, no external dependencies

## Browser Compatibility

- **Modern Browsers**: Chrome, Firefox, Edge, Safari (latest versions)
- **Vue.js 3**: Included with Dashboard 2.0
- **ES6+ JavaScript**: Required for template scripts
- **CSS Grid/Flexbox**: Required for layout

## Troubleshooting

### Cards Not Displaying
- Check MQTT messages are arriving: Add debug node
- Verify payload structure matches expected format
- Check browser console for JavaScript errors

### Countdown Not Updating
- Verify `mounted()` and `unmounted()` lifecycle hooks
- Check setInterval is running (use console.log)
- Ensure timestamps are valid ISO-8601 format

### Styling Issues
- Clear browser cache
- Check Dashboard 2.0 is properly installed
- Verify no CSS conflicts with custom themes

### Performance Issues
- Reduce update interval from 1s to 2s or 5s
- Limit number of checks displayed
- Check browser developer tools performance tab

## Advanced Features

### Multiple Checks per Server
The dashboard automatically handles multiple checks:
- Each check gets its own card
- Overall status badge reflects all checks
- Cards are sorted by unique_key

### Responsive Design
- Cards adapt to container width
- Grid layout adjusts for mobile/tablet
- Font sizes scale appropriately

### Accessibility
- High contrast color choices
- Semantic HTML structure
- Icon + text labels for clarity
- Keyboard navigation supported

## Integration with Healthchecks.io

This dashboard is optimized for Healthchecks.io API response format but can work with any health check service that provides:
- Check name and status
- Ping timestamps
- Grace period and timeout values
- Unique identifier for each check

Adapt the Python backend to format your health check service data to match the expected MQTT payload structure.

---

**Created**: December 29, 2025  
**Node-RED Dashboard**: 2.0 (@flowfuse/node-red-dashboard)  
**Vue.js Version**: 3.x

