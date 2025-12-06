"use client";

import { cn } from "@/lib/utils";
import { useWorkflowStore, useUiStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, Zap, ArrowLeftRight, Lock, Send, Save, Trash2 } from "lucide-react";

// Node type icons
const nodeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  trigger: Zap,
  swap: ArrowLeftRight,
  stake: Lock,
  transfer: Send,
};

// Node type colors
const nodeColors: Record<string, { text: string; bg: string; border: string }> = {
  trigger: {
    text: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
  },
  swap: {
    text: "text-cyan-500",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
  },
  stake: {
    text: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
  },
  transfer: {
    text: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
  },
};

export function PropertiesPanel() {
  const { closePropertiesPanel, propertiesPanelOpen } = useUiStore();
  const { getSelectedNode, updateNodeData, setSelectedNodeId } = useWorkflowStore();

  const selectedNode = getSelectedNode();

  if (!propertiesPanelOpen || !selectedNode) {
    return null;
  }

  const nodeType = selectedNode.type || "trigger";
  const Icon = nodeIcons[nodeType] || Zap;
  const colors = nodeColors[nodeType] || nodeColors.trigger;

  const handleClose = () => {
    closePropertiesPanel();
    setSelectedNodeId(null);
  };

  const handleUpdate = (key: string, value: unknown) => {
    updateNodeData(selectedNode.id, { [key]: value });
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-border px-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg",
              colors.bg
            )}
          >
            <Icon className={cn("h-4 w-4", colors.text)} />
          </div>
          <div>
            <h3 className="text-sm font-semibold capitalize">{nodeType}</h3>
            <p className="text-xs text-muted-foreground">
              Node Properties
            </p>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="space-y-6 p-4">
          {/* Label */}
          <div className="space-y-2">
            <Label htmlFor="label" className="text-xs font-medium text-muted-foreground">
              Label
            </Label>
            <Input
              id="label"
              value={(selectedNode.data.label as string) || ""}
              onChange={(e) => handleUpdate("label", e.target.value)}
              className="h-9"
              placeholder="Enter node label..."
            />
          </div>

          <Separator />

          {/* Trigger-specific fields */}
          {nodeType === "trigger" && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Trigger Type
                </Label>
                <Select
                  value={(selectedNode.data.type as string) || "price"}
                  onValueChange={(value) => handleUpdate("type", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">Price Condition</SelectItem>
                    <SelectItem value="time">Time Schedule</SelectItem>
                    <SelectItem value="event">On-chain Event</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Token
                </Label>
                <Input
                  value={(selectedNode.data.token as string) || ""}
                  onChange={(e) => handleUpdate("token", e.target.value)}
                  className="h-9"
                  placeholder="e.g., NEO, GAS"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    Operator
                  </Label>
                  <Select
                    value={(selectedNode.data.operator as string) || ">"}
                    onValueChange={(value) => handleUpdate("operator", value)}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value=">">Greater than</SelectItem>
                      <SelectItem value="<">Less than</SelectItem>
                      <SelectItem value=">=">Greater or equal</SelectItem>
                      <SelectItem value="<=">Less or equal</SelectItem>
                      <SelectItem value="=">Equal to</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    Value ($)
                  </Label>
                  <Input
                    type="number"
                    value={(selectedNode.data.value as number) || ""}
                    onChange={(e) => handleUpdate("value", parseFloat(e.target.value))}
                    className="h-9"
                    placeholder="0.00"
                  />
                </div>
              </div>
            </>
          )}

          {/* Swap-specific fields */}
          {nodeType === "swap" && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    From Token
                  </Label>
                  <Input
                    value={(selectedNode.data.from_token as string) || ""}
                    onChange={(e) => handleUpdate("from_token", e.target.value)}
                    className="h-9"
                    placeholder="e.g., NEO"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    To Token
                  </Label>
                  <Input
                    value={(selectedNode.data.to_token as string) || ""}
                    onChange={(e) => handleUpdate("to_token", e.target.value)}
                    className="h-9"
                    placeholder="e.g., GAS"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount
                </Label>
                <Input
                  type="number"
                  value={(selectedNode.data.amount as number) || ""}
                  onChange={(e) => handleUpdate("amount", parseFloat(e.target.value))}
                  className="h-9"
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Minimum Output
                </Label>
                <Input
                  type="number"
                  value={(selectedNode.data.min_output as number) || ""}
                  onChange={(e) => handleUpdate("min_output", parseFloat(e.target.value))}
                  className="h-9"
                  placeholder="0.00"
                />
              </div>
            </>
          )}

          {/* Stake-specific fields */}
          {nodeType === "stake" && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Token
                </Label>
                <Input
                  value={(selectedNode.data.token as string) || ""}
                  onChange={(e) => handleUpdate("token", e.target.value)}
                  className="h-9"
                  placeholder="e.g., NEO"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount
                </Label>
                <Input
                  type="number"
                  value={(selectedNode.data.amount as number) || ""}
                  onChange={(e) => handleUpdate("amount", parseFloat(e.target.value))}
                  className="h-9"
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Pool
                </Label>
                <Input
                  value={(selectedNode.data.pool as string) || ""}
                  onChange={(e) => handleUpdate("pool", e.target.value)}
                  className="h-9"
                  placeholder="Pool name or address"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Duration
                </Label>
                <Select
                  value={(selectedNode.data.duration as string) || "30d"}
                  onValueChange={(value) => handleUpdate("duration", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7d">7 Days</SelectItem>
                    <SelectItem value="30d">30 Days</SelectItem>
                    <SelectItem value="90d">90 Days</SelectItem>
                    <SelectItem value="180d">180 Days</SelectItem>
                    <SelectItem value="365d">1 Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {/* Transfer-specific fields */}
          {nodeType === "transfer" && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Token
                </Label>
                <Input
                  value={(selectedNode.data.token as string) || ""}
                  onChange={(e) => handleUpdate("token", e.target.value)}
                  className="h-9"
                  placeholder="e.g., NEO"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount
                </Label>
                <Input
                  type="number"
                  value={(selectedNode.data.amount as number) || ""}
                  onChange={(e) => handleUpdate("amount", parseFloat(e.target.value))}
                  className="h-9"
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Recipient Address
                </Label>
                <Input
                  value={(selectedNode.data.to_address as string) || ""}
                  onChange={(e) => handleUpdate("to_address", e.target.value)}
                  className="h-9 font-mono text-xs"
                  placeholder="N..."
                />
              </div>
            </>
          )}
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 gap-2">
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </Button>
          <Button variant="cyber" size="sm" className="flex-1 gap-2">
            <Save className="h-3.5 w-3.5" />
            Save
          </Button>
        </div>
      </div>
    </div>
  );
}
