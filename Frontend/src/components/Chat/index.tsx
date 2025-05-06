//Modules
import gptAvatar from "@/assets/gpt-avatar.svg";
import warning from "@/assets/warning.svg";
import user from "@/assets/user.png";
import { useRef } from "react";
import { useChat } from "@/store/chat";
import { useForm } from "react-hook-form";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { OpenAIApi, Configuration } from "openai";
import { useMutation } from "react-query";
import { v4 } from "uuid";
import axios from "axios";
//Components
import { Input } from "@/components/Input";
import { FiSend, FiUpload } from "react-icons/fi";
import {
    Avatar,
    IconButton,
    Spinner,
    Stack,
    Text,
    InputGroup,
    InputRightElement,
    Input as ChakraInput,
} from "@chakra-ui/react";
import ReactMarkdown from 'react-markdown'
import { Instructions } from "../Layout/Instructions";
import { useAPI } from "@/store/api";
import { useDisclosure } from "@chakra-ui/react";
import { UploadDocsModal } from "@/components/Modal/useDocsModal";
import { useUpload } from "@/hooks/useUpload";
import { createSession } from "@/api/upload";

export interface ChatProps { };

interface ChatSchema {
    input: string
};

export const Chat = ({ ...props }: ChatProps) => {
    const { api } = useAPI();
    const {
        selectedChat,
        addMessage,
        addChat,
        editChat
    } = useChat();
    const selectedId = selectedChat?.id,
        selectedRole = selectedChat?.role;
    const { isOpen, onOpen, onClose } = useDisclosure();
    const { sessionId } = selectedChat || {};

    const hasSelectedChat = selectedChat && selectedChat?.content.length > 0;

    const {
        register,
        setValue,
        handleSubmit
    } = useForm<ChatSchema>();

    const overflowRef = useRef<HTMLDivElement>(null);
    const updateScroll = () => {
        overflowRef.current?.scrollTo(0, overflowRef.current.scrollHeight);
    };

    const [parentRef] = useAutoAnimate();

    const configuration = new Configuration({
        apiKey: api
    });

    const openAi = new OpenAIApi(configuration);

    const { mutateAsync, isLoading } = useMutation({
        mutationKey: 'query',
        mutationFn: async ({ prompt, sessionId }: { prompt: string; sessionId: string }) => {
            const VITE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
            const response = await axios.get(`${VITE_BACKEND_URL}/query`, {
                params: {
                    query: prompt,
                    tag: "test_frontend_user",
                    session_id: sessionId
                }
            });
            return response.data;
        }
    });

    const handleAsk = async ({ input: prompt }: ChatSchema) => {
        updateScroll();

        const sendRequest = async (selectedId: string, sessionId: string) => {
            setValue("input", "");

            addMessage(selectedId, {
                emitter: "user",
                message: prompt
            });

            try {
                const data = await mutateAsync({ prompt, sessionId: sessionId.session_id });

                const message = data?.generated_text || "No response message";

                addMessage(selectedId, {
                    emitter: "gpt",
                    message
                });

                if (selectedRole === "New chat" || selectedRole === undefined) {
                    editChat(selectedId, { role: prompt });
                }
            } catch (error: any) {
                const message = error?.response?.data?.detail || "Something went wrong!";
                addMessage(selectedId, {
                    emitter: "error",
                    message
                });
            }

            updateScroll();
        };

        if (selectedId && sessionId) {
            if (prompt && !isLoading) {
                await sendRequest(selectedId, sessionId);
            }
        } else {
            addChat(async (newId) => {
                const newSessionId = await createSession();
                await editChat(newId, { sessionId: newSessionId });
                await sendRequest(newId, newSessionId);
            });
        }
    };

    return (
        <Stack width="full" height="full">
            <Stack
                maxWidth="768px"
                width="full"
                marginX="auto"
                height="85%"
                overflow="auto"
                ref={overflowRef}
            >
                <Stack
                    spacing={2}
                    padding={2}
                    ref={parentRef}
                    height="full"
                >
                    {/* Loading Spinner when waiting for API response */}
                    {isLoading && (
                        <Stack
                            direction="row"
                            padding={4}
                            justifyContent="center"
                            alignItems="center"
                        >
                            <Spinner size="lg" color="blue.500" thickness="4px" />
                            <Text ml={3}>Thinking...</Text>
                        </Stack>
                    )}

                    {hasSelectedChat ? (
                        selectedChat.content.map(({ emitter, message }, key) => {
                            const getAvatar = () => {
                                switch (emitter) {
                                    case "gpt":
                                        return gptAvatar;
                                    case "error":
                                        return warning;
                                    default:
                                        return user;
                                }
                            };

                            const getMessage = () => {
                                if (message.slice(0, 2) === "\n\n") {
                                    return message.slice(2, Infinity);
                                };

                                return message;
                            };

                            return (
                                <Stack
                                    key={key}
                                    direction="row"
                                    padding={4}
                                    rounded={8}
                                    backgroundColor={
                                        emitter === 'gpt' ? "blackAlpha.200" : "transparent"
                                    }
                                    spacing={4}
                                >
                                    <Avatar
                                        name={emitter}
                                        src={getAvatar()}
                                    />
                                    <Text
                                        whiteSpace="pre-wrap"
                                        marginTop=".75em !important"
                                        overflow="hidden"
                                    >
                                        <ReactMarkdown>
                                            {getMessage()}
                                        </ReactMarkdown>
                                    </Text>
                                </Stack>
                            );
                        })
                    ) : (
                        <Instructions
                            onClick={(text) => setValue('input', text)}
                        />
                    )}
                </Stack>
            </Stack>

            <Stack
                height="20%"
                padding={4}
                backgroundColor="blackAlpha.400"
                justifyContent="center"
                alignItems="center"
                overflow="hidden"
            >
                <Stack maxWidth="768px">
                    {/* Input Group with aligned Send and Upload buttons */}
                    <InputGroup>
                        <ChakraInput
                            autoFocus
                            variant="filled"
                            pr="6.5rem"
                            {...register("input")}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    handleAsk({ input: e.currentTarget.value });
                                }
                            }}
                        />
                        <InputRightElement width="6.5rem" display="flex" justifyContent="space-between" pr={2}>
                            <IconButton
                                aria-label="upload_button"
                                icon={<FiUpload />}
                                size="sm"
                                variant="ghost"
                                onClick={onOpen}
                            />
                            <IconButton
                                aria-label="send_button"
                                icon={!isLoading ? <FiSend /> : <Spinner size="sm" />}
                                size="sm"
                                variant="ghost"
                                onClick={handleSubmit(handleAsk)}
                            />
                        </InputRightElement>
                    </InputGroup>

                    <Text textAlign="center" fontSize="sm" opacity={.5}>
                        Free Research Preview. Our goal is to make AI systems more natural and safe to interact with. Your feedback will help us improve.
                    </Text>

                    <UploadDocsModal
                        isOpen={isOpen}
                        onClose={onClose}
                        sessionId={sessionId}
                        onUploadComplete={() => {
                            onClose();
                        }}
                    />
                </Stack>
            </Stack>
        </Stack>
    );
};
