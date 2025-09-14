"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Icon from "@/components/ui/icon";
import * as icons from "lucide-react";
import { useEffect, useState } from "react";

interface HowItWorksProps {
  icon: string;
  title: string;
  description: string;
}

const howItWorksList: HowItWorksProps[] = [
  {
    icon: "Paperclip",
    title: "Upload any document",
    description:
        "PDF, Word, Excel, PowerPoint, or plain text",
  },
  {
    icon: "MessageCircle",
    title: "Ask anything",
    description:
        "Type your question in natural language",
  },
  {
    icon: "Text",
    title: "Get precise answers",
    description:
        "AI extracts exactly what you need in seconds",
  },
  {
    icon: "Pin",
    title: "Save Chats",
    description:
        "Your chats will be saved as history, You can always look back.",
  },
];

export const HowItWorksSection = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(entry.target);
          }
        },
        { threshold: 0.1 }
    );

    const section = document.getElementById('benefits');
    if (section) observer.observe(section);

    return () => {
      if (section) observer.unobserve(section);
    };
  }, []);

  return (
      <section
          id="howItWorks"
          className="container py-24 sm:py-8 px-6 lg:px-24 px-6 w-full mx-auto"
      >
        <div className="grid lg:grid-cols-2 place-items-center lg:gap-24">
          <div className={`transform transition-all duration-300`}>
            <h2 className="text-lg text-primary mb-2 font-mono uppercase text-sm tracking-wider">AI</h2>

            <h2 className="text-3xl md:text-4xl font-semibold mb-4">
              How Reg-Guru Works
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Reg-Guru uses AI to study your documents and answer your questions
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-4 w-full">
            {howItWorksList.map(({ icon, title, description }, index) => (
                <Card
                    key={title}
                    className={`
                bg-[#fefefe] dark:bg-[#171717] hover:bg-background 
                hover:shadow-lg hover:scale-105
                transition-all duration-300 group/number
                transform
              `}
                    style={{
                      transitionDelay: `${index * 150}ms`,
                    }}
                >
                  <CardHeader>
                    <div className="flex justify-between">
                      <div className="relative">
                        <Icon
                            name={icon as keyof typeof icons}
                            size={24}
                            color="#0D92F4"
                            className="mb-6 text-primary transition-all duration-300 group-hover/number:scale-110"
                        />
                      </div>
                      <span className="text-5xl text-blue-400/50 font-medium transition-all duration-300 group-hover/number:text-muted-foreground/30 group-hover/number:rotate-12">
                    0{index + 1}
                  </span>
                    </div>

                    <CardTitle className="font-mono uppercase">{title}</CardTitle>
                  </CardHeader>

                  <CardContent className="text-muted-foreground">
                    {description}
                  </CardContent>
                </Card>
            ))}
          </div>
        </div>
      </section>
  );
};