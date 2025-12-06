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

interface StakeFormData {
  token?: string;
  amount?: number;
  percentage?: number;
  pool?: string;
  duration?: string;
  [key: string]: unknown;
}

interface StakeFormProps {
  data: StakeFormData;
  onChange: (data: StakeFormData) => void;
  onValidationChange?: (hasErrors: boolean) => void;
}

const TOKENS = ['GAS', 'NEO', 'bNEO'];

export default function StakeForm({ data, onChange, onValidationChange }: StakeFormProps) {
  const [formData, setFormData] = useState<StakeFormData>(data);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [amountType, setAmountType] = useState<'fixed' | 'percentage'>(
    data.percentage !== undefined ? 'percentage' : 'fixed'
  );

  useEffect(() => {
    setFormData(data);
    setAmountType(data.percentage !== undefined ? 'percentage' : 'fixed');
  }, [data]);

  const handleChange = (field: keyof StakeFormData, value: string | number) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);

    // Validate on change
    const newErrors = { ...errors };

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

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Badge variant="secondary" className="text-xs">
          Stake Action
        </Badge>
      </div>

      {/* Token Selection */}
      <div className="space-y-2">
        <Label htmlFor="token">Token</Label>
        <Select
          value={formData.token || ''}
          onValueChange={(value) => handleChange('token', value)}
        >
          <SelectTrigger id="token">
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
                ? 'bg-cyber-purple text-white'
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
                ? 'bg-cyber-purple text-white'
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
    </div>
  );
}
