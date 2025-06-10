import axios from 'axios';
import type { UserType } from '@/components/UserRegistrationForm';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export const uploadUserAndEMGData = async (user: UserType, emgData: number[]) => {
  const response = await axios.post(`${API_BASE_URL}/upload/`, {
    user,
    emg_data: emgData,
  });
  return response.data;
};

// You can add more API functions here as you build more features.
