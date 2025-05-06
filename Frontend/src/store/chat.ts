import { create } from "zustand";
import { v4 } from 'uuid';
import store from "store2";
import axios from "axios";

// Your interface and types...
export interface UseChatProps {
    chat: Chat[],
    selectedChat: Chat | undefined,
    setChat: (payload: Chat) => void,
    addChat: (callback?: (id: string) => void) => void,
    editChat: (id: string, payload: Partial<Chat>) => void,
    addMessage: (id: string, action: ChatContent) => void,
    setSelectedChat: (payload: { id: string }) => void,
    removeChat: (pyload: { id: string }) => void,
    clearAll: () => void,
};

type Chat = {
    id: string,
    role: string,
    sessionId?: string,
    content: ChatContent[]
};

type ChatContent = {
    emitter: ChatContentEmmiter,
    message: string
};

type ChatContentEmmiter = "gpt" | "user" | "error";

// Get saved chats from session
const savedChats = JSON.parse(store.session("@chat"));
const getSafeSavedChats = () => {
    if (Array.isArray(savedChats) && savedChats.length > 0) {
        return savedChats;
    };
    return undefined;
};

// Save chats to session
const saveChatsToSession = (chats: Chat[]) => {
    store.session("@chat", JSON.stringify(chats));
};

const initialChatState: Chat[] = getSafeSavedChats() || [
    // Sample initial chats...
];

export const useChat = create<UseChatProps>((set, get) => ({
    chat: initialChatState,
    selectedChat: initialChatState[0],

    setChat: async (payload) => set(({ chat }) => {
        const updatedChat = [...chat, payload];
        saveChatsToSession(updatedChat);
        return { chat: updatedChat };
    }),

    addChat: async (callback) => {
        const hasNewChat = get().chat.find(({ content }) => content.length === 0);

        if (!hasNewChat) {
            const id = v4();
            try {
                // Use environment variable for the API base URL
                const VITE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
                console.log("VITE_BACKEND_URL", VITE_BACKEND_URL);
                const res = await axios.get(`${VITE_BACKEND_URL}/createSession`);
                const sessionId = res.data; // Get sessionId from the API response

                get().setChat({
                    role: "New chat",
                    id: id,
                    sessionId: sessionId, // Save sessionId here
                    content: []
                });

                get().setSelectedChat({ id });
                if (callback) callback(id);
            } catch (error) {
                console.error("Failed to create session:", error);
                // Handle error appropriately (e.g., show a message to the user)
            }
        } else {
            const { id } = hasNewChat;
            get().setSelectedChat({ id });
            if (callback) callback(id);
        };
    },

    // Other methods remain the same...
    editChat: async (id, payload) => set(({ chat }) => {
        const selectedChat = chat.findIndex((query) => query.id === id);
        if (selectedChat > -1) {
            chat[selectedChat] = { ...chat[selectedChat], ...payload };
            return { chat, selectedChat: chat[selectedChat] };
        };
        return {};
    }),

    addMessage: async (id, action) => set(({ chat }) => {
        const selectedChat = chat.findIndex((query) => query.id === id);
        if (selectedChat > -1) {
            const props = chat[selectedChat];
            chat[selectedChat] = { ...props, content: [...props.content, action] };
            saveChatsToSession(chat);
            return { chat, selectedChat: chat[selectedChat] };
        }
        return {};
    }),

    setSelectedChat: async (payload) => set(({ chat }) => {
        const selectedChat = chat.find(({ id }) => id === payload.id);
        return { selectedChat };
    }),

    removeChat: async (payload) => set(({ chat }) => {
        const newChat = chat.filter(({ id }) => id !== payload.id);
        saveChatsToSession(newChat);
        return { chat: newChat };
    }),

    clearAll: async () => {
        store.session("@chat", null);
        set({ chat: [], selectedChat: undefined });
    },
}));
