import React from 'react';

const PREVIOUS_INJURY_OPTIONS = [
  { value: 'none', label: 'None' },
  { value: 'calves', label: 'Calves' },
  { value: 'hamstrings', label: 'Hamstrings' },
  { value: 'quadriceps', label: 'Quadriceps' },
];
const MUSCLE_GROUP_OPTIONS = [
  { value: 'calves', label: 'Calves' },
  { value: 'hamstrings', label: 'Hamstrings' },
  { value: 'quadriceps', label: 'Quadriceps' },
];
const CONTRACTION_TYPE_OPTIONS = [
  { value: 'isometric', label: 'Isometric' },
  { value: 'isotonic', label: 'Isotonic' },
];

type UserFormProps = {
  initialValues: any;
  onChange: (values: any) => void;
  disabled?: boolean;
};

export default function UserRegistrationForm({ initialValues, onChange, disabled }: UserFormProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    onChange({ ...initialValues, [name]: value });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
      <div>
        <label className="block font-semibold text-black mb-2">Name</label>
        <input
          type="text"
          name="name"
          value={initialValues.name}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          placeholder="Enter name"
        />
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Age</label>
        <input
          type="number"
          name="age"
          value={initialValues.age}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          min={10}
          max={100}
          placeholder="Enter age"
        />
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Height (cm)</label>
        <input
          type="number"
          name="height"
          value={initialValues.height}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          min={100}
          max={250}
          placeholder="Enter height"
        />
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Weight (kg)</label>
        <input
          type="number"
          name="weight"
          value={initialValues.weight}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          min={30}
          max={200}
          placeholder="Enter weight"
        />
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Training Frequency (sessions/week)</label>
        <input
          type="number"
          name="training_frequency"
          value={initialValues.training_frequency}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm placeholder-gray-400 text-black bg-white"
          min={1}
          max={7}
          placeholder="Sessions per week"
        />
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Previous Injury</label>
        <select
          name="previous_injury"
          value={initialValues.previous_injury}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm text-black bg-white"
        >
          <option value="" disabled className="text-gray-400">Select previous injury</option>
          {PREVIOUS_INJURY_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Muscle Group</label>
        <select
          name="muscle_group"
          value={initialValues.muscle_group}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm text-black bg-white"
        >
          <option value="" disabled className="text-gray-400">Select muscle group</option>
          {MUSCLE_GROUP_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block font-semibold text-black mb-2">Contraction Type</label>
        <select
          name="contraction_type"
          value={initialValues.contraction_type}
          onChange={handleChange}
          disabled={disabled}
          className="w-full border border-gray-300 rounded-lg px-4 py-2 shadow-sm text-black bg-white"
        >
          <option value="" disabled className="text-gray-400">Select contraction type</option>
          {CONTRACTION_TYPE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
