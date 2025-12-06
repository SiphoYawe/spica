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

interface TransferFormData {
  token?: string;
  amount?: number;
  percentage?: number;
  to_address?: string;
  recipient?: string;
  [key: string]: unknown;
}

interface TransferFormProps {
  data: TransferFormData;
  onChange: (data: TransferFormData) => void;
  onValidationChange?: (hasErrors: boolean) => void;
}

const TOKENS = ['GAS', 'NEO', 'bNEO'];

// Neo N3 address validation using Base58 regex
const validateNeoAddress = (address: string): boolean => {
  if (!address) return true; // Allow empty for partial input
  // Neo N3 addresses: Base58 format, starts with 'N', 34 characters total
  const neoAddressRegex = /^N[1-9A-HJ-NP-Za-km-z]{33}$/;
  return neoAddressRegex.test(address);
};

export default function TransferForm({ data, onChange, onValidationChange }: TransferFormProps) {
  const [formData, setFormData] = useState<TransferFormData>(data);
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

  const handleChange = (field: keyof TransferFormData, value: string | number) => {
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

    // Validation: Neo N3 address
    if ((field === 'to_address' || field === 'recipient') && typeof value === 'string') {
      const address = value;
      if (address && !validateNeoAddress(address)) {
        newErrors.to_address = 'Invalid Neo N3 address (Base58, starts with N, 34 characters)';
      } else {
        delete newErrors.to_address;
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
          Transfer Action
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

      {/* To Address Input */}
      <div className="space-y-2">
        <Label htmlFor="to_address">To Address</Label>
        <Input
          id="to_address"
          type="text"
          placeholder="NXXXxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          value={formData.to_address || formData.recipient || ''}
          onChange={(e) => handleChange('to_address', e.target.value)}
          className={errors.to_address ? 'border-red-500' : ''}
          aria-invalid={!!errors.to_address}
          aria-describedby={errors.to_address ? 'to_address-error to_address-hint' : 'to_address-hint'}
        />
        {errors.to_address && (
          <p id="to_address-error" className="text-xs text-red-500" role="alert">
            {errors.to_address}
          </p>
        )}
        <p id="to_address-hint" className="text-xs text-muted-foreground">
          Neo N3 address (34 characters, starts with N)
        </p>
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
                ? 'bg-amber-400 text-darker-bg'
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
                ? 'bg-amber-400 text-darker-bg'
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
