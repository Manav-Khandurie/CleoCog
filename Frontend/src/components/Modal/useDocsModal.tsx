
// File: src/components/modal/UploadDocsModal.tsx
import React, { useState } from 'react';
import {
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter,
  ModalBody, ModalCloseButton, Button, Input, VStack, useToast
} from '@chakra-ui/react';
import { useUpload } from '@/hooks/useUpload';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const UploadDocsModal = ({ isOpen, onClose }: Props) => {
  const [files, setFiles] = useState<File[]>([]);
  const toast = useToast();
  const { uploadFiles } = useUpload();

  const handleUpload = async () => {
    try {
      await uploadFiles(files);
      toast({ title: 'Upload successful', status: 'success' });
      onClose();
    } catch (err) {
      console.error(err);
      toast({ title: 'Upload failed', status: 'error' });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Upload Documents</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <Input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files || []))} />
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button colorScheme="blue" onClick={handleUpload}>Upload</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
