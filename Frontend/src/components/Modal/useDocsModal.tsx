// File: src/components/Modal/UploadDocsModal.tsx
import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Input,
  VStack,
  useToast,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { useUpload } from '@/hooks/useUpload';
import { useChat } from '@/store/Chat'; // Ensure this path is correct

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const UploadDocsModal = ({ isOpen, onClose }: Props) => {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false); // ✅ Correct placement inside component
  const toast = useToast();
  const { uploadFiles } = useUpload();

  const handleUpload = async () => {
    setLoading(true);
    try {
      await uploadFiles(files);
      toast({ title: 'Upload successful', status: 'success' });

      // Add a chat message after success
      useChat.getState().addMessage(
        useChat.getState().selectedChat?.id || '',
        {
          emitter: 'gpt',
          message: '📄 Documents uploaded successfully!',
        }
      );

      onClose();
    } catch (err) {
      console.error(err);
      toast({ title: 'Upload failed', status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Upload Documents</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          {loading ? (
            <Center py={8}>
              <Spinner
                thickness="4px"
                speed="0.65s"
                emptyColor="gray.200"
                color="blue.500"
                size="xl"
              />
            </Center>
          ) : (
            <VStack spacing={4}>
              <Input
                type="file"
                multiple
                onChange={(e) =>
                  setFiles(Array.from(e.target.files || []))
                }
              />
            </VStack>
          )}
        </ModalBody>
        <ModalFooter>
          <Button colorScheme="blue" onClick={handleUpload} isDisabled={files.length === 0}>
            Upload
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
