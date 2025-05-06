// src/hooks/useUpload.ts
import { getPresignedUrls, uploadFileToS3, registerDocuments } from '@/api/upload';

export const useUpload = () => {
  const uploadFiles = async (
    files: File[],
    sessionId: string,
    tag: string = '',
    yt_list: string[] = []
  ) => {
    const filenames = files.map(file => file.name);
    const { presigned_urls } = await getPresignedUrls(sessionId, filenames);
  
    await Promise.all(
      files.map(file => {
        const url = presigned_urls[file.name];
        return uploadFileToS3(url, file);
      })
    );
  
    await registerDocuments(sessionId, tag, yt_list);
    return sessionId;
  };

  return { uploadFiles };
};
