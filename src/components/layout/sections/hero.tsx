"use client";
import {Badge} from "@/components/ui/badge";
import {Button} from "@/components/ui/button";
import {ArrowRight} from "lucide-react";
import {useTheme} from "next-themes";
import Link from "next/link";
import React, {useEffect, useState} from "react";
import AnimatedChatLoop from "@/app/components/AnimatedChatLoop";

export const HeroSection = () => {
  const { theme } = useTheme();
  const [wavePosition, setWavePosition] = useState(0);

  // Animation for the waving effect
  useEffect(() => {
    const interval = setInterval(() => {
      setWavePosition((prev) => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);
  return (
      <section className="w-full mx-auto relative">
        {/*<div className="mb-8 max-w-sm w-full relative">*/}
        {/*  /!* Document icon *!/*/}
        {/*  <div className="absolute left-10 border shadow hover:rotate-10 transition-all duration-400 top-4 bg-white dark:bg-[#191919] p-3 rounded-lg hover:shadow-lg transform -rotate-6">*/}
        {/*    <FileText size={48} className="text-[#0D92F4]"/>*/}
        {/*  </div>*/}

        {/*  /!* Chatbot icon *!/*/}
        {/*  <div className="absolute right-10 top-0 hover:-rotate-10 transition-all duration-400 bg-white dark:bg-[#191919] p-3 rounded-lg shadow border hover:shadow-lg transform rotate-6">*/}
        {/*    <MessageCircleMore size={48} className="text-[#0D92F4]"/>*/}
        {/*    /!* Waving hand animation *!/*/}
        {/*    <div*/}
        {/*        className="absolute -right-4 -bottom-4  bg-yellow-300 h-8 w-8 rounded-full flex items-center justify-center shadow transform origin-bottom-right animate-pulse">*/}
        {/*      <span className="text-lg">👋</span>*/}
        {/*    </div>*/}
        {/*  </div>*/}
        {/*</div>*/}
          <div className="grid place-items-center px-2 lg:max-w-screen-xl gap-8 mx-auto py-12 md:py-20 w-full">
            <div className="text-center space-y-8">
              <Badge variant="outline" className="text-sm py-2 rounded-full">
            <span className="mr-2 text-primary">
              <Badge className={"rounded-full py-1"}>New</Badge>
            </span>
                <span className={"font-mono uppercase text-xs"}>Version 2.0.0 </span>
              </Badge>

              <div className="max-w-4xl w-full mx-auto text-center text-5xl md:text-7xl font-semibold">
                <h1 className={"tracking-tighter"}>
                  Transform how you interact with
                  <span className="text-transparent bg-gradient-to-r from-[#0D92F4] to-[#77CDFF] bg-clip-text">
                 {" "}documents
              </span>
                </h1>
              </div>

              <p className="max-w-screen-sm mx-auto text-xl text-muted-foreground">
                {`Upload any file and get instant, accurate answers without reading through endless pages.`}
              </p>

              <div className="space-y-4 md:space-y-0 md:space-x-4">
                <Button asChild className="w-5/6 md:w-1/4 font-bold font-mono uppercase text-xs py-6">
                  <Link
                      href="/chat"
                      target="_blank"
                      className={"flex items-center py-6"}
                  >
                    Ask me anything
                    <ArrowRight className="size-5 ml-2 group-hover/arrow:translate-x-1 transition-transform"/>
                  </Link>
                </Button>

                <Button
                    asChild
                    variant={"outline"}
                    className="w-5/6 md:w-1/4 font-bold font-mono uppercase text-xs py-6"
                >
                  <Link
                      href="https://github.com"
                      target="_blank"
                  >
                    Github Repository
                    <ArrowRight className="size-5 ml-1 group-hover/arrow:translate-x-1 transition-transform"/>
                  </Link>
                </Button>
              </div>
            </div>
            <div className="mt-12 mx-4 p-6 bg-white dark:bg-[#171717] rounded-lg border shadow max-w-4xl w-full">
              <div className="flex items-center mb-4">
                <div className="h-3 w-3 rounded-full bg-red-400 mr-2"></div>
                <div className="h-3 w-3 rounded-full bg-yellow-400 mr-2"></div>
                <div className="h-3 w-3 rounded-full bg-green-400"></div>
              </div>
              <AnimatedChatLoop/>
            </div>
          </div>
      </section>
  );
};
