# Spica Frontend

The frontend for Spica - an AI-powered DeFi workflow builder for Neo N3. Built with Next.js 16, React 19, and Tailwind CSS v4.

## Tech Stack

- **Next.js 16** - React framework with App Router and Turbopack
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Utility-first styling
- **shadcn/ui** - Accessible component library
- **ReactFlow** - Workflow graph visualization
- **Zustand** - Lightweight state management
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server with Turbopack
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Available Scripts

```bash
npm run dev      # Start development server with Turbopack
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Main workflow builder page
│   └── globals.css         # Tailwind CSS global styles
│
├── components/
│   ├── layout/             # App layout components
│   │   ├── AppLayout.tsx   # Main app shell
│   │   ├── Sidebar.tsx     # Navigation sidebar
│   │   ├── CanvasHeader.tsx# Workflow canvas toolbar
│   │   └── PropertiesPanel.tsx # Node properties editor
│   │
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   │
│   └── workflow/           # Workflow-specific components
│       ├── WorkflowCanvas.tsx  # ReactFlow canvas
│       ├── NLInput.tsx         # Natural language input
│       ├── nodes/              # Custom node types
│       │   ├── BaseNode.tsx
│       │   ├── TriggerNode.tsx
│       │   ├── SwapNode.tsx
│       │   ├── StakeNode.tsx
│       │   └── TransferNode.tsx
│       └── forms/              # Node configuration forms
│
├── stores/                 # Zustand state stores
│   ├── workflowStore.ts    # Workflow state
│   ├── paymentStore.ts     # Payment/x402 state
│   └── uiStore.ts          # UI preferences
│
├── api/                    # API client
│   └── client.ts           # Backend API wrapper
│
├── hooks/                  # Custom React hooks
│   └── usePayment.ts       # x402 payment hook
│
├── lib/                    # Utilities
│   └── utils.ts            # Helper functions
│
└── types/                  # TypeScript types
    └── api.ts              # API response types
```

## Adding shadcn/ui Components

This project uses [shadcn/ui](https://ui.shadcn.com/) for accessible, customizable components.

```bash
# Add a new component
npx shadcn@latest add <component-name>

# Examples
npx shadcn@latest add calendar
npx shadcn@latest add form
npx shadcn@latest add table
```

## State Management

The app uses Zustand for state management with three main stores:

### workflowStore
Manages workflow state including nodes, edges, parsing, and generation.

```tsx
import { useWorkflowStore } from '@/stores';

const { nodes, edges, setNodes } = useWorkflowStore();
```

### paymentStore
Handles x402 payment modal and payment state.

```tsx
import { usePaymentStore } from '@/stores';

const { isOpen, openModal, closeModal } = usePaymentStore();
```

### uiStore
Controls UI preferences like minimap, grid visibility, and panel states.

```tsx
import { useUiStore } from '@/stores';

const { minimapVisible, toggleMinimap } = useUiStore();
```

## Environment Variables

Create a `.env.local` file:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Demo Mode
NEXT_PUBLIC_DEMO_MODE=true
```

## Building for Production

```bash
# Build
npm run build

# The build output is in .next/
# For Docker, use standalone output mode
```

## Docker

The frontend includes Dockerfiles for both development and production:

- `Dockerfile` - Development container with hot reload
- `Dockerfile.prod` - Production build with standalone output

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [ReactFlow](https://reactflow.dev/)
- [Zustand](https://zustand-demo.pmnd.rs/)
