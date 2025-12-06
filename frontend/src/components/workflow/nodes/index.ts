import type { NodeTypes } from "@xyflow/react";
import { TriggerNode, type TriggerNodeData } from "./trigger-node";
import { SwapNode, type SwapNodeData } from "./swap-node";
import { StakeNode, type StakeNodeData } from "./stake-node";
import { TransferNode, type TransferNodeData } from "./transfer-node";

// Node type registry for ReactFlow
// Type assertion needed due to ReactFlow NodeTypes generics
export const nodeTypes = {
  trigger: TriggerNode,
  swap: SwapNode,
  stake: StakeNode,
  transfer: TransferNode,
} as NodeTypes;

// Re-export node components
export { TriggerNode, SwapNode, StakeNode, TransferNode };

// Re-export data types
export type {
  TriggerNodeData,
  SwapNodeData,
  StakeNodeData,
  TransferNodeData,
};
