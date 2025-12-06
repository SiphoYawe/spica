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

interface TriggerFormData {
  type?: string;
  token?: string;
  operator?: string;
  value?: number;
  interval?: string;
  time?: string;
  schedule?: string;
  [key: string]: unknown;
}

interface TriggerFormProps {
  data: TriggerFormData;
  onChange: (data: TriggerFormData) => void;
  onValidationChange?: (hasErrors: boolean) => void;
}

const TOKENS = ['GAS', 'NEO', 'bNEO'];
const OPERATORS = [
  { value: 'above', label: 'Above' },
  { value: 'below', label: 'Below' },
  { value: 'equals', label: 'Equals' },
];

export default function TriggerForm({ data, onChange, onValidationChange }: TriggerFormProps) {
  const [formData, setFormData] = useState<TriggerFormData>(data);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Determine trigger type from data
  const triggerType = data.type === 'time' || data.interval || data.time || data.schedule
    ? 'time'
    : 'price';

  useEffect(() => {
    setFormData(data);
  }, [data]);

  const handleChange = (field: keyof TriggerFormData, value: string | number) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);

    // Validate on change
    const newErrors = { ...errors };

    // Handle empty input separately (allow during editing)
    if (field === 'value') {
      if (value === '' || value === null || value === undefined) {
        delete newErrors.value;
      } else if (typeof value === 'number' && value <= 0) {
        newErrors.value = 'Value must be positive';
      } else {
        delete newErrors.value;
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

  if (triggerType === 'price') {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Badge variant="secondary" className="text-xs">
            Price Trigger
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

        {/* Operator Selection */}
        <div className="space-y-2">
          <Label htmlFor="operator">Condition</Label>
          <Select
            value={formData.operator || ''}
            onValueChange={(value) => handleChange('operator', value)}
          >
            <SelectTrigger id="operator">
              <SelectValue placeholder="Select condition" />
            </SelectTrigger>
            <SelectContent>
              {OPERATORS.map((op) => (
                <SelectItem key={op.value} value={op.value}>
                  {op.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Value Input */}
        <div className="space-y-2">
          <Label htmlFor="value">Price (USD)</Label>
          <Input
            id="value"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0.00"
            value={formData.value || ''}
            onChange={(e) => {
              const val = e.target.value === '' ? '' : parseFloat(e.target.value);
              handleChange('value', val);
            }}
            className={errors.value ? 'border-red-500' : ''}
            aria-invalid={!!errors.value}
            aria-describedby={errors.value ? 'value-error' : undefined}
          />
          {errors.value && (
            <p id="value-error" className="text-xs text-red-500" role="alert">
              {errors.value}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Time Trigger
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Badge variant="secondary" className="text-xs">
          Time Trigger
        </Badge>
      </div>

      {/* Schedule Input */}
      <div className="space-y-2">
        <Label htmlFor="schedule">Schedule</Label>
        <Input
          id="schedule"
          type="text"
          placeholder="e.g., '5pm daily' or '0 17 * * *'"
          value={formData.schedule || formData.interval || formData.time || ''}
          onChange={(e) => handleChange('schedule', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Natural language (5pm daily) or cron format
        </p>
      </div>
    </div>
  );
}
