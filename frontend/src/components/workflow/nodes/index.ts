import TriggerNode from './TriggerNode';
import SwapNode from './SwapNode';
import StakeNode from './StakeNode';
import TransferNode from './TransferNode';

export const nodeTypes = {
  trigger: TriggerNode,
  swap: SwapNode,
  stake: StakeNode,
  transfer: TransferNode,
};

export { TriggerNode, SwapNode, StakeNode, TransferNode };
