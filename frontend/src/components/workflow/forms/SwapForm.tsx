"use client";

import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

interface SwapFormData {
  from_token?: string;
  to_token?: string;
  amount?: number;
  percentage?: number;
  slippage?: number;
  min_output?: number;
  [key: string]: unknown;
}

interface SwapFormProps {
  data: SwapFormData;
  onChange: (data: SwapFormData) => void;
  onValidationChange?: (hasErrors: boolean) => void;
}

const TOKENS = ['GAS', 'NEO', 'bNEO'];

export default function SwapForm({ data, onChange, onValidationChange }: SwapFormProps) {
  const [formData, setFormData] = useState<SwapFormData>(data);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [amountType, setAmountType] = useState<'fixed' | 'percentage'>(
    data.percentage !== undefined ? 'percentage' : 'fixed'
  );

  // Sync form data when prop changes - use JSON comparison to prevent unnecessary updates
  const dataKey = JSON.stringify(data);
  useEffect(() => {
    setFormData(() => data);
    setAmountType(() => data.percentage !== undefined ? 'percentage' : 'fixed');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataKey]);

  const handleChange = (field: keyof SwapFormData, value: string | number) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);

    // Validate on change
    const newErrors = { ...errors };

    // Validation: cannot swap token to itself
    if (field === 'from_token' || field === 'to_token') {
      if (newData.from_token && newData.to_token && newData.from_token === newData.to_token) {
        newErrors.to_token = 'Cannot swap token to itself';
      } else {
        delete newErrors.to_token;
      }
    }

    // Validation: amount must be positive (allow empty during editing)
    if (field === 'amount') {
      if (value === '' || value === null || value === undefined) {
        delete newErrors.amount;
      } else if (typeof value === 'number' && value <= 0) {
        newErrors.amount = 'Amount must be positive';
      } else {
        delete newErrors.amount;
      }
    }

    // Validation: percentage must be between 0-100 (allow empty during editing)
    if (field === 'percentage') {
      if (value === '' || value === null || value === undefined) {
        delete newErrors.percentage;
      } else if (typeof value === 'number' && (value <= 0 || value > 100)) {
        newErrors.percentage = 'Percentage must be between 0 and 100';
      } else {
        delete newErrors.percentage;
      }
    }

    // Validation: slippage must be positive (allow empty during editing)
    if (field === 'slippage') {
      if (value === '' || value === null || value === undefined) {
        delete newErrors.slippage;
      } else if (typeof value === 'number' && value < 0) {
        newErrors.slippage = 'Slippage must be positive';
      } else {
        delete newErrors.slippage;
      }
    }

    setErrors(newErrors);

    // Notify parent about validation state
    if (onValidationChange) {
      onValidationChange(Object.keys(newErrors).length > 0);
    }

    // Propagate changes
    onChange(newData);
  };

  const handleAmountTypeChange = (type: 'fixed' | 'percentage') => {
    setAmountType(type);
    const newData = { ...formData };
    if (type === 'fixed') {
      delete newData.percentage;
    } else {
      delete newData.amount;
    }
    setFormData(newData);
    onChange(newData);
  };

  // Get available "to" tokens (exclude from_token)
  const availableToTokens = TOKENS.filter((token) => token !== formData.from_token);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Badge variant="secondary" className="text-xs">
          Swap Action
        </Badge>
      </div>

      {/* From Token Selection */}
      <div className="space-y-2">
        <Label htmlFor="from_token">From Token</Label>
        <Select
          value={formData.from_token || ''}
          onValueChange={(value) => handleChange('from_token', value)}
        >
          <SelectTrigger id="from_token">
            <SelectValue placeholder="Select token" />
          </SelectTrigger>
          <SelectContent>
            {TOKENS.map((token) => (
              <SelectItem key={token} value={token}>
                {token}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* To Token Selection */}
      <div className="space-y-2">
        <Label htmlFor="to_token">To Token</Label>
        <Select
          value={formData.to_token || ''}
          onValueChange={(value) => handleChange('to_token', value)}
          disabled={!formData.from_token}
        >
          <SelectTrigger
            id="to_token"
            className={errors.to_token ? 'border-red-500' : ''}
            aria-invalid={!!errors.to_token}
            aria-describedby={errors.to_token ? 'to_token-error' : undefined}
          >
            <SelectValue placeholder="Select token" />
          </SelectTrigger>
          <SelectContent>
            {availableToTokens.map((token) => (
              <SelectItem key={token} value={token}>
                {token}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.to_token && (
          <p id="to_token-error" className="text-xs text-red-500" role="alert">
            {errors.to_token}
          </p>
        )}
      </div>

      {/* Amount Type Selector */}
      <div className="space-y-2">
        <Label id="amount-type-label">Amount Type</Label>
        <div className="flex gap-2" role="radiogroup" aria-labelledby="amount-type-label">
          <button
            type="button"
            role="radio"
            aria-checked={amountType === 'fixed'}
            onClick={() => handleAmountTypeChange('fixed')}
            className={`flex-1 rounded-md px-3 py-2 text-sm transition-colors ${
              amountType === 'fixed'
                ? 'bg-cyber-blue text-darker-bg'
                : 'bg-darker-bg text-foreground border border-card-border hover:bg-card'
            }`}
          >
            Fixed Amount
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={amountType === 'percentage'}
            onClick={() => handleAmountTypeChange('percentage')}
            className={`flex-1 rounded-md px-3 py-2 text-sm transition-colors ${
              amountType === 'percentage'
                ? 'bg-cyber-blue text-darker-bg'
                : 'bg-darker-bg text-foreground border border-card-border hover:bg-card'
            }`}
          >
            Percentage
          </button>
        </div>
      </div>

      {/* Amount Input */}
      {amountType === 'fixed' ? (
        <div className="space-y-2">
          <Label htmlFor="amount">Amount</Label>
          <Input
            id="amount"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0.00"
            value={formData.amount || ''}
            onChange={(e) => {
              const val = e.target.value === '' ? '' : parseFloat(e.target.value);
              handleChange('amount', val);
            }}
            className={errors.amount ? 'border-red-500' : ''}
            aria-invalid={!!errors.amount}
            aria-describedby={errors.amount ? 'amount-error' : undefined}
          />
          {errors.amount && (
            <p id="amount-error" className="text-xs text-red-500" role="alert">
              {errors.amount}
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          <Label htmlFor="percentage">Percentage (%)</Label>
          <Input
            id="percentage"
            type="number"
            step="1"
            min="1"
            max="100"
            placeholder="0"
            value={formData.percentage || ''}
            onChange={(e) => {
              const val = e.target.value === '' ? '' : parseFloat(e.target.value);
              handleChange('percentage', val);
            }}
            className={errors.percentage ? 'border-red-500' : ''}
            aria-invalid={!!errors.percentage}
            aria-describedby={errors.percentage ? 'percentage-error' : undefined}
          />
          {errors.percentage && (
            <p id="percentage-error" className="text-xs text-red-500" role="alert">
              {errors.percentage}
            </p>
          )}
        </div>
      )}

      {/* Slippage Input (Optional) */}
      <div className="space-y-2">
        <Label htmlFor="slippage">Slippage Tolerance (%) - Optional</Label>
        <Input
          id="slippage"
          type="number"
          step="0.1"
          min="0"
          placeholder="1.0"
          value={formData.slippage !== undefined ? formData.slippage : ''}
          onChange={(e) => {
            const val = e.target.value === '' ? '' : parseFloat(e.target.value);
            handleChange('slippage', val);
          }}
          className={errors.slippage ? 'border-red-500' : ''}
          aria-invalid={!!errors.slippage}
          aria-describedby={errors.slippage ? 'slippage-error slippage-hint' : 'slippage-hint'}
        />
        {errors.slippage && (
          <p id="slippage-error" className="text-xs text-red-500" role="alert">
            {errors.slippage}
          </p>
        )}
        <p id="slippage-hint" className="text-xs text-muted-foreground">Default: 1%</p>
      </div>
    </div>
  );
}
