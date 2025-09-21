"use client";
import {AlignLeft, ChevronsDown, Github, Menu, Send} from "lucide-react";
import React from "react";
import {
    Sheet,
    SheetContent,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "../ui/sheet";
import { Separator } from "../ui/separator";
import {
    NavigationMenu,
    NavigationMenuContent,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    NavigationMenuTrigger,
} from "../ui/navigation-menu";
import { Button } from "../ui/button";
import Link from "next/link";
import Image from "next/image";
import { ToggleTheme } from "./toogle-theme";
import { motion, AnimatePresence } from "framer-motion";

interface RouteProps {
    href: string;
    label: string;
}

interface FeatureProps {
    title: string;
    description: string;
}

const routeList: RouteProps[] = [
    {
        href: "/#features",
        label: "Features",
    },
    {
        href: "/contact",
        label: "Contact",
    },
    {
        href: "/feedback",
        label: "Feedback",
    },
    {
        href: "/#howItWorks",
        label: "How it works",
    },
];

const featureList: FeatureProps[] = [
    {
        title: "Showcase Your Value ",
        description: "Highlight how your product solves user problems.",
    },
    {
        title: "Build Trust",
        description:
            "Leverages social proof elements to establish trust and credibility.",
    },
    {
        title: "Capture Leads",
        description:
            "Make your lead capture form visually appealing and strategically.",
    },
];

export const Navbar = () => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [scrolled, setScrolled] = React.useState(false);

    // Handle scroll effect
    React.useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };

        window.addEventListener("scroll", handleScroll);
        return () => {
            window.removeEventListener("scroll", handleScroll);
        };
    }, []);

    // Animation variants for mobile menu items
    const containerVariants = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.3,
            }
        }
    };

    const itemVariants = {
        hidden: { x: -20, opacity: 0 },
        show: { x: 0, opacity: 1 }
    };

    return (
        <header className={`shadow-inner w-full md:w-[70%] lg:w-[100%] lg:max-w-screen-xl mx-auto z-40 flex justify-between items-center p-2 transition-all duration-300 ${
            scrolled ? "bg-transparent" : "bg-transparent"
        } py-6`}>
            <Link href="/" className="font-bold text-lg flex items-center">
                <Image
                    src={"/logo.png"}
                    className="w-10 mr-4 h-auto transition-transform duration-300 hover:scale-110"
                    width={400}
                    height={400}
                    alt="logo"
                />
                <span className="transition-colors font-bold font-mono uppercase duration-300 hover:text-primary">reg-guru</span>
            </Link>
            {/* <!-- Mobile --> */}
            <div className="flex items-center space-x-4 lg:hidden">
                <ToggleTheme/>
                <Sheet open={isOpen} onOpenChange={setIsOpen}>
                    <SheetTrigger asChild>
                        <motion.div
                            whileTap={{ scale: 0.9 }}
                        >
                            <Button
                                variant={"secondary"}
                                onClick={() => setIsOpen(!isOpen)}
                                className={"lg:hidden transition-all duration-300 hover:text-primary cursor-pointer w-10 h-10 rounded-full"}
                            >
                                <AlignLeft/>
                            </Button>
                        </motion.div>
                    </SheetTrigger>

                    <SheetContent
                        side="left"
                        className="flex flex-col justify-between rounded-tr-2xl rounded-br-2xl bg-card border-secondary transition delay-150 duration-300 ease-in-out"
                    >
                        <AnimatePresence>
                            {isOpen && (
                                <motion.div
                                    initial="hidden"
                                    animate="show"
                                    exit="hidden"
                                    variants={containerVariants}
                                    className="flex flex-col h-full justify-between"
                                >
                                    <div>
                                        <SheetHeader className="mb-4 ml-6">
                                            <SheetTitle className="flex items-center">
                                                <motion.div
                                                    initial={{ scale: 0.8, opacity: 0 }}
                                                    animate={{ scale: 1, opacity: 1 }}
                                                    transition={{ duration: 0.5 }}
                                                    className="flex items-center"
                                                >
                                                    <Link href="/" className="font-bold text-lg flex items-center">
                                                        <Image
                                                            src={"/logo.png"}
                                                            className="w-10 mr-2 h-auto rounded-full"
                                                            width={400}
                                                            height={400}
                                                            alt="logo"
                                                        />
                                                        <span className="ml-2">reg-guru</span>
                                                    </Link>
                                                </motion.div>
                                            </SheetTitle>
                                        </SheetHeader>

                                        <div className="flex flex-col ml-6 gap-2">
                                            {routeList.map(({ href, label }, index) => (
                                                <motion.div
                                                    key={href}
                                                    variants={itemVariants}
                                                    custom={index}
                                                    transition={{
                                                        duration: 0.4,
                                                        type: "spring",
                                                        stiffness: 100
                                                    }}
                                                >
                                                    <Button
                                                        onClick={() => setIsOpen(false)}
                                                        asChild
                                                        variant="ghost"
                                                        className="justify-start text-base transition-all duration-300 hover:pl-4 hover:text-primary"
                                                    >
                                                        <Link href={`${href}`}>{label}</Link>
                                                    </Button>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </div>

                                    <motion.div
                                        variants={itemVariants}
                                        transition={{ delay: 0.5, duration: 0.5 }}
                                    >
                                        <SheetFooter className="flex-col sm:flex-col justify-start items-start">
                                            <Separator className="mb-2" />
                                            <motion.div
                                                whileHover={{ scale: 1.05 }}
                                                transition={{ duration: 0.2 }}
                                            >
                                                <ToggleTheme />
                                            </motion.div>
                                        </SheetFooter>
                                    </motion.div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </SheetContent>
                </Sheet>
            </div>

            {/* <!-- Desktop --> */}
            <NavigationMenu className="hidden lg:block mx-auto">
                <NavigationMenuList>
                    <NavigationMenuItem className="flex space-x-8">
                        {routeList.map(({ href, label }) => (
                            <NavigationMenuLink key={href} asChild>
                                <Link
                                    href={href}
                                    className="text-base px-4 font-mono uppercase text-xs relative transition-all duration-300 hover:text-primary"
                                >
                                    <span className="relative group">
                                        {label}
                                    </span>
                                </Link>
                            </NavigationMenuLink>
                        ))}
                    </NavigationMenuItem>
                </NavigationMenuList>
            </NavigationMenu>

            <div className="hidden lg:flex space-x-4">
                <motion.div whileHover={{ scale: 1.1 }} transition={{ duration: 0.2 }}>
                    <ToggleTheme />
                </motion.div>
                <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} transition={{ duration: 0.2 }}>
                    <Button
                        asChild
                        size="sm"
                        variant="secondary"
                        aria-label="View on GitHub"
                        className="w-10 h-10 flex justify-center items-center rounded-full transition-colors duration-300 hover:bg-primary/10"
                    >
                        <Link
                            aria-label="View on GitHub"
                            href="https://github.com/nobruf/shadcn-landing-page.git"
                            target="_blank"
                        >
                            <Github className="size-4" />
                        </Link>
                    </Button>
                </motion.div>
            </div>
        </header>
    );
};