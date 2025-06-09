import React, { useRef } from 'react';

type EMGDataInputProps = {
  value: number[];
  onChange: (data: number[]) => void;
  disabled?: boolean;
};

export default function EMGDataInput({ value, onChange, disabled }: EMGDataInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    // Parse CSV: assume single column, one value per line
    const lines = text.split(/\r?\n/).filter(Boolean);
    const numbers = lines.map(line => parseFloat(line)).filter(num => !isNaN(num));
    onChange(numbers);
  };

  const handleManualChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const input = e.target.value;
    const numbers = input
      .split(/,|\s+/)
      .map(str => parseFloat(str))
      .filter(num => !isNaN(num));
    onChange(numbers);
  };

  return (
    <div className="space-y-2">
      <label className="block font-medium">EMG Data</label>
      <input
        type="file"
        accept=".csv"
        ref={fileInputRef}
        onChange={handleFileChange}
        disabled={disabled}
        className="block"
      />
      <span className="text-sm text-gray-500">or paste comma-separated values below:</span>
      <textarea
        rows={4}
        className="w-full border rounded px-3 py-2"
        value={value.join(', ')}
        onChange={handleManualChange}
        disabled={disabled}
        placeholder="e.g. 0.1, 0.2, 0.3, ..."
      />
      <div className="text-xs text-gray-400">{value.length} values entered</div>
    </div>
  );
}
