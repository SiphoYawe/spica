"use client";

import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { useWorkflowStore, useUiStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, Zap, ArrowLeftRight, Lock, Send, Save, Trash2, Check, Clock, DollarSign, Calendar } from "lucide-react";
import { toast } from "sonner";

// Supported tokens on Neo N3
const SUPPORTED_TOKENS = [
  { value: "NEO", label: "NEO", description: "Neo Token" },
  { value: "GAS", label: "GAS", description: "Gas Token" },
  { value: "bNEO", label: "bNEO", description: "Wrapped NEO" },
  { value: "FLM", label: "FLM", description: "Flamingo Token" },
  { value: "FUSDT", label: "fUSDT", description: "Flamingo USDT" },
];

// Time intervals for scheduling
const TIME_INTERVALS = [
  { value: "hourly", label: "Every Hour" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

// Days of week for weekly schedule
const DAYS_OF_WEEK = [
  { value: "monday", label: "Monday" },
  { value: "tuesday", label: "Tuesday" },
  { value: "wednesday", label: "Wednesday" },
  { value: "thursday", label: "Thursday" },
  { value: "friday", label: "Friday" },
  { value: "saturday", label: "Saturday" },
  { value: "sunday", label: "Sunday" },
];

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
  const { getSelectedNode, updateNodeData, setSelectedNodeId, removeNode } = useWorkflowStore();

  const selectedNode = getSelectedNode();

  // Local form state to track changes before saving
  const [localData, setLocalData] = useState<Record<string, unknown>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Sync local state when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setLocalData({ ...selectedNode.data });
      setHasChanges(false);
    }
  }, [selectedNode?.id]);

  if (!propertiesPanelOpen || !selectedNode) {
    return null;
  }

  const nodeType = selectedNode.type || "trigger";
  const Icon = nodeIcons[nodeType] || Zap;
  const colors = nodeColors[nodeType] || nodeColors.trigger;

  const handleClose = () => {
    closePropertiesPanel();
    setSelectedNodeId(null);
    setLocalData({});
    setHasChanges(false);
  };

  // Update local state (not the store yet)
  const handleLocalUpdate = (key: string, value: unknown) => {
    setLocalData(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  // Save changes to the store
  const handleSave = () => {
    setIsSaving(true);

    // Apply all local changes to the store
    updateNodeData(selectedNode.id, localData);

    // Show success feedback
    setTimeout(() => {
      setIsSaving(false);
      setHasChanges(false);
      toast.success("Node updated successfully", {
        description: `${nodeType.charAt(0).toUpperCase() + nodeType.slice(1)} node properties saved.`,
      });
    }, 300);
  };

  // Delete the node
  const handleDelete = () => {
    removeNode(selectedNode.id);
    handleClose();
    toast.success("Node deleted", {
      description: `${nodeType.charAt(0).toUpperCase() + nodeType.slice(1)} node removed from workflow.`,
    });
  };

  // Get trigger type for conditional rendering
  const triggerType = (localData.type as string) || "price";

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
              value={(localData.label as string) || ""}
              onChange={(e) => handleLocalUpdate("label", e.target.value)}
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
                  value={triggerType}
                  onValueChange={(value) => handleLocalUpdate("type", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-3.5 w-3.5" />
                        Price Condition
                      </div>
                    </SelectItem>
                    <SelectItem value="time">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3.5 w-3.5" />
                        Time Schedule
                      </div>
                    </SelectItem>
                    <SelectItem value="event">
                      <div className="flex items-center gap-2">
                        <Zap className="h-3.5 w-3.5" />
                        On-chain Event
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Price Trigger Fields */}
              {triggerType === "price" && (
                <>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Token
                    </Label>
                    <Select
                      value={(localData.token as string) || ""}
                      onValueChange={(value) => handleLocalUpdate("token", value)}
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Select token" />
                      </SelectTrigger>
                      <SelectContent>
                        {SUPPORTED_TOKENS.map((token) => (
                          <SelectItem key={token.value} value={token.value}>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{token.label}</span>
                              <span className="text-xs text-muted-foreground">
                                {token.description}
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Condition
                      </Label>
                      <Select
                        value={(localData.operator as string) || ">"}
                        onValueChange={(value) => handleLocalUpdate("operator", value)}
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value=">">Greater than</SelectItem>
                          <SelectItem value="<">Less than</SelectItem>
                          <SelectItem value=">=">Greater or equal</SelectItem>
                          <SelectItem value="<=">Less or equal</SelectItem>
                          <SelectItem value="==">Equal to</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Price ($)
                      </Label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={(localData.value as number) ?? ""}
                        onChange={(e) => handleLocalUpdate("value", e.target.value === "" ? "" : parseFloat(e.target.value))}
                        className="h-9"
                        placeholder="0.00"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Time Trigger Fields */}
              {triggerType === "time" && (
                <>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Interval
                    </Label>
                    <Select
                      value={(localData.interval as string) || "daily"}
                      onValueChange={(value) => handleLocalUpdate("interval", value)}
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Select interval" />
                      </SelectTrigger>
                      <SelectContent>
                        {TIME_INTERVALS.map((interval) => (
                          <SelectItem key={interval.value} value={interval.value}>
                            {interval.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Show day selector for weekly */}
                  {(localData.interval as string) === "weekly" && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Day of Week
                      </Label>
                      <Select
                        value={(localData.dayOfWeek as string) || "monday"}
                        onValueChange={(value) => handleLocalUpdate("dayOfWeek", value)}
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue placeholder="Select day" />
                        </SelectTrigger>
                        <SelectContent>
                          {DAYS_OF_WEEK.map((day) => (
                            <SelectItem key={day.value} value={day.value}>
                              {day.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Show day of month selector for monthly */}
                  {(localData.interval as string) === "monthly" && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-muted-foreground">
                        Day of Month
                      </Label>
                      <Select
                        value={String((localData.dayOfMonth as number) || 1)}
                        onValueChange={(value) => handleLocalUpdate("dayOfMonth", parseInt(value))}
                      >
                        <SelectTrigger className="h-9">
                          <SelectValue placeholder="Select day" />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                            <SelectItem key={day} value={String(day)}>
                              {day}{day === 1 ? "st" : day === 2 ? "nd" : day === 3 ? "rd" : "th"}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Time (24h format)
                    </Label>
                    <Input
                      type="time"
                      value={(localData.time as string) || "09:00"}
                      onChange={(e) => handleLocalUpdate("time", e.target.value)}
                      className="h-9"
                    />
                  </div>

                  {/* Timezone display */}
                  <div className="rounded-md bg-muted/50 p-3">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>Times are in your local timezone</span>
                    </div>
                  </div>
                </>
              )}

              {/* Event Trigger Fields */}
              {triggerType === "event" && (
                <>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Contract Address
                    </Label>
                    <Input
                      value={(localData.contractAddress as string) || ""}
                      onChange={(e) => handleLocalUpdate("contractAddress", e.target.value)}
                      className="h-9 font-mono text-xs"
                      placeholder="0x..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Event Name
                    </Label>
                    <Input
                      value={(localData.eventName as string) || ""}
                      onChange={(e) => handleLocalUpdate("eventName", e.target.value)}
                      className="h-9"
                      placeholder="e.g., Transfer, Approval"
                    />
                  </div>
                </>
              )}
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
                  <Select
                    value={(localData.from_token as string) || ""}
                    onValueChange={(value) => handleLocalUpdate("from_token", value)}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder="Select token" />
                    </SelectTrigger>
                    <SelectContent>
                      {SUPPORTED_TOKENS.filter(t => t.value !== (localData.to_token as string)).map((token) => (
                        <SelectItem key={token.value} value={token.value}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{token.label}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    To Token
                  </Label>
                  <Select
                    value={(localData.to_token as string) || ""}
                    onValueChange={(value) => handleLocalUpdate("to_token", value)}
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder="Select token" />
                    </SelectTrigger>
                    <SelectContent>
                      {SUPPORTED_TOKENS.filter(t => t.value !== (localData.from_token as string)).map((token) => (
                        <SelectItem key={token.value} value={token.value}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{token.label}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount Type
                </Label>
                <Select
                  value={(localData.amountType as string) || "fixed"}
                  onValueChange={(value) => {
                    handleLocalUpdate("amountType", value);
                    // Set default amount when switching to percentage
                    if (value === "percentage" && !localData.amount) {
                      handleLocalUpdate("amount", 50);
                    }
                  }}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Amount</SelectItem>
                    <SelectItem value="percentage">Percentage of Balance</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Amount input - different for fixed vs percentage */}
              {(localData.amountType as string) === "percentage" ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Percentage of Balance
                    </Label>
                    <span className="text-sm font-mono font-medium text-spica">
                      {(localData.amount as number) || 50}%
                    </span>
                  </div>
                  <Slider
                    value={[(localData.amount as number) || 50]}
                    onValueChange={([value]) => handleLocalUpdate("amount", value)}
                    min={1}
                    max={100}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>1%</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    Amount
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={(localData.amount as number) ?? ""}
                    onChange={(e) => handleLocalUpdate("amount", e.target.value === "" ? "" : parseFloat(e.target.value))}
                    className="h-9"
                    placeholder="0.00"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Slippage Tolerance (%)
                </Label>
                <Select
                  value={String((localData.slippage as number) || 0.5)}
                  onValueChange={(value) => handleLocalUpdate("slippage", parseFloat(value))}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.1">0.1%</SelectItem>
                    <SelectItem value="0.5">0.5%</SelectItem>
                    <SelectItem value="1">1%</SelectItem>
                    <SelectItem value="2">2%</SelectItem>
                    <SelectItem value="5">5%</SelectItem>
                  </SelectContent>
                </Select>
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
                <Select
                  value={(localData.token as string) || ""}
                  onValueChange={(value) => handleLocalUpdate("token", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select token" />
                  </SelectTrigger>
                  <SelectContent>
                    {SUPPORTED_TOKENS.map((token) => (
                      <SelectItem key={token.value} value={token.value}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{token.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {token.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount Type
                </Label>
                <Select
                  value={(localData.amountType as string) || "fixed"}
                  onValueChange={(value) => {
                    handleLocalUpdate("amountType", value);
                    if (value === "percentage" && !localData.amount) {
                      handleLocalUpdate("amount", 50);
                    }
                  }}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Amount</SelectItem>
                    <SelectItem value="percentage">Percentage of Balance</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Amount input - different for fixed vs percentage */}
              {(localData.amountType as string) === "percentage" ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Percentage of Balance
                    </Label>
                    <span className="text-sm font-mono font-medium text-spica">
                      {(localData.amount as number) || 50}%
                    </span>
                  </div>
                  <Slider
                    value={[(localData.amount as number) || 50]}
                    onValueChange={([value]) => handleLocalUpdate("amount", value)}
                    min={1}
                    max={100}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>1%</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    Amount
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={(localData.amount as number) ?? ""}
                    onChange={(e) => handleLocalUpdate("amount", e.target.value === "" ? "" : parseFloat(e.target.value))}
                    className="h-9"
                    placeholder="0.00"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Staking Pool
                </Label>
                <Select
                  value={(localData.pool as string) || ""}
                  onValueChange={(value) => handleLocalUpdate("pool", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select pool" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="flamingo">Flamingo Finance</SelectItem>
                    <SelectItem value="neoburger">NeoBurger</SelectItem>
                    <SelectItem value="grandneo">GrandNeo</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Lock Duration
                </Label>
                <Select
                  value={(localData.duration as string) || "30d"}
                  onValueChange={(value) => handleLocalUpdate("duration", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="flexible">Flexible (No Lock)</SelectItem>
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
                <Select
                  value={(localData.token as string) || ""}
                  onValueChange={(value) => handleLocalUpdate("token", value)}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Select token" />
                  </SelectTrigger>
                  <SelectContent>
                    {SUPPORTED_TOKENS.map((token) => (
                      <SelectItem key={token.value} value={token.value}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{token.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {token.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Amount Type
                </Label>
                <Select
                  value={(localData.amountType as string) || "fixed"}
                  onValueChange={(value) => {
                    handleLocalUpdate("amountType", value);
                    if (value === "percentage" && !localData.amount) {
                      handleLocalUpdate("amount", 50);
                    }
                  }}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Amount</SelectItem>
                    <SelectItem value="percentage">Percentage of Balance</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Amount input - different for fixed vs percentage */}
              {(localData.amountType as string) === "percentage" ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-medium text-muted-foreground">
                      Percentage of Balance
                    </Label>
                    <span className="text-sm font-mono font-medium text-spica">
                      {(localData.amount as number) || 50}%
                    </span>
                  </div>
                  <Slider
                    value={[(localData.amount as number) || 50]}
                    onValueChange={([value]) => handleLocalUpdate("amount", value)}
                    min={1}
                    max={100}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>1%</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Label className="text-xs font-medium text-muted-foreground">
                    Amount
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={(localData.amount as number) ?? ""}
                    onChange={(e) => handleLocalUpdate("amount", e.target.value === "" ? "" : parseFloat(e.target.value))}
                    className="h-9"
                    placeholder="0.00"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">
                  Recipient Address
                </Label>
                <Input
                  value={(localData.to_address as string) || ""}
                  onChange={(e) => handleLocalUpdate("to_address", e.target.value)}
                  className="h-9 font-mono text-xs"
                  placeholder="N..."
                />
                <p className="text-xs text-muted-foreground">
                  Neo N3 address starting with N
                </p>
              </div>
            </>
          )}
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="border-t border-border p-4">
        <div className="flex flex-col gap-2">
          {hasChanges && (
            <p className="text-xs text-amber-500 text-center mb-1">
              You have unsaved changes
            </p>
          )}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 gap-2"
              onClick={handleDelete}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </Button>
            <Button
              variant="cyber"
              size="sm"
              className="flex-1 gap-2"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Check className="h-3.5 w-3.5 animate-pulse" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-3.5 w-3.5" />
                  Save
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
