// File: src/hooks/useUpload.ts
import { useState } from 'react';
import { createSession, getPresignedUrls, uploadFileToS3, registerDocuments } from '@/api/upload';

export const useUpload = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);

  const startSession = async () => {
    const session = await createSession();
    setSessionId(session);
    return session;
  };

  const uploadFiles = async (files: File[], tag: string = '', yt_list: string[] = []) => {
    const currentSessionId = sessionId || (await startSession());
    const filenames = files.map(file => file.name);
    const { presigned_urls } = await getPresignedUrls(currentSessionId, filenames);
  
    await Promise.all(
      files.map(file => {
        const url = presigned_urls[file.name];
        return uploadFileToS3(url, file);
      })
    );
  
    await registerDocuments(currentSessionId, tag, yt_list);
    return currentSessionId;
  };
  
  return {
    sessionId,
    startSession,
    uploadFiles
  };
};