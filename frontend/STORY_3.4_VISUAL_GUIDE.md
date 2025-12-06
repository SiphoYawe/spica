# Story 3.4: React Flow Graph Display - Visual Guide

## Node Component Designs

### 1. TriggerNode (Cyber Blue Theme)

```
┌─────────────────────────────────┐
│ ═══════════════════════════════ │ ← Gradient top border (blue/purple/green)
│                                 │
│  [💲] TRIGGER                   │ ← Icon badge + Type label
│                                 │
│  GAS below $5.00                │ ← Main display text (bold)
│                                 │
│  [price]                        │ ← Type badge
│                                 │
└────────────────┬────────────────┘
                 ● ← Source handle (output)
```

**Features:**
- Icons: Clock (time triggers) or DollarSign (price triggers)
- Color: Cyan blue (#00D9FF)
- Displays: Condition text, trigger type
- Handles: Source only (bottom)

---

### 2. SwapNode (Cyber Green Theme)

```
                 ● ← Target handle (input)
┌────────────────┴────────────────┐
│ ═══════════════════════════════ │ ← Gradient top border (green)
│                                 │
│  [⇄] SWAP                       │ ← Arrow icon + Type label
│                                 │
│  10 GAS → NEO                   │ ← Amount and tokens
│                                 │
│  [GAS] ⇄ [NEO]                  │ ← Token badges
│                                 │
└────────────────┬────────────────┘
                 ● ← Source handle (output)
```

**Features:**
- Icon: ArrowLeftRight
- Color: Emerald green (#10B981)
- Displays: Token amounts, from/to tokens
- Handles: Target (top) + Source (bottom)

---

### 3. StakeNode (Cyber Purple Theme)

```
                 ● ← Target handle (input)
┌────────────────┴────────────────┐
│ ═══════════════════════════════ │ ← Gradient top border (purple)
│                                 │
│  [🔒] STAKE                     │ ← Lock icon + Type label
│                                 │
│  Stake 100 GAS in Pool A        │ ← Main display text
│                                 │
│  [100 GAS]                      │ ← Amount badge
│  Pool: Pool A                   │ ← Pool details
│  Duration: 30 days              │ ← Optional duration
│                                 │
└────────────────┬────────────────┘
                 ● ← Source handle (output)
```

**Features:**
- Icon: Lock
- Color: Purple (#A855F7)
- Displays: Amount, pool name, duration
- Handles: Target (top) + Source (bottom)

---

### 4. TransferNode (Amber Theme)

```
                 ● ← Target handle (input)
┌────────────────┴────────────────┐
│ ═══════════════════════════════ │ ← Gradient top border (amber/orange)
│                                 │
│  [📤] TRANSFER                  │ ← Send icon + Type label
│                                 │
│  Send 50 NEO                    │ ← Amount and token
│                                 │
│  [50 NEO]                       │ ← Amount badge
│  To: NXXXyy...z123              │ ← Truncated address
│                                 │
└────────────────┬────────────────┘
                 ● ← Source handle (output)
```

**Features:**
- Icon: Send
- Color: Amber (#FBBF24)
- Displays: Amount, token, recipient address
- Handles: Target (top) + Source (bottom)
- Address truncation: Shows first 6 and last 4 chars

---

## Complete Workflow Example

### Input Text
```
"When GAS price falls below $5, swap 10 GAS for NEO"
```

### Visual Graph Output

```
┌─────────────────────────────────┐
│ ═══════════════════════════════ │ (Blue gradient)
│  [💲] TRIGGER                   │
│  GAS below $5.00                │
│  [price]                        │
└────────────────┬────────────────┘
                 │
                 │ (Animated cyan edge)
                 ↓
                 ●
┌────────────────┴────────────────┐
│ ═══════════════════════════════ │ (Green gradient)
│  [⇄] SWAP                       │
│  10 GAS → NEO                   │
│  [GAS] ⇄ [NEO]                  │
└─────────────────────────────────┘
```

---

## Graph Canvas Features

### Control Panel (Bottom Right)
```
┌─────────────┐
│  [+]        │  Zoom In
│  [-]        │  Zoom Out
│  [⊡]        │  Fit View
└─────────────┘
```

### MiniMap (Bottom Left)
```
┌──────────────────┐
│  ┌─┐             │  Colored nodes
│  │ │             │  represent graph
│  └┬┘             │  overview
│   │              │
│  ┌▼┐             │  Click to
│  └─┘             │  navigate
└──────────────────┘
```

### Info Panel (Top Left)
```
┌─────────────────────────────────┐
│  Auto DCA into NEO              │  Workflow name
│  When GAS price falls below...  │  Description
│                                 │
│  [2 nodes] [1 edge]             │  Statistics
└─────────────────────────────────┘
```

### Background
```
· · · · · · · · · · · · · ·
· · · · · · · · · · · · · ·  Dot pattern
· · · · · · · · · · · · · ·  for visual
· · · · · · · · · · · · · ·  reference
```

---

## Interactive Features

### Pan
- **Action:** Click and drag on background
- **Visual:** Cursor changes to grab/grabbing hand
- **Result:** Entire graph moves

### Zoom
- **Mouse Wheel:** Scroll up/down
- **Controls:** Click +/- buttons
- **Pinch:** Two-finger gesture on trackpad
- **Range:** 0.1x to 2.0x

### Select Node
- **Action:** Click on any node
- **Visual:** Node border glows with type color
- **Result:** Node highlighted, shadow effect applied

### Drag Node
- **Action:** Click and drag node
- **Visual:** Node follows cursor
- **Result:** Position updated, edges remain connected

### Fit View
- **Action:** Click fit view button
- **Visual:** Graph animates to center
- **Result:** All nodes visible with padding

---

## Color Palette Reference

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Trigger Node | Cyber Blue | #00D9FF | Border, icon, badges |
| Swap Node | Cyber Green | #10B981 | Border, icon, badges |
| Stake Node | Cyber Purple | #A855F7 | Border, icon, badges |
| Transfer Node | Amber | #FBBF24 | Border, icon, badges |
| Edge Default | Cyber Blue | #00D9FF (60% opacity) | Connection lines |
| Background | Slate | #64748B (20% opacity) | Dot pattern |
| Card BG | Dark | #0F172A | Node backgrounds |
| Text Primary | White | #FFFFFF | Main labels |
| Text Muted | Gray | #94A3B8 | Secondary text |

---

## Responsive Behavior

### Desktop (>1024px)
- Container: max-w-7xl (80rem / 1280px)
- Graph height: 600px fixed
- All controls visible
- MiniMap expanded

### Tablet (768px - 1024px)
- Container: max-w-5xl (64rem / 1024px)
- Graph height: 600px fixed
- Controls visible
- MiniMap smaller

### Mobile (<768px)
- Container: Full width with padding
- Graph height: 500px (adjustable)
- Touch gestures enabled
- MiniMap optional/collapsible

---

## Animation Details

### Edges
- **Type:** Animated dashed line
- **Speed:** 1s per cycle
- **Color:** Cyan (#00D9FF) at 60% opacity
- **Stroke:** 2px width

### Node Selection
- **Transition:** 200ms ease
- **Shadow:** Glowing box-shadow matching type color
- **Border:** Thickens from 2px to 3px

### Graph Load
- **Effect:** Fade in + slide up
- **Duration:** 300ms
- **Easing:** Ease-out

### Fit View
- **Duration:** 500ms
- **Easing:** Smooth
- **Padding:** 20% around edges

---

## Accessibility Features

### Keyboard Navigation
- **Tab:** Focus next node
- **Shift+Tab:** Focus previous node
- **Arrow Keys:** Pan graph
- **+/-:** Zoom in/out

### Screen Readers
- **Labels:** All nodes have aria-labels
- **Roles:** Proper ARIA roles assigned
- **Descriptions:** Alt text for icons

### Color Contrast
- **Text on Dark:** 4.5:1 ratio (WCAG AA)
- **Icons:** High contrast against backgrounds
- **Borders:** Visible in all states

---

## Usage Examples

### Basic Implementation

```typescript
import WorkflowGraph from '@/components/workflow/WorkflowGraph';

<WorkflowGraph
  nodes={[
    {
      id: "trigger_1",
      type: "trigger",
      position: { x: 250, y: 0 },
      data: {
        label: "GAS below $5.00",
        icon: "dollar-sign",
        type: "price",
        token: "GAS",
        operator: "below",
        value: 5.0
      }
    },
    {
      id: "action_1",
      type: "swap",
      position: { x: 250, y: 150 },
      data: {
        label: "10 GAS → NEO",
        icon: "arrow-left-right",
        from_token: "GAS",
        to_token: "NEO",
        amount: 10.0
      }
    }
  ]}
  edges={[
    {
      id: "e1",
      source: "trigger_1",
      target: "action_1",
      type: "default",
      animated: true
    }
  ]}
  workflowName="Auto DCA into NEO"
  workflowDescription="When GAS price falls below $5, swap 10 GAS for NEO"
/>
```

---

## Future Enhancements (Phase 4+)

### Execution Visualization
- Real-time status updates
- Progress indicators on nodes
- Execution logs panel

### Interactive Editing
- Add nodes via toolbar
- Edit node parameters inline
- Drag to reconnect edges

### Advanced Layouts
- Auto-layout algorithms
- Hierarchical tree view
- Force-directed graphs

### Export/Share
- Download as PNG/SVG
- Copy shareable URL
- Embed code generation

---

*Visual Guide v1.0*
*Story 3.4: React Flow Graph Display*
*Last Updated: December 6, 2025*
