import { Position, type Node } from "@xyflow/react";
import {
  Clock,
  ArrowLeftRight,
  Lock,
  Send,
  type LucideIcon,
} from "lucide-react";

// Node dimensions - fixed size for consistent layout
export const NODE_SIZE = {
  width: 260,
  height: 80,
} as const;

// Handle configuration type
export type HandleConfig = {
  id?: string;
  type: "source" | "target";
  position: Position;
  x: number;
  y: number;
};

// Node type identifiers
export type SpicaNodeType = "trigger" | "swap" | "stake" | "transfer";

// Node configuration
export interface NodeConfig {
  id: SpicaNodeType;
  title: string;
  description: string;
  icon: LucideIcon;
  handles: HandleConfig[];
  // Spica-specific styling
  color: {
    primary: string; // Main color (e.g., "#F59E0B")
    bg: string; // Background with opacity
    border: string; // Border color
    glow: string; // Glow effect
  };
}

// Icon mapping for dynamic lookup
export const iconMapping: Record<SpicaNodeType, LucideIcon> = {
  trigger: Clock,
  swap: ArrowLeftRight,
  stake: Lock,
  transfer: Send,
};

// Node configurations
// Colors use CSS variables defined in globals.css for theme-awareness
export const nodesConfig: Record<SpicaNodeType, NodeConfig> = {
  trigger: {
    id: "trigger",
    title: "Trigger",
    description: "Start workflow on price or time condition",
    icon: Clock,
    handles: [
      {
        type: "source",
        position: Position.Bottom,
        x: NODE_SIZE.width / 2,
        y: NODE_SIZE.height,
      },
    ],
    color: {
      primary: "var(--node-trigger)",
      bg: "var(--node-trigger-bg)",
      border: "var(--node-trigger-border)",
      glow: "rgba(245, 158, 11, 0.15)",
    },
  },
  swap: {
    id: "swap",
    title: "Swap",
    description: "Exchange tokens on DEX",
    icon: ArrowLeftRight,
    handles: [
      {
        type: "target",
        position: Position.Top,
        x: NODE_SIZE.width / 2,
        y: 0,
      },
      {
        type: "source",
        position: Position.Bottom,
        x: NODE_SIZE.width / 2,
        y: NODE_SIZE.height,
      },
    ],
    color: {
      primary: "var(--node-swap)",
      bg: "var(--node-swap-bg)",
      border: "var(--node-swap-border)",
      glow: "rgba(6, 182, 212, 0.15)",
    },
  },
  stake: {
    id: "stake",
    title: "Stake",
    description: "Stake tokens for yield",
    icon: Lock,
    handles: [
      {
        type: "target",
        position: Position.Top,
        x: NODE_SIZE.width / 2,
        y: 0,
      },
      {
        type: "source",
        position: Position.Bottom,
        x: NODE_SIZE.width / 2,
        y: NODE_SIZE.height,
      },
    ],
    color: {
      primary: "var(--node-stake)",
      bg: "var(--node-stake-bg)",
      border: "var(--node-stake-border)",
      glow: "rgba(16, 185, 129, 0.15)",
    },
  },
  transfer: {
    id: "transfer",
    title: "Transfer",
    description: "Send tokens to address",
    icon: Send,
    handles: [
      {
        type: "target",
        position: Position.Top,
        x: NODE_SIZE.width / 2,
        y: 0,
      },
    ],
    color: {
      primary: "var(--node-transfer)",
      bg: "var(--node-transfer-bg)",
      border: "var(--node-transfer-border)",
      glow: "rgba(59, 130, 246, 0.15)",
    },
  },
};

// Workflow node data interface
export interface WorkflowNodeData {
  title?: string;
  label?: string;
  icon?: SpicaNodeType;
  status?: "initial" | "loading" | "success" | "error";
  // Node-specific data
  [key: string]: unknown;
}

// Type-safe node type
export type SpicaNode = Node<WorkflowNodeData, SpicaNodeType>;

// Compatible nodes for handle connections
export const compatibleSourceNodes: SpicaNodeType[] = ["swap", "stake", "transfer"];
export const compatibleTargetNodes: SpicaNodeType[] = ["trigger", "swap", "stake"];

// Get compatible nodes based on handle type
export function getCompatibleNodes(
  handleType: "source" | "target"
): SpicaNodeType[] {
  return handleType === "source" ? compatibleSourceNodes : compatibleTargetNodes;
}
