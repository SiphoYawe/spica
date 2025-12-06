import { useState, useEffect, useRef } from 'react';
import type { Node } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { X, Save, RotateCcw } from 'lucide-react';
import { TriggerForm, SwapForm, StakeForm, TransferForm } from './forms';
import { cn } from '@/lib/utils';

interface ParameterPanelProps {
  node: Node | null;
  onClose: () => void;
  onSave: (nodeId: string, data: Record<string, unknown>) => void;
  className?: string;
}

export default function ParameterPanel({ node, onClose, onSave, className }: ParameterPanelProps) {
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [hasValidationErrors, setHasValidationErrors] = useState(false);
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (node) {
      // Initialize form data from node data
      setFormData({ ...node.data });
      setHasChanges(false);
      setHasValidationErrors(false);

      // Focus the panel when it opens
      if (cardRef.current) {
        cardRef.current.focus();
      }
    }
  }, [node]);

  // Keyboard event handler for Escape key
  const handleCancel = () => {
    if (hasChanges) {
      setShowUnsavedDialog(true);
    } else {
      onClose();
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && node) {
        e.preventDefault();
        if (hasChanges) {
          setShowUnsavedDialog(true);
        } else {
          onClose();
        }
      }
    };

    if (node) {
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [node, hasChanges, onClose]);

  if (!node) {
    return null;
  }

  const handleFormChange = (data: Record<string, unknown>) => {
    setFormData(data);
    setHasChanges(true);
  };

  const handleValidationChange = (hasErrors: boolean) => {
    setHasValidationErrors(hasErrors);
  };

  const handleSave = () => {
    onSave(node.id, formData);
    setHasChanges(false);
  };

  const handleReset = () => {
    setFormData({ ...node.data });
    setHasChanges(false);
  };

  const handleConfirmClose = () => {
    setShowUnsavedDialog(false);
    setHasChanges(false);
    onClose();
  };

  const handleCancelClose = () => {
    setShowUnsavedDialog(false);
  };

  // Render the appropriate form based on node type
  const renderForm = () => {
    switch (node.type) {
      case 'trigger':
        return (
          <TriggerForm
            data={formData}
            onChange={handleFormChange}
            onValidationChange={handleValidationChange}
          />
        );
      case 'swap':
        return (
          <SwapForm
            data={formData}
            onChange={handleFormChange}
            onValidationChange={handleValidationChange}
          />
        );
      case 'stake':
        return (
          <StakeForm
            data={formData}
            onChange={handleFormChange}
            onValidationChange={handleValidationChange}
          />
        );
      case 'transfer':
        return (
          <TransferForm
            data={formData}
            onChange={handleFormChange}
            onValidationChange={handleValidationChange}
          />
        );
      default:
        return (
          <div className="text-center text-muted-foreground py-8">
            No parameters available for this node type.
          </div>
        );
    }
  };

  // Get node type label
  const getNodeTypeLabel = () => {
    switch (node.type) {
      case 'trigger':
        return 'Trigger';
      case 'swap':
        return 'Swap';
      case 'stake':
        return 'Stake';
      case 'transfer':
        return 'Transfer';
      default:
        return 'Node';
    }
  };

  // Get node type color
  const getNodeTypeColor = () => {
    switch (node.type) {
      case 'trigger':
        return 'border-cyber-blue';
      case 'swap':
        return 'border-cyber-green';
      case 'stake':
        return 'border-cyber-purple';
      case 'transfer':
        return 'border-amber-400';
      default:
        return 'border-card-border';
    }
  };

  return (
    <>
      <Card
        ref={cardRef}
        tabIndex={-1}
        className={cn(
          'fixed right-0 top-0 bottom-0 w-96 border-l-2 bg-card shadow-xl z-40 overflow-auto animate-slide-in-right focus:outline-none',
          getNodeTypeColor(),
          className
        )}
      >
        {/* Header */}
        <CardHeader className="border-b border-card-border">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg flex items-center gap-2">
                {getNodeTypeLabel()} Parameters
              </CardTitle>
              <CardDescription className="text-xs mt-1">
                Node ID: {node.id}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancel}
              className="h-8 w-8 -mt-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          {hasChanges && (
            <div className="mt-3 px-3 py-2 bg-amber-950/30 border border-amber-500/30 rounded-md">
              <p className="text-xs text-amber-400">Unsaved changes</p>
            </div>
          )}
        </CardHeader>

        {/* Form Content */}
        <CardContent className="p-6">
          {renderForm()}
        </CardContent>

        {/* Footer Actions */}
        <div className="sticky bottom-0 border-t border-card-border bg-card p-4 space-y-2">
          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={!hasChanges || hasValidationErrors}
              className="flex-1"
              variant="default"
              title={hasValidationErrors ? 'Fix validation errors before applying' : ''}
            >
              <Save className="h-4 w-4 mr-2" />
              Apply
            </Button>
            <Button
              onClick={handleReset}
              disabled={!hasChanges}
              variant="outline"
              title="Reset to original values"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
          {hasValidationErrors && (
            <p className="text-xs text-red-500 text-center" role="alert">
              Please fix validation errors before applying
            </p>
          )}
          <Button
            onClick={handleCancel}
            variant="ghost"
            className="w-full"
          >
            Cancel
          </Button>
        </div>
      </Card>

      {/* Unsaved Changes Dialog */}
      <Dialog open={showUnsavedDialog} onOpenChange={setShowUnsavedDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Unsaved Changes</DialogTitle>
            <DialogDescription>
              You have unsaved changes. Are you sure you want to close without saving?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={handleCancelClose}>
              Keep Editing
            </Button>
            <Button variant="destructive" onClick={handleConfirmClose}>
              Discard Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
