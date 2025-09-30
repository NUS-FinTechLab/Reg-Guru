import React, { useEffect, useState } from 'react';
import { User } from 'lucide-react';
import Image from 'next/image';
import { Skeleton } from "@/components/ui/skeleton";
import SourceLinks from "@/components/ui/source-links";
import { Source } from "@/utils/api/types";


const AnimatedChatLoop = () => {
    const [conversationState, setConversationState] = useState('user-typing');
    const [userMessage, setUserMessage] = useState<string>('');
    const [botTyping, setBotTyping] = useState<boolean>(true);
    const [botResponse, setBotResponse] = useState<string[]>([]);

    const userText = "Under GDPR Article 6, do controllers need a lawful basis before they process personal data?";
    const botLines = [
        "Yes. Article 6 of the GDPR requires every controller to identify and record one of the six lawful bases before starting any processing of personal data.",
        "Without a valid lawful basis (consent, contract, legal obligation, vital interests, public task, or legitimate interests) the processing is non-compliant and exposes the controller to enforcement."
    ];
    const relatedSources: Source[] = [
        {
            title: "GDPR Article 6 - Lawfulness of Processing",
            link: "https://gdpr-info.eu/art-6-gdpr/"
        },
        {
            title: "EDPB Guidelines 05/2020 on Consent",
            link: "https://edpb.europa.eu/our-work-tools/documents/public-consultations/2020/guidelines-052020-consent-under-regulation_en"
        }
    ];

    useEffect(() => {
        let timer: any;

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
        <div className="w-full h-90 md:h-80 max-w-2xl mx-auto bg-white dark:bg-[#171717] rounded-lg">
            <div className={`flex justify-end mb-4`}>
                <div className={`flex items-start gap-2 py-2 max-w-[90%] flex-row-reverse`}>
                    <div
                        className="flex-shrink-0 border bg-[#f1f1f1] dark:bg-[#121212] w-9 h-9 rounded-full flex items-center justify-center">
                        <User className="h-5 w-5" />
                    </div>
                    <div className={`relative group mr-1`}>
                        <div className={`w-fit max-w-full md:max-w-[420px] inline-block p-3 rounded-2xl text-left rounded-tr-none bg-[#f1f1f1] dark:bg-[#121212]`}>
                            <p>{userMessage || (conversationState === 'user-typing' ? '|' : '')}</p>
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
                                        <Skeleton className={"w-[170px] max-w-sm h-4"} />
                                        <Skeleton className={"w-[140px] max-w-sm h-4"} />
                                    </>
                                ) : (
                                    <div className="space-y-2">
                                        {botResponse.map((line, index) => (
                                            <p key={index} className="animate-fadeUp transition-all duration-400">{line}</p>
                                        ))}
                                        {botResponse.length === botLines.length && (
                                            <SourceLinks sources={relatedSources} />
                                        )}
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
