# Telegram Help Command - Sectioned Layout Update

## Overview

This document provides instructions for updating the `/help` command to use a sectioned layout that scales better as more automation domains are added.

## Problem

The original `/help` command listed all commands and buttons in a flat structure, which becomes cluttered and hard to navigate as more automation domains (gates, lights, irrigation, etc.) are added.

## Solution

Implement a **sectioned layout** with:
1. **Visual separators** in the text message using `━━━━━` characters
2. **Section headers** in the inline keyboard as non-clickable buttons
3. **Grouped buttons** under each section for better organization

## Updated Help Message Format

### Text Message Structure

```
🤖 Automation Control Bot

━━━━━━━━━━━━━━━━━━━━━━━━━━

🖥️ SERVER MANAGEMENT
🟢 `/boot [dell|hp]` - Boot server
🟠 `/shutdown [dell|hp]` - Graceful shutdown
🔴 `/force [dell|hp]` - Force shutdown
📊 `/status` - Get server status

━━━━━━━━━━━━━━━━━━━━━━━━━━

🚪 GATE AUTOMATION
🚪 `/gate_open` or `/gate` - Open main gate
📊 `/gate_status` - Get gate status
❓ `/gate_help` - Gate-specific help

━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ HELP & REFERENCE
❓ `/help` - This quick help
📋 `/commands` - Complete reference
🚀 `/start` - Start bot

━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 QUICK TIPS
• Use buttons below for quick access
• Type `/commands` for detailed info
• Default server is `dell` if not specified

Quick Actions ⬇️
```

### Inline Keyboard Structure

```
┌─────────────────────────────────┐
│  ━━━━━ 🖥️ SERVERS ━━━━━        │  ← Section Header (non-clickable)
├─────────────────────────────────┤
│  🟢 Boot Dell  │  🟢 Boot HP    │
├─────────────────────────────────┤
│  🟠 Shutdown Dell │ 🟠 Shutdown HP │
├─────────────────────────────────┤
│      📊 Server Status            │
├─────────────────────────────────┤
│  ━━━━━ 🚪 GATES ━━━━━           │  ← Section Header (non-clickable)
├─────────────────────────────────┤
│      🚪 Open Main Gate           │
├─────────────────────────────────┤
│      📊 Gate Status              │
├─────────────────────────────────┤
│  ━━━━━ ℹ️ INFO ━━━━━            │  ← Section Header (non-clickable)
├─────────────────────────────────┤
│  📋 All Commands │ ❓ Help       │
└─────────────────────────────────┘
```

## Implementation

### Step 1: Update the Help Function

Replace the `func_handle_help` function node in `nodered/flows/50-telegram-interface.json`:

**File**: `nodered/flows/50-telegram-interface-updated.json` (reference implementation)

**Key Changes**:

1. **Text Message** - Use section separators:
```javascript
const helpText = `🤖 *Automation Control Bot*\\n\\n` +
    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +
    `🖥️ *SERVER MANAGEMENT*\\n` +
    // ... commands ...
    `━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +
    `🚪 *GATE AUTOMATION*\\n` +
    // ... commands ...
