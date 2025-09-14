import React, {useEffect, useState} from 'react';
import {User} from 'lucide-react';
import Image from 'next/image';
import {Skeleton} from "@/components/ui/skeleton";


const AnimatedChatLoop = () => {
    const [conversationState, setConversationState] = useState('user-typing');
    const [userMessage, setUserMessage] = useState<string>('');
    const [botTyping, setBotTyping] = useState<boolean>(true);
    const [botResponse, setBotResponse] = useState<any[]>([]);

    const userText = "What is the inscription on the One Ring?";
    const botLines = [
        `It says: "One Ring to rule them all, One Ring to find them, One Ring to bring them all and in the darkness bind them.`,
    ];

    useEffect(() => {
        let timer :any;

        switch (conversationState) {
            case 'user-typing':
                if (userMessage.length < userText.length) {
                    timer = setTimeout(() => {
                        setUserMessage(userText.substring(0, userMessage.length + 1));
                    }, 70);
                } else {
                    timer = setTimeout(() => {
                        setConversationState('bot-typing');
                    }, 700);
                }
                break;

            case 'bot-typing':
                if (botTyping) {
                    timer = setTimeout(() => {
                        setBotTyping(false);
                        setBotResponse([]);
                        setConversationState('bot-responding');
                    }, 1000);
                }
                break;

            case 'bot-responding':
                if (botResponse.length < botLines.length) {
                    timer = setTimeout(() => {
                        setBotResponse([...botResponse, botLines[botResponse.length]]);
                    }, 500);
                } else {
                    timer = setTimeout(() => {
                        setConversationState('conversation-reset');
                    }, 3000);
                }
                break;

            case 'conversation-reset':
                timer = setTimeout(() => {
                    setUserMessage('');
                    setBotTyping(true);
                    setBotResponse([]);
                    setConversationState('user-typing');
                }, 1500);
                break;
        }

        return () => clearTimeout(timer);
    }, [conversationState, userMessage, botTyping, botResponse]);

    return (
        <div className="w-full h-90 md:h-56 max-w-2xl mx-auto bg-white dark:bg-[#171717] rounded-lg">
            <div className={`flex justify-end`}>
                <div className={`flex items-start gap-2 py-2 max-w-[90%] flex-row-reverse`}>
                    <div
                        className="flex-shrink-0 border bg-[#f1f1f1] dark:bg-[#121212] w-9 h-9 rounded-full flex items-center justify-center">
                        <User className="h-5 w-5"/>
                    </div>
                    <div className={`relative group mr-1`}>
                        <div className={`p-3 rounded-2xl text-right rounded-tr-none bg-[#f1f1f1] dark:bg-[#121212]`}>
                            <p>{userMessage || (conversationState === 'user-typing' ? '|' : '')}</p>
                            {userMessage.length === userText.length && (
                                <span
                                    className="text-xs opacity-70 block text-right mt-1 py-2 flex items-center justify-end">
                  The Fellowship of the Ring.pdf
                </span>
                            )}
                        </div>
                        <div className={"py-2"}></div>
                    </div>
                </div>
            </div>

            {(userMessage.length === userText.length || conversationState !== 'user-typing') && (
                <div className={`flex justify-start`}>
                    <div className={`flex items-start gap-2 max-w-[90%]`}>
                        <div className="flex-shrink-0">
                            <Image
                                src="/logo.png"
                                alt="Bot avatar"
                                width={36}
                                height={36}
                                className=""
                            />
                        </div>
                        <div className={`relative group mr-1`}>
                            <div
                                className={`px-3 rounded-2xl space-y-3 ${botTyping ? 'text-[#559BFE]' : 'text-gray-800 dark:text-gray-200'}`}>
                                {botTyping ? (
                                    <>
                                        <Skeleton className={"w-[170px] max-w-sm h-4"}/>
                                        <Skeleton className={"w-[140px] max-w-sm h-4"}/>
                                    </>
                                ) : (
                                    <div className=" space-y-2">
                                        {botResponse.map((line, index) => (
                                            <p key={index} className="animate-fadeUp transition-all duration-400">{line}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className={"py-2"}></div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnimatedChatLoop;