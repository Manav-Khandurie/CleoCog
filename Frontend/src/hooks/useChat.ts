// src/hooks/useChat.ts
import { useEffect, useState } from "react";
import { VITE_BACKEND_URL } from "@/utils/vars";
import axios from "axios";
const [sessionId, setSessionId] = useState<string | null>(null);

const initializeSession = async () => {
  const res = await axios.get(`${VITE_BACKEND_URL}/createSession`);
  setSessionId(res.data); // Assuming API returns the session_id directly
};

useEffect(() => {
  initializeSession();
}, []);