```

2. **Inline Keyboard** - Add section headers:
```javascript
const inlineKeyboard = {
    inline_keyboard: [
        // Section header (non-clickable)
        [
            { text: '━━━━━ 🖥️ SERVERS ━━━━━', callback_data: 'noop' }
        ],
        // Buttons for this section
        [
            { text: '🟢 Boot Dell', callback_data: '/boot dell' },
            { text: '🟢 Boot HP', callback_data: '/boot hp' }
        ],
        // ... more buttons ...
        
        // Next section header
        [
            { text: '━━━━━ 🚪 GATES ━━━━━', callback_data: 'noop' }
        ],
        // ... buttons ...
    ]
};
```

### Step 2: Handle "noop" Callback

The section headers use `callback_data: 'noop'` to prevent errors when clicked. You need to handle this in the parse function:

**Option 1**: Ignore in parser (recommended):
```javascript
// In func_parse_telegram, after parsing command:
if (command === 'noop') {
    // Just answer the callback, don't route
    return [null, answerCallback].filter(m => m !== null);
}
```

**Option 2**: Add to switch node:
Add a new output to `switch_telegram_commands` for `noop` that goes directly to `func_answer_callback`.

### Step 3: Deploy and Test

1. Open Node-RED: http://localhost:1880
2. Import the updated function from `50-telegram-interface-updated.json`
3. Replace the existing `func_handle_help` node
4. Deploy
5. Test in Telegram: `/help`

## Benefits

### Scalability
- ✅ Easy to add new automation domains
- ✅ Each domain has its own section
- ✅ Clear visual separation

### User Experience
- ✅ Easier to scan and find commands
- ✅ Grouped related actions together
- ✅ Professional appearance

### Maintainability
- ✅ Simple to add/remove sections
- ✅ Consistent structure across domains
- ✅ Self-documenting layout

## Adding New Automation Domains

When adding a new domain (e.g., lights, irrigation), follow this pattern:

### 1. Add to Text Message

```javascript
`━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n` +
`💡 *LIGHTS AUTOMATION*\\n` +
`💡 \\`/lights_on\\` - Turn on all lights\\n` +
`🌙 \\`/lights_off\\` - Turn off all lights\\n` +
`📊 \\`/lights_status\\` - Get lights status\\n\\n` +
```

### 2. Add to Inline Keyboard

```javascript
// Section header
[
    { text: '━━━━━ 💡 LIGHTS ━━━━━', callback_data: 'noop' }
],
// Buttons
[
    { text: '💡 All On', callback_data: '/lights_on' },
    { text: '🌙 All Off', callback_data: '/lights_off' }
],
[
    { text: '📊 Lights Status', callback_data: '/lights_status' }
],
```

### 3. Keep It Organized

**Best Practices**:
- Use consistent emoji for each domain
- Limit to 2-3 most common actions per section
- Keep section headers short (max 20 chars)
- Use `callback_data: 'noop'` for all headers

## Example: Full Updated Help Function

See `nodered/flows/50-telegram-interface-updated.json` for the complete implementation.

## Testing Checklist

- [ ] `/help` command shows sectioned layout
- [ ] Section headers are visible but don't respond to clicks
- [ ] All buttons work correctly
- [ ] Text message has proper formatting
- [ ] Emoji display correctly
- [ ] Layout looks good on mobile
- [ ] Layout looks good on desktop Telegram

## Troubleshooting

### Section Headers Are Clickable

**Problem**: Users can click section headers and get errors.

**Solution**: Ensure `callback_data: 'noop'` is set and handled in parser.

### Layout Looks Cluttered

**Problem**: Too many buttons in one section.

**Solution**: 
- Limit to 2-3 key actions per section
- Move detailed commands to `/commands`
- Use domain-specific help (e.g., `/gate_help`)

### Buttons Don't Align

**Problem**: Buttons appear misaligned or stacked oddly.

**Solution**:
- Each row in `inline_keyboard` is an array
- Keep 1-2 buttons per row for best appearance
- Test on both mobile and desktop

## Migration Notes

### From Old Format

**Before** (flat list):
```
[Boot Dell] [Boot HP]
[Shutdown Dell] [Shutdown HP]
[Force Dell] [Force HP]
[Open Gate] [Gate Status]
[Server Status] [Help]
```

**After** (sectioned):
```
━━━━━ 🖥️ SERVERS ━━━━━
[Boot Dell] [Boot HP]
[Shutdown Dell] [Shutdown HP]
[Server Status]

━━━━━ 🚪 GATES ━━━━━
[Open Main Gate]
[Gate Status]

━━━━━ ℹ️ INFO ━━━━━
[All Commands] [Help]
```

### Backwards Compatibility

- All existing commands still work
- Callback data unchanged
- Only presentation is different
- No breaking changes to functionality

## Future Enhancements

### Dynamic Sections

Create sections dynamically based on available domains:

```javascript
const domains = [
    { name: 'SERVERS', emoji: '🖥️', commands: [...] },
    { name: 'GATES', emoji: '🚪', commands: [...] },
    { name: 'LIGHTS', emoji: '💡', commands: [...] }
];

// Build keyboard dynamically
domains.forEach(domain => {
    keyboard.push([{ text: `━━━━━ ${domain.emoji} ${domain.name} ━━━━━`, callback_data: 'noop' }]);
    domain.commands.forEach(cmd => {
        keyboard.push([{ text: cmd.label, callback_data: cmd.callback }]);
    });
});
```

### Collapsible Sections

Use Telegram's inline query feature to create expandable sections (advanced).

### Per-Domain Help

Each domain can have its own detailed help:
- `/help` - Quick overview (current)
- `/server_help` - Detailed server commands
- `/gate_help` - Detailed gate commands
- `/commands` - Complete reference (all domains)

## Related Documentation

- **Complete Command Reference**: `docs/TELEGRAM_COMMANDS_REFERENCE.md`
- **Telegram Setup**: `nodered/TELEGRAM_SETUP.md`
- **Gate Integration**: `docs/GATE_TELEGRAM_INTEGRATION.md`

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Ready for Implementation
