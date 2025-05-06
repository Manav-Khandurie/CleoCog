// src/api/query.ts
import axios from 'axios';
import { VITE_BACKEND_URL } from '@/utils/vars';

export const fetchChatResponse = async (query: string, tag: string, sessionId: string) => {
  const res = await axios.get(`${VITE_BACKEND_URL}/query`, {
    params: {
      query,
      tag,
      session_id: sessionId
    }
  });

  return res.data.generated_text;
};
