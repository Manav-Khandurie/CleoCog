// File: src/api/upload.ts
import axios from 'axios';
import { VITE_BACKEND_URL } from '@/utils/vars';
export const createSession = async (): Promise<string> => {
  const res = await axios.get(`${VITE_BACKEND_URL}/createSession`);
  return res.data;
};

export const getPresignedUrls = async (sessionId: string, filenames: string[]): Promise<string[]> => {
    console.log(filenames, sessionId.session_id)
    console.log(typeof filenames, typeof sessionId.session_id);
    const res = await axios.post(`${VITE_BACKEND_URL}/uploadDocs`, {
    session_id: sessionId.session_id,
    filenames
  });
  return res.data; // array of presigned URLs
};

export const registerDocuments = async (sessionId: string, tag: string, yt_list: string[]) => {
  return axios.post(`${VITE_BACKEND_URL}/store`, {
    session_id: sessionId.session_id,
    tag : "test_frontend_user",
    yt_list: []
  });
};

export const uploadFileToS3 = async (url: string, file: File) => {
  return axios.put(url, file, {
    headers: {
      'Content-Type': file.type
    }
  });
};
